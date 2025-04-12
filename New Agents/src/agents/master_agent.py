import asyncio
from typing import Dict, Any, List, Type, Optional
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

from .base_agent import BaseAgent
from .world_bank_agent import WorldBankAgent
from .imf_agent import IMFAgent
from .oecd_agent import OECDAgent
from .un_agent import UNAgent
from ..schemas.data_schema import AggregatedDataResponse, DataSet, Metadata, DataSource
from ..utils.mistral_analyzer import MistralAnalyzer

load_dotenv()

class MasterAgent:
    def __init__(self):
        self.logger = logging.getLogger("MasterAgent")
        self.agents: Dict[str, Type[BaseAgent]] = {
            "world_bank": WorldBankAgent,
            "imf": IMFAgent,
            "oecd": OECDAgent,
            "un": UNAgent,
        }
        
        try:
            self.analyzer = MistralAnalyzer()
            self.logger.info("✅ Initialized MistralAnalyzer")
        except Exception as e:
            self.logger.error(f"⚠️ Failed to initialize MistralAnalyzer: {e}")
            self.analyzer = None

    async def _merge_datasets(self, datasets: List[DataSet]) -> DataSet:
        """
        Merge datasets from all sources into a single dataset.
        """
        merged_data_points = {}

        for dataset in datasets:
            for data_point in dataset.data:
                year = data_point.year
                if year not in merged_data_points:
                    merged_data_points[year] = data_point
                else:
                    # Merge data points by averaging values or choosing non-null values
                    existing_point = merged_data_points[year]
                    if data_point.value is not None:
                        if existing_point.value is None:
                            existing_point.value = data_point.value
                        else:
                            existing_point.value = (existing_point.value + data_point.value) / 2

        # Create a merged dataset
        merged_dataset = DataSet(
            metadata=Metadata(
                source=DataSource.WORLD_BANK,  # Use a generic source
                indicator_code="merged",
                indicator_name="Merged Data",
                last_updated=datetime.now(),
                frequency="yearly",
                unit=""
            ),
            data=list(merged_data_points.values())
        )

        return merged_dataset

    async def fetch_all_data(self, params: Dict[str, Any]) -> AggregatedDataResponse:
        """
        Fetch data from all available agents concurrently and merge the results.
        """
        tasks = []
        async with asyncio.TaskGroup() as group:
            for agent_name, agent_class in self.agents.items():
                tasks.append(
                    group.create_task(
                        self._fetch_from_agent(agent_class, params)
                    )
                )

        results = [task.result() for task in tasks if not task.cancelled()]

        # Print fetched data from each source
        print("\nFetched Data:")
        for result in results:
            if "error" not in result:
                dataset = DataSet(**result)
                print(f"\nSource: {dataset.metadata.source}")
                for point in dataset.data:
                    print(f"Year: {point.year}, Value: {point.value}")
            else:
                print(f"Error fetching data from {result['agent']}: {result['error']}")

        # Merge datasets
        merged_dataset = await self._merge_datasets([DataSet(**result) for result in results if "error" not in result])

        # Print merged data
        print("\nMerged Data:")
        for point in merged_dataset.data:
            print(f"Year: {point.year}, Value: {point.value}")

        # Analyze merged data
        analyses = {}
        if self.analyzer:
            try:
                analysis = await self.analyzer.analyze_data(
                    country=params.get("country", "Unknown"),
                    indicator=params.get("indicator", "Unknown"),
                    data=merged_dataset.dict()
                )
                analyses["merged"] = analysis
                # Print analysis
                print("\nAnalysis of Merged Data:")
                print(analysis)
            except Exception as e:
                self.logger.error(f"Error analyzing merged data: {str(e)}")
                analyses["error"] = f"Analysis failed: {str(e)}"
        else:
            analyses["error"] = "Analyzer not initialized."

        response = AggregatedDataResponse(
            query_params=params,
            timestamp=datetime.now(),
            datasets=[merged_dataset],
            status="completed" if not any("error" in result for result in results) else "partial_success",
            error_summary={result["agent"]: [result["error"]] for result in results if "error" in result},
            analyses=analyses
        )

        return response

    async def _fetch_from_agent(self, agent_class: Type[BaseAgent], params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch data from a single agent with error handling
        """
        try:
            async with agent_class() as agent:
                return await agent.get_data(params)
        except Exception as e:
            self.logger.error(f"Error fetching data from {agent_class.__name__}: {str(e)}")
            return {
                "error": str(e),
                "agent": agent_class.__name__
            }

    async def fetch_with_retry(self, params: Dict[str, Any], max_retries: int = 3) -> AggregatedDataResponse:
        """
        Fetch data with retry mechanism
        """
        last_error = None
        for attempt in range(max_retries):
            try:
                return await self.fetch_all_data(params)
            except Exception as e:
                last_error = e
                self.logger.warning(f"Attempt {attempt + 1} failed, retrying...")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        raise Exception(f"Failed after {max_retries} attempts. Last error: {str(last_error)}")

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """
        Validate input parameters
        """
        required_fields = ["indicator", "country"]
        return all(field in params for field in required_fields)

    def get_available_indicators(self) -> Dict[str, List[str]]:
        """
        Get available indicators from all agents
        """
        indicators = {}
        for agent_name, agent_class in self.agents.items():
            try:
                agent = agent_class()
                if hasattr(agent, "get_available_indicators"):
                    indicators[agent_name] = agent.get_available_indicators()
            except Exception as e:
                self.logger.error(f"Error getting indicators from {agent_name}: {str(e)}")
                indicators[agent_name] = []
        return indicators 