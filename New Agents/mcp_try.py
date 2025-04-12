# import requests

# # Define the URL for the MCP fetch endpoint
# url = "http://localhost:5000/mcp/fetch"

# # Define the payload for the request
# payload = {
#     "query": "Give me GDP per capita of India from 2000 to 2025"
# }

# # Send a POST request to the MCP server
# response = requests.post(url, json=payload)

# # Print the response from the server
# print(response.json())


import json
import subprocess

# Use a raw string to avoid Unicode escape issues
config_path = r'C:\Users\subed\.cursor\mcp.json'

# Load the configuration file
try:
    with open(config_path, 'r') as file:
        config = json.load(file)
except FileNotFoundError:
    print(f"Configuration file not found: {config_path}")
    exit(1)

# Get the command and arguments for the agent
agent_config = config['mcpServers']['documentation']
command = agent_config['command']
args = agent_config['args']

# Start the server
subprocess.run([command] + args)