<<<<<<< HEAD
# World Bank Data Analysis with MCP and MistralAI

This project combines World Bank data retrieval with AI-powered analysis using MistralAI. It consists of two main components:
1. An MCP (Machine Communication Protocol) server for World Bank data
2. A MistralAI-powered agent for detailed economic analysis

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root and add your MistralAI API key:
```
MISTRAL_API_KEY=your_api_key_here
```

4. Start the MCP server:
```bash
python main.py
```
The server will start on http://localhost:8000

5. In a separate terminal, start the MistralAI agent:
```bash
python mistral_agent.py
```

## Components

### 1. MCP Server (main.py)
Provides World Bank data through HTTP endpoints and Server-Sent Events (SSE).

### 2. MistralAI Agent (mistral_agent.py)
An interactive client that:
- Accepts natural language queries about economic data
- Fetches relevant World Bank data through the MCP server
- Uses MistralAI to provide detailed analysis of the data

## Using the System

1. Make sure both the MCP server (main.py) and MistralAI agent (mistral_agent.py) are running
2. In the MistralAI agent terminal, enter queries like:
   - "Give me GDP per capita of India from 2000 to 2025"
   - "Show me the population of China from 2010 to 2020"
   - "What is the inflation rate of Brazil from 2015 to 2023"
3. The agent will fetch the data and provide AI-powered analysis including:
   - Trend summaries
   - Key observations and insights
   - Potential factors influencing changes
   - Global comparisons when relevant

## Available Indicators

- GDP: "gdp"
- GDP per capita: "gdp per capita"
- Literacy rate: "literacy rate"
- Population: "population"
- Life expectancy: "life expectancy"
- Inflation: "inflation"
- Unemployment rate: "unemployment rate"

## API Documentation

When the MCP server is running, API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Example Endpoints

### MCP Server Endpoints:
```
http://localhost:8000/docs
http://localhost:8000/mcp/sse
http://localhost:8000/mcp/invoke/get_data
```


### Direct Data Query Example:
```
http://localhost:8000/get_data?country_code=DEU&query=inflation&start_year=1990&end_year=2023
```

## Architecture

The system works in three steps:
1. User inputs a query to the MistralAI agent
2. Agent parses the query and fetches data from the MCP server
3. Data is sent to MistralAI for comprehensive economic analysis

## Error Handling

The system includes robust error handling for:
- Invalid country codes
- Unsupported indicators
- Missing or invalid date ranges
- API connection issues
- Data availability gaps

## Requirements

- Python 3.7+
- FastAPI
- MistralAI API key
- Required Python packages (see requirements.txt)


API documentation is available at http://localhost:8000/docs when the server is running. 

http://localhost:8000/docs
http://localhost:8000/mcp/sse
http://localhost:8000/get_data?country_code=DEU&query=inflation&start_year=1990&end_year=2023
=======
"# WB_MCP_AgentConnected_Mistral" 
>>>>>>> 3c7abefc3d84acadbc2866ccd9c20f4966a2713a
