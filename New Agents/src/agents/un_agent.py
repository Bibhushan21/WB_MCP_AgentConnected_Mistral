from typing import Dict, Any
import asyncio
from datetime import datetime
import aiohttp
from .base_agent import BaseAgent, SharedState
from ..schemas.data_schema import DataSet, DataPoint, Metadata, DataSource
import xml.etree.ElementTree as ET
import csv

class UNAgent(BaseAgent):
    def __init__(self):
        super().__init__("UN")
        self.base_url = "https://data.un.org/ws/rest/data"
        self.indicators_mapping = {
            "population": "SP_POP_TOTL",  # Total population
            "life_expectancy": "SP_DYN_LE00_IN",  # Life expectancy at birth
            "education_index": "EDU_IDX",  # Education index
            "gender_inequality": "GII",  # Gender Inequality Index
            "human_development": "HDI",  # Human Development Index
            "maternal_mortality": "SH_MMR",  # Maternal mortality ratio
            "child_mortality": "SH_DYN_MORT",  # Under-5 mortality rate
            "access_electricity": "EG_ELC_ACCS_ZS",  # Access to electricity
            "internet_users": "IT_NET_USER_ZS",  # Internet users
            "gdp growth": "NY_GDP_MKTP_KD_ZG_UN",  # Added GDP growth
            "gdp": "NY_GDP_MKTP_CD",  # GDP
        }

    def get_available_indicators(self) -> list[str]:
        """Return list of available indicators"""
        return sorted(self.indicators_mapping.keys())

    async def fetch_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch data from UN API
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")

        indicator = params.get("indicator", "").lower()
        country = params.get("country")
        start_year = str(params.get("start_year", "2000"))
        end_year = str(params.get("end_year", "2023"))

        if not indicator or not country:
            raise ValueError("Both indicator and country are required parameters")

        indicator_code = self.indicators_mapping.get(indicator)
        if not indicator_code:
            available = ", ".join(self.get_available_indicators())
            raise ValueError(f"Invalid indicator. Available indicators are: {available}")

        # UN specific endpoint construction
        dataset_indicator = "DF_UNData_WDI"  # Update this to the correct dataset indicator if needed
        query_key = f"A.{indicator_code}.{country}"
        url = f"{self.base_url}/{dataset_indicator}/{query_key}?startPeriod={start_year}&endPeriod={end_year}"

        print(f"UN API URL: {url}")

        async def _fetch():
            headers = {"Accept": "application/json"}
            async with self.session.get(url, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"UN API error: {error_text}")

                # Return the JSON content
                return await response.json()

        return await self.handle_retry(_fetch)

    async def transform_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform UN data from JSON into unified schema
        """
        try:
            # Extract data from JSON response
            data_set = raw_data.get("dataSets", [{}])[0]
            series = data_set.get("series", {})
            if not series:
                raise ValueError("No data found in UN response")

            transformed_data_points = []
            # Extract time periods from the structure
            structure = raw_data.get("structure", {})
            dimensions = structure.get("dimensions", {}).get("observation", [])
            time_periods = next((dim for dim in dimensions if dim.get("id") == "TIME_PERIOD"), {})
            time_values = time_periods.get("values", [])

            for serie_key, serie_data in series.items():
                observations = serie_data.get("observations", {})
                for time_idx, obs in observations.items():
                    if obs and obs[0] is not None:
                        year = int(time_values[int(time_idx)].get("id"))  # Map index to actual year
                        value = float(obs[0])
                        transformed_data_points.append(
                            DataPoint(
                                value=value,
                                year=year,
                                country_code=serie_key.split(":")[0],
                                country_name="",  # Country name not provided in this structure
                                additional_info={
                                    "indicator_id": serie_key.split(":")[1]
                                }
                            )
                        )

            # Determine the unit of the data based on the first data point
            if transformed_data_points:
                first_value = transformed_data_points[0].value
                unit = self.determine_unit(first_value)
                print(f"Determined unit for UN data: {unit}")  # Print the determined unit
                SharedState.set_un_unit(unit)  # Set the determined unit in SharedState
            else:
                unit = "unknown"

            # Sort data points by year
            transformed_data_points.sort(key=lambda x: x.year)

            dataset = DataSet(
                metadata=Metadata(
                    source=DataSource.UN,
                    indicator_code=serie_key.split(":")[1],
                    indicator_name="",  # Indicator name not provided in this structure
                    last_updated=datetime.now(),
                    frequency="yearly",  # Assuming yearly frequency
                    unit=unit  # Store the determined unit
                ),
                data=transformed_data_points
            )

            return dataset.dict()
        except Exception as e:
            self.logger.error(f"Error transforming UN data: {str(e)}")
            raise

    def _get_country_name(self, structure: Dict[str, Any], country_code: str) -> str:
        """Extract country name from UN structure"""
        try:
            dimensions = structure.get("dimensions", [])
            country_dim = next((dim for dim in dimensions if dim.get("id") == "REF_AREA"), {})
            country_values = country_dim.get("values", [])
            country = next((c for c in country_values if c.get("id") == country_code), {})
            return country.get("name", country_code)
        except Exception:
            return country_code

    def _get_indicator_name(self, structure: Dict[str, Any]) -> str:
        """Extract indicator name from UN structure"""
        try:
            dimensions = structure.get("dimensions", [])
            indicator_dim = next((dim for dim in dimensions if dim.get("id") == "SERIES"), {})
            return indicator_dim.get("name", "")
        except Exception:
            return ""

    def _get_unit(self, structure: Dict[str, Any]) -> str:
        """Extract unit from UN structure"""
        try:
            attributes = structure.get("attributes", [])
            unit_attr = next((attr for attr in attributes if attr.get("id") == "UNIT_MEASURE"), {})
            return unit_attr.get("name", "")
        except Exception:
            return ""

    def _get_frequency(self, structure: Dict[str, Any]) -> str:
        """Extract frequency from UN structure"""
        try:
            dimensions = structure.get("dimensions", [])
            freq_dim = next((dim for dim in dimensions if dim.get("id") == "FREQ"), {})
            return freq_dim.get("name", "yearly")
        except Exception:
            return "yearly" 