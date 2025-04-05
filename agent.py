import asyncio
import json
import aiohttp
import re
from typing import Optional, Dict, Any, Tuple

class MCPClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.tools = {}
        self.session = None
        self.indicators = {
            "gdp": "gdp",
            "gdp per capita": "gdp per capita",
            "literacy rate": "literacy rate",
            "population": "population",
            "life expectancy": "life expectancy",
            "inflation": "inflation",
            "unemployment rate": "unemployment rate"
        }
        # ISO 3166-1 alpha-3 country codes mapping
        self.country_codes = {
            "afghanistan": "AFG", "albania": "ALB", "algeria": "DZA", "andorra": "AND",
            "angola": "AGO", "argentina": "ARG", "armenia": "ARM", "australia": "AUS",
            "austria": "AUT", "azerbaijan": "AZE", "bahamas": "BHS", "bahrain": "BHR",
            "bangladesh": "BGD", "barbados": "BRB", "belarus": "BLR", "belgium": "BEL",
            "belize": "BLZ", "benin": "BEN", "bhutan": "BTN", "bolivia": "BOL",
            "bosnia": "BIH", "botswana": "BWA", "brazil": "BRA", "brunei": "BRN",
            "bulgaria": "BGR", "burkina faso": "BFA", "burundi": "BDI", "cambodia": "KHM",
            "cameroon": "CMR", "canada": "CAN", "chad": "TCD", "chile": "CHL",
            "china": "CHN", "colombia": "COL", "congo": "COG", "costa rica": "CRI",
            "croatia": "HRV", "cuba": "CUB", "cyprus": "CYP", "czech republic": "CZE",
            "denmark": "DNK", "djibouti": "DJI", "dominica": "DMA", "dr congo": "COD",
            "ecuador": "ECU", "egypt": "EGY", "el salvador": "SLV", "estonia": "EST",
            "ethiopia": "ETH", "fiji": "FJI", "finland": "FIN", "france": "FRA",
            "gabon": "GAB", "gambia": "GMB", "georgia": "GEO", "germany": "DEU",
            "ghana": "GHA", "greece": "GRC", "guatemala": "GTM", "guinea": "GIN",
            "guyana": "GUY", "haiti": "HTI", "honduras": "HND", "hungary": "HUN",
            "iceland": "ISL", "india": "IND", "indonesia": "IDN", "iran": "IRN",
            "iraq": "IRQ", "ireland": "IRL", "israel": "ISR", "italy": "ITA",
            "jamaica": "JAM", "japan": "JPN", "jordan": "JOR", "kazakhstan": "KAZ",
            "kenya": "KEN", "kuwait": "KWT", "kyrgyzstan": "KGZ", "laos": "LAO",
            "latvia": "LVA", "lebanon": "LBN", "lesotho": "LSO", "liberia": "LBR",
            "libya": "LBY", "liechtenstein": "LIE", "lithuania": "LTU", "luxembourg": "LUX",
            "madagascar": "MDG", "malawi": "MWI", "malaysia": "MYS", "maldives": "MDV",
            "mali": "MLI", "malta": "MLT", "mauritania": "MRT", "mauritius": "MUS",
            "mexico": "MEX", "moldova": "MDA", "monaco": "MCO", "mongolia": "MNG",
            "montenegro": "MNE", "morocco": "MAR", "mozambique": "MOZ", "myanmar": "MMR",
            "namibia": "NAM", "nepal": "NPL", "netherlands": "NLD", "new zealand": "NZL",
            "nicaragua": "NIC", "niger": "NER", "nigeria": "NGA", "north korea": "PRK",
            "norway": "NOR", "oman": "OMN", "pakistan": "PAK", "panama": "PAN",
            "papua new guinea": "PNG", "paraguay": "PRY", "peru": "PER", "philippines": "PHL",
            "poland": "POL", "portugal": "PRT", "qatar": "QAT", "romania": "ROU",
            "russia": "RUS", "rwanda": "RWA", "saudi arabia": "SAU", "senegal": "SEN",
            "serbia": "SRB", "sierra leone": "SLE", "singapore": "SGP", "slovakia": "SVK",
            "slovenia": "SVN", "somalia": "SOM", "south africa": "ZAF", "south korea": "KOR",
            "spain": "ESP", "sri lanka": "LKA", "sudan": "SDN", "sweden": "SWE",
            "switzerland": "CHE", "syria": "SYR", "taiwan": "TWN", "tajikistan": "TJK",
            "tanzania": "TZA", "thailand": "THA", "togo": "TGO", "tunisia": "TUN",
            "turkey": "TUR", "turkmenistan": "TKM", "uganda": "UGA", "ukraine": "UKR",
            "united arab emirates": "ARE", "united kingdom": "GBR", "united states": "USA",
            "usa": "USA", "us": "USA", "uruguay": "URY", "uzbekistan": "UZB",
            "venezuela": "VEN", "vietnam": "VNM", "yemen": "YEM", "zambia": "ZMB",
            "zimbabwe": "ZWE"
        }

    async def connect(self):
        """Connect to the MCP server and start listening for messages"""
        self.session = aiohttp.ClientSession()
        try:
            async with self.session.get(f"{self.base_url}/mcp/sse") as response:
                if response.status != 200:
                    raise RuntimeError(f"Failed to connect to MCP server: {response.status}")
                
                print("Connected to MCP server, waiting for tools...")
                async for event in response.content:
                    try:
                        event_data = event.decode('utf-8').strip()
                        if event_data.startswith('data:'):
                            data = json.loads(event_data[5:].strip())
                            if isinstance(data, dict) and data.get('type') == 'ready':
                                self.tools = data.get('tools', {})
                                print("Ready to process your queries!")
                                break
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        print(f"Error processing event: {e}")
                        continue
        except Exception as e:
            print(f"Connection error: {e}")
            if self.session:
                await self.session.close()
                self.session = None
            raise

    async def invoke_tool(self, tool_name: str, **params) -> Any:
        """Invoke an MCP tool"""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")

        try:
            async with self.session.post(
                f"{self.base_url}/mcp/invoke/{tool_name}",
                json=params
            ) as response:
                if response.status == 404:
                    raise ValueError(f"Tool {tool_name} not found")
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Error invoking tool: {error_text}")
                
                result = await response.json()
                return result.get('result')
        except Exception as e:
            print(f"Error invoking tool {tool_name}: {e}")
            raise

    async def close(self):
        """Close the client connection"""
        if self.session:
            await self.session.close()
            self.session = None

    def parse_query(self, query: str) -> Tuple[str, str, int, int]:
        """Parse natural language query into components"""
        # Convert query to lowercase for easier matching
        query = query.lower()
        
        # Find the indicator (GDP, inflation, etc.)
        indicator = None
        for ind in self.indicators:
            if ind in query:
                indicator = self.indicators[ind]
                break
        
        if not indicator:
            raise ValueError("Could not identify the indicator (GDP, inflation, etc.) in your query")

        # Find country name and convert to ISO code
        country_match = re.search(r'(?:of|for)\s+([a-zA-Z\s]+?)(?=\s+from|\s*$)', query)
        if not country_match:
            raise ValueError("Could not identify the country name in your query")
        
        country_name = country_match.group(1).strip().lower()
        country_code = self.country_codes.get(country_name)
        if not country_code:
            raise ValueError(f"Could not find ISO code for country: {country_name}")

        # Find years - looking for full 4-digit years
        year_pattern = re.compile(r'(?:19|20)\d{2}')  # Match years from 1900-2099
        years = year_pattern.findall(query)
        
        if len(years) >= 2:
            start_year = int(years[0])
            end_year = int(years[1])
        elif len(years) == 1:
            # If only one year is found, use it as start year and current year as end
            start_year = int(years[0])
            end_year = 2025
        else:
            # If no years found, default to last 5 years
            end_year = 2025
            start_year = 2020

        # Validate years
        if not (1900 <= start_year <= 2025 and 1900 <= end_year <= 2025):
            raise ValueError("Years must be between 1900 and 2025")
        if start_year > end_year:
            start_year, end_year = end_year, start_year  # Swap if in wrong order

        return indicator, country_code, start_year, end_year

async def main():
    """Interactive MCP client"""
    client = MCPClient()
    try:
        await client.connect()
        
        while True:
            print("\nEnter your query (or 'quit' to exit)")
            print("Example: 'Give me GDP per capita of Nepal from 2000 to 2023'")
            query = input("> ")
            
            if query.lower() in ['quit', 'exit', 'q']:
                break

            try:
                indicator, country_code, start_year, end_year = client.parse_query(query)
                print(f"\nFetching {indicator} data for {country_code} from {start_year} to {end_year}...")
                
                result = await client.invoke_tool(
                    "get_data",
                    country_code=country_code,
                    query=indicator,
                    start_year=start_year,
                    end_year=end_year
                )
                print("\nResults:")
                print(result)
                
            except ValueError as e:
                print(f"\nError understanding query: {e}")
                print("Please try again with a different wording.")
            except Exception as e:
                print(f"\nError: {e}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())