import httpx
from wb_indicators import INDICATOR_MAPPING, get_indicator_info

# World Bank API URL
WORLD_BANK_API_URL = "https://api.worldbank.org/v2/country/{}/indicator/{}?date={}:{}&format=json"

async def get_data(country_code: str, query: str, start_year: int = 2000, end_year: int = 2025):
    """
    Fetch data from World Bank API
    
    Args:
        country_code (str): ISO 3166-1 alpha-3 country code
        query (str): Type of data to fetch (e.g., "gdp", "population")
        start_year (int): Start year for data range
        end_year (int): End year for data range
        
    Returns:
        str: Formatted data output
    """
    indicator = INDICATOR_MAPPING.get(query.lower())
    if not indicator:
        available_indicators = ", ".join(sorted(INDICATOR_MAPPING.keys()))
        return f"Invalid query. Available indicators are: {available_indicators}"
    
    # Get indicator metadata
    indicator_info = get_indicator_info(query.lower())
    indicator_name = indicator_info["name"] if indicator_info else query.capitalize()
    
    url = WORLD_BANK_API_URL.format(country_code, indicator, start_year, end_year)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, list) and len(data) > 1 and isinstance(data[1], list):
                output = [f"{indicator_name} Data for {country_code} ({start_year}-{end_year}):\n"]
                if indicator_info:
                    output.append(f"Description: {indicator_info['description']}")
                    output.append(f"Source: {indicator_info['source']}\n")
                
                for entry in data[1]:
                    year = entry.get("date", "N/A")
                    value = entry.get("value", "No Data")
                    output.append(f"Year: {year}, {indicator_name}: {value}")
                return "\n".join(output)
            return "No data found for the given country and indicator."
            
        except httpx.TimeoutException:
            return "Timeout error while fetching data"
        except httpx.HTTPStatusError as e:
            return f"HTTP error {e.response.status_code} while fetching data"
        except Exception as e:
            return f"Error fetching data: {str(e)}" 