import asyncio
import os
import re
from dotenv import load_dotenv
from mistralai.client import MistralClient
from agent import MCPClient
from world_bank_data import get_data, INDICATOR_MAPPING

load_dotenv()

class MistralAnalyzer:
    def __init__(self, mcp_instance=None):
        # Initialize MistralAI client
        mistral_api_key = os.getenv("MISTRAL_API_KEY")
        if not mistral_api_key:
            raise ValueError("MISTRAL_API_KEY environment variable is required")
        
        self.mistral_client = MistralClient(api_key=mistral_api_key)
        self.mcp_client = mcp_instance if mcp_instance else MCPClient()
        
        # Use the imported INDICATOR_MAPPING
        self.indicators = INDICATOR_MAPPING
        
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

    def parse_query(self, query: str) -> tuple[str, str, int, int]:
        """Parse natural language query into components"""
        # Convert query to lowercase for easier matching
        query = query.lower()
        
        # Find the indicator (GDP, inflation, etc.)
        indicator = None
        indicator_key = None
        for ind in self.indicators:
            if ind in query:
                indicator_key = ind
                indicator = ind  # We keep the user-friendly name for the query
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

    async def connect(self, max_retries=5, retry_delay=2):
        """Connect to the MCP server with retries"""
        if not hasattr(self.mcp_client, 'connect'):
            # If we're using an existing MCP instance, no need to connect
            print("✅ Using existing MCP connection")
            return
            
        for attempt in range(max_retries):
            try:
                await self.mcp_client.connect()
                print(f"✅ Connected to MCP server on attempt {attempt + 1}")
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⚠️ Connection attempt {attempt + 1} failed: {e}")
                    print(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                else:
                    raise Exception(f"Failed to connect after {max_retries} attempts: {e}")

    async def close(self):
        """Close all connections"""
        if self.mcp_client and hasattr(self.mcp_client, 'close'):
            await self.mcp_client.close()

    def _create_analysis_prompt(self, country: str, indicator: str, data: str) -> str:
        """Create a prompt for MistralAI to analyze the data"""
        return f"""You are a helpful economic analyst. Analyze the following {indicator} data for {country} and provide:
1. A clear summary of the trends
2. Key observations and insights
3. Potential factors influencing the changes
4. Comparison with global averages if relevant

Here's the data:
{data}

Please provide a well-structured, detailed analysis that would be helpful for understanding the economic situation of {country} based on this {indicator} data."""

    async def analyze_data(self, query: str) -> str:
        """
        Fetch data using MCP client and analyze it using MistralAI
        
        Args:
            query: Natural language query (e.g., "Give me GDP per capita of India from 2000 to 2025")
            
        Returns:
            str: Detailed analysis of the data
        """
        try:
            # Parse the query using our parse_query method
            indicator, country_code, start_year, end_year = self.parse_query(query)
            
            # Fetch data using get_data function
            data = await get_data(
                country_code=country_code,
                query=indicator,
                start_year=start_year,
                end_year=end_year
            )
            
            if isinstance(data, str) and "error" in data.lower():
                return f"Error fetching data: {data}"
            
            # Create analysis prompt
            prompt = self._create_analysis_prompt(country_code, indicator, data)
            
            try:
                # Get analysis from MistralAI using create method
                response = self.mistral_client.chat(
                    model="mistral-medium",  # Changed from mistral-large to mistral-medium
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert economic analyst specializing in analyzing World Bank data and providing insightful economic analysis."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                
                if response and hasattr(response, 'choices') and response.choices:
                    return response.choices[0].message.content
                else:
                    return "Error: No response from MistralAI"
                    
            except Exception as e:
                print(f"MistralAI Error: {str(e)}")
                # Try again with simpler prompt if the first attempt fails
                response = self.mistral_client.chat(
                    model="mistral-medium",  # Fallback to medium model
                    messages=[
                        {
                            "role": "user",
                            "content": f"Analyze this economic data: {data}"
                        }
                    ]
                )
                return response.choices[0].message.content
            
        except Exception as e:
            error_msg = str(e)
            print(f"Analysis Error: {error_msg}")
            if "API key" in error_msg.lower():
                return "Error: Invalid or missing MistralAI API key. Please check your .env file."
            return f"Error during analysis: {error_msg}"

async def main():
    """Interactive client combining World Bank data and MistralAI analysis"""
    analyzer = MistralAnalyzer()
    
    try:
        await analyzer.connect()
        
        while True:
            print("\nEnter your query (or 'quit' to exit)")
            print("Example: 'Give me GDP per capita of India from 2000 to 2025'")
            query = input("> ")
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            print("\nFetching and analyzing data...")
            analysis = await analyzer.analyze_data(query)
            print("\nAnalysis:")
            print(analysis)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await analyzer.close()

if __name__ == "__main__":
    asyncio.run(main()) 