from flask import Flask, render_template, request, jsonify
import asyncio
from src.agents.master_agent import MasterAgent
from main import QueryParser

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    query = data.get('query')
    
    # Initialize the parser and master agent
    parser = QueryParser()
    master = MasterAgent()

    # Parse the query and fetch data
    params = asyncio.run(parser.parse_query(query))
    result = asyncio.run(master.fetch_with_retry(params))

    # Convert result to a dictionary for JSON serialization using model_dump
    result_dict = result.model_dump()

    return jsonify(result_dict)

if __name__ == '__main__':
    app.run(debug=True)