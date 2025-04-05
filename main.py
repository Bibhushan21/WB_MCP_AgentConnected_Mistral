from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
import json
import asyncio
import os
from dotenv import load_dotenv
from fastmcp import FastMCP
from mistral_agent import MistralAnalyzer
from world_bank_data import get_data, INDICATOR_MAPPING

load_dotenv()

# Initialize MCP first
mcp = FastMCP("world_bank_data")

# Initialize MistralAnalyzer with MCP instance
analyzer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global analyzer
    try:
        # Initialize MistralAnalyzer
        analyzer = MistralAnalyzer(mcp)
        # Start the server first
        await asyncio.sleep(2)  # Give the server more time to start
        await analyzer.connect()
        print("✅ Connected to MCP server and MistralAI")
    except Exception as e:
        print(f"⚠️ Error during startup: {e}")
        raise e
        
    yield
    
    # Shutdown
    try:
        if analyzer:
            await analyzer.close()
            print("✅ Closed all connections")
    except Exception as e:
        print(f"⚠️ Error during shutdown: {e}")

app = FastAPI(title="World Bank Data MCP", lifespan=lifespan)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model for analysis
class AnalysisRequest(BaseModel):
    query: str

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/analyze")
async def analyze_data(request: AnalysisRequest):
    if not analyzer:
        raise HTTPException(status_code=503, detail="Service is initializing, please try again in a moment")
        
    try:
        # Get both raw data and analysis
        analysis = await analyzer.analyze_data(request.query)
        
        # Get raw data separately using analyzer's parse_query method
        indicator, country_code, start_year, end_year = analyzer.parse_query(request.query)
        raw_data = await get_data(
            country_code=country_code,
            query=indicator,
            start_year=start_year,
            end_year=end_year
        )
        
        if isinstance(raw_data, str) and ("error" in raw_data.lower() or "invalid" in raw_data.lower()):
            raise HTTPException(status_code=400, detail=raw_data)
            
        return {
            "raw_data": raw_data,
            "analysis": analysis
        }
    except Exception as e:
        error_msg = str(e)
        if "Could not identify" in error_msg or "Could not find ISO code" in error_msg:
            raise HTTPException(status_code=400, detail=error_msg)
        raise HTTPException(status_code=500, detail=f"Error processing request: {error_msg}")

# ✅ Define a request model for Swagger
class GetDataRequest(BaseModel):
    country_code: str
    query: str
    start_year: int = 2000
    end_year: int = 2025

# ✅ SSE endpoint
@app.get("/mcp/sse")
async def mcp_sse():
    async def event_generator():
        yield {
            "event": "message",
            "data": json.dumps({
                "type": "ready",
                "tools": {
                    "get_data": {
                        "name": "get_data",
                        "description": "Get World Bank data for a country",
                        "parameters": {
                            "country_code": "str",
                            "query": "str",
                            "start_year": "int",
                            "end_year": "int"
                        }
                    }
                }
            })
        }
        
        while True:
            await asyncio.sleep(1)
            yield {"event": "message", "data": json.dumps({"type": "heartbeat"})}

    return EventSourceResponse(event_generator())

if __name__ == "__main__":
    import uvicorn
    # Try different port if 8000 is in use
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except OSError:
        print("Port 8000 is in use, trying port 8001...")
        uvicorn.run(app, host="0.0.0.0", port=8001)
