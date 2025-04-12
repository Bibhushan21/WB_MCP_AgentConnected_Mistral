from flask import Flask, request, jsonify, render_template
import asyncio
from src.agents.master_agent import MasterAgent
from main import QueryParser
from src.utils.mistral_analyzer import MistralAnalyzer

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/mcp/fetch', methods=['POST'])
def mcp_fetch():
    try:
        data = request.json
        query = data.get('query')
        app.logger.info(f'Received query: {query}')
        
        # Initialize the parser and master agent
        parser = QueryParser()
        master = MasterAgent()

        # Parse the query and fetch data
        params = asyncio.run(parser.parse_query(query))
        app.logger.info(f'Parsed parameters: {params}')
        result = asyncio.run(master.fetch_with_retry(params))

        # Serialize the result to a JSON-serializable format
        result_dict = result.model_dump()

        app.logger.info('Data fetched successfully')
        return jsonify(result_dict)
    except Exception as e:
        app.logger.error(f'Error in mcp_fetch: {str(e)}')
        return jsonify({"error": str(e)}), 500

@app.route('/mcp/analyze', methods=['POST'])
def mcp_analyze():
    try:
        data = request.json
        country = data.get('country')
        indicator = data.get('indicator')
        dataset = data.get('dataset')
        
        app.logger.info(f'Received analysis request for {country}, {indicator}')

        # Initialize the analyzer
        analyzer = MistralAnalyzer()

        # Perform analysis
        analysis_result = asyncio.run(analyzer.analyze_data(country, indicator, dataset))

        app.logger.info('Analysis completed successfully')
        return jsonify({"analysis": analysis_result})
    except Exception as e:
        app.logger.error(f'Error in mcp_analyze: {str(e)}')
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)