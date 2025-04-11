from typing import Dict, Any
import asyncio
from datetime import datetime
import aiohttp
from .base_agent import BaseAgent
from ..schemas.data_schema import DataSet, DataPoint, Metadata, DataSource

class IMFAgent(BaseAgent):
    def __init__(self):
        super().__init__("IMF")
        self.base_url = "http://dataservices.imf.org/REST/SDMX_JSON.svc"
        self.indicators_mapping = {
            "gdp": "NGDP_RPCH",  # Real GDP growth
            "gdp growth": "NGDP_RPCH",  # Added GDP growth
            "inflation": "PCPIPCH",  # Inflation rate
            "unemployment": "LUR",  # Unemployment rate
            "current_account": "BCA",  # Current account balance
            "government_debt": "GGXWDG_NGDP",  # Government debt to GDP
            "fiscal_balance": "GGXCNL_NGDP",  # Government fiscal balance
            "foreign_reserves": "NGDP_FX",  # Foreign exchange reserves
            "exports": "BX",  # Exports of goods and services
            "imports": "BM",  # Imports of goods and services
        }

    def get_available_indicators(self) -> list[str]:
        """Return list of available indicators"""
        return sorted(self.indicators_mapping.keys())

    async def fetch_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch data from IMF API
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

        # IMF specific endpoint construction
        years = ','.join(str(year) for year in range(int(start_year), int(end_year) + 1))
        url = f"https://www.imf.org/external/datamapper/api/v1/{indicator_code}/{country}?periods={years}"

        print(f"IMF API URL: {url}")

        self.logger.info(f"Fetching data from IMF API with URL: {url}")

        async def _fetch():
            async with self.session.get(url) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"IMF API error: {error_text}")
                return await response.json()

        return await self.handle_retry(_fetch)

    async def transform_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform IMF data into unified schema
        """
        try:
            # Extract data series from IMF response
            values = raw_data.get("values", {})
            if not values:
                raise ValueError("No data found in IMF response")

            transformed_data_points = []
            for indicator_code, countries in values.items():
                for country_code, data in countries.items():
                    for year, value in data.items():
                        transformed_data_points.append(
                            DataPoint(
                                value=float(value),
                                year=int(year),
                                country_code=country_code,
                                country_name="",  # Country name not provided in this structure
                                additional_info={
                                    "indicator_id": indicator_code
                                }
                            )
                        )

            # Sort data points by year
            transformed_data_points.sort(key=lambda x: x.year)

            dataset = DataSet(
                metadata=Metadata(
                    source=DataSource.IMF,
                    indicator_code=indicator_code,
                    indicator_name="",  # Indicator name not provided in this structure
                    last_updated=datetime.now(),
                    frequency="yearly",  # Assuming yearly frequency
                    unit=""
                ),
                data=transformed_data_points
            )

            return dataset.dict()
        except Exception as e:
            self.logger.error(f"Error transforming IMF data: {str(e)}")
            raise 