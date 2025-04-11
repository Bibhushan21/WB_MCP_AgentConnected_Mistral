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
from ..schemas.data_schema import AggregatedDataResponse, DataSet
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

    async def fetch_all_data(self, params: Dict[str, Any]) -> AggregatedDataResponse:
        """
        Fetch data from all available agents concurrently
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
        
        return await self._aggregate_results(params, results)

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

    async def _aggregate_results(self, query_params: Dict[str, Any], results: List[Dict[str, Any]]) -> AggregatedDataResponse:
        """
        Aggregate results from all agents and include analysis if available
        """
        datasets = []
        error_summary = {}
        analyses = {}

        # First, collect all successful datasets
        for result in results:
            if "error" in result:
                error_summary[result["agent"]] = [result["error"]]
                continue

            dataset = DataSet(**result)
            datasets.append(dataset)

        # Then, analyze all datasets together if we have data
        if datasets and self.analyzer:
            try:
                # Combine all datasets for a comprehensive analysis
                combined_data = {
                    "datasets": [d.dict() for d in datasets],
                    "sources": [d.metadata.source for d in datasets]
                }
                
                analysis = await self.analyzer.analyze_data(
                    country=query_params.get("country", "Unknown"),
                    indicator=query_params.get("indicator", "Unknown"),
                    data=combined_data
                )
                
                # Store the comprehensive analysis
                analyses["combined"] = analysis
                
                # Also analyze individual datasets if requested
                for dataset in datasets:
                    individual_analysis = await self.analyzer.analyze_data(
                        country=query_params.get("country", "Unknown"),
                        indicator=query_params.get("indicator", "Unknown"),
                        data=dataset.dict()
                    )
                    analyses[dataset.metadata.source] = individual_analysis
                    
            except Exception as e:
                self.logger.error(f"Error analyzing data: {str(e)}")
                analyses["error"] = f"Analysis failed: {str(e)}"

        response = AggregatedDataResponse(
            query_params=query_params,
            timestamp=datetime.now(),
            datasets=datasets,
            status="completed" if not error_summary else "partial_success",
            error_summary=error_summary if error_summary else None
        )
        
        # Add analyses to the response if available
        if analyses:
            response.analyses = analyses

        return response

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