"""
World Bank Indicators mapping and metadata.
This file contains a comprehensive list of commonly used World Bank indicators.
"""

# Main indicator mapping used by the application
INDICATOR_MAPPING = {
    # Economic indicators
    "gdp": "NY.GDP.MKTP.CD",  # GDP (current US$)
    "gdp per capita": "NY.GDP.PCAP.CD",  # GDP per capita (current US$)
    "gdp growth": "NY.GDP.MKTP.KD.ZG",  # GDP growth (annual %)
    "gni": "NY.GNP.MKTP.CD",  # GNI (current US$)
    "gni per capita": "NY.GNP.PCAP.CD",  # GNI per capita (current US$)
    
    # Population and Social indicators
    "population": "SP.POP.TOTL",  # Total population
    "population growth": "SP.POP.GROW",  # Population growth (annual %)
    "urban population": "SP.URB.TOTL",  # Urban population
    "rural population": "SP.RUR.TOTL",  # Rural population
    "life expectancy": "SP.DYN.LE00.IN",  # Life expectancy at birth (years)
    "mortality rate": "SP.DYN.IMRT.IN",  # Infant mortality rate
    "birth rate": "SP.DYN.CBRT.IN",  # Birth rate, crude (per 1,000 people)
    "death rate": "SP.DYN.CDRT.IN",  # Death rate, crude (per 1,000 people)
    
    # Education indicators
    "literacy rate": "SE.ADT.LITR.ZS",  # Literacy rate, adult total (%)
    "primary enrollment": "SE.PRM.ENRR",  # School enrollment, primary (% gross)
    "secondary enrollment": "SE.SEC.ENRR",  # School enrollment, secondary (% gross)
    "tertiary enrollment": "SE.TER.ENRR",  # School enrollment, tertiary (% gross)
    
    # Economic and Financial indicators
    "inflation": "FP.CPI.TOTL.ZG",  # Inflation, consumer prices (annual %)
    "unemployment rate": "SL.UEM.TOTL.ZS",  # Unemployment, total (% of labor force)
    "exports": "NE.EXP.GNFS.CD",  # Exports of goods and services (current US$)
    "imports": "NE.IMP.GNFS.CD",  # Imports of goods and services (current US$)
    "fdi": "BX.KLT.DINV.CD.WD",  # Foreign direct investment, net inflows (BoP, current US$)
    
    # Health indicators
    "health expenditure": "SH.XPD.CHEX.GD.ZS",  # Current health expenditure (% of GDP)
    "hospital beds": "SH.MED.BEDS.ZS",  # Hospital beds (per 1,000 people)
    "physicians": "SH.MED.PHYS.ZS",  # Physicians (per 1,000 people)
    "immunization": "SH.IMM.MEAS",  # Immunization, measles (% of children ages 12-23 months)
    
    # Environment and Infrastructure
    "co2 emissions": "EN.ATM.CO2E.PC",  # CO2 emissions (metric tons per capita)
    "forest area": "AG.LND.FRST.ZS",  # Forest area (% of land area)
    "renewable energy": "EG.FEC.RNEW.ZS",  # Renewable energy consumption (% of total final energy consumption)
    "internet users": "IT.NET.USER.ZS",  # Individuals using the Internet (% of population)
    "mobile subscriptions": "IT.CEL.SETS.P2",  # Mobile cellular subscriptions (per 100 people)
    
    # Trade and Business
    "trade balance": "NE.RSB.GNFS.CD",  # External balance on goods and services (current US$)
    "market capitalization": "CM.MKT.LCAP.GD.ZS",  # Market capitalization of listed domestic companies (% of GDP)
    "ease of business": "IC.BUS.EASE.XQ",  # Ease of doing business score
    
    # Poverty and Inequality
    "poverty ratio": "SI.POV.DDAY",  # Poverty headcount ratio at $1.90 a day (2011 PPP) (% of population)
    "gini index": "SI.POV.GINI",  # GINI index
    "income share": "SI.DST.10TH.10",  # Income share held by highest 10%
}

# Additional metadata about indicators
INDICATOR_METADATA = {
    "NY.GDP.MKTP.CD": {
        "name": "GDP (current US$)",
        "description": "GDP at purchaser's prices is the sum of gross value added by all resident producers in the economy plus any product taxes.",
        "source": "World Bank national accounts data, and OECD National Accounts data files.",
        "frequency": "Annual"
    },
    "SP.POP.TOTL": {
        "name": "Population, total",
        "description": "Total population is based on the de facto definition of population, which counts all residents regardless of legal status or citizenship.",
        "source": "United Nations Population Division.",
        "frequency": "Annual"
    },
    # Add more metadata as needed
}

def get_indicator_info(indicator_key: str) -> dict:
    """
    Get detailed information about a specific indicator.
    
    Args:
        indicator_key: The key from INDICATOR_MAPPING
        
    Returns:
        dict: Metadata about the indicator if available, or None if not found
    """
    if indicator_key not in INDICATOR_MAPPING:
        return None
    
    wb_code = INDICATOR_MAPPING[indicator_key]
    return INDICATOR_METADATA.get(wb_code, {
        "name": indicator_key.title(),
        "description": "No detailed description available",
        "source": "World Bank",
        "frequency": "Annual"
    }) 