import os
from typing import Dict, Any, Optional
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import re
from datetime import datetime
import logging

class MistralAnalyzer:
    def __init__(self):
        # Initialize logger
        self.logger = logging.getLogger("MistralAnalyzer")
        
        # Initialize MistralAI client
        mistral_api_key = 'api'
        
        self.client = MistralClient(api_key=mistral_api_key)

    def _create_analysis_prompt(self, country: str, indicator: str, data: Dict[str, Any]) -> str:
        """Create a prompt for data analysis"""
        # Extract data points for the prompt
        data_points = data.get("data", [])
        metadata = data.get("metadata", {})
        
        # Format data points for the prompt
        formatted_data = []
        for point in data_points:
            formatted_data.append(f"Year: {point['year']}, Value: {point['value']}")
        
        data_str = "\n".join(formatted_data)
        
        return f"""You are an expert economic analyst. Analyze the following {indicator} data for {country} and provide:
1. A clear summary of the trends
2. Key observations and insights
3. Potential factors influencing the changes
4. Comparison with global or regional averages if relevant
5. Future outlook based on the trends

Indicator Details:
- Name: {metadata.get('indicator_name')}
- Unit: {metadata.get('unit', 'Not specified')}
- Source: World Bank

Data Points:
{data_str}

Please provide a well-structured, detailed analysis that would be helpful for understanding the economic situation of {country} based on this {indicator} data."""

    async def analyze_data(self, country: str, indicator: str, data: Dict[str, Any]) -> str:
        """
        Analyze the data using MistralAI
        """
        try:
            # Create analysis prompt
            prompt = self._create_analysis_prompt(country, indicator, data)
            
            # Attempt to use the specified model
            try:
                response = self.client.chat(
                    model="mistral-large",
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
            except Exception as e:
                self.logger.warning(f"Failed to use mistral-large model: {str(e)}. Falling back to mistral-medium.")

            # Fallback to medium model if large model fails
            response = self.client.chat(
                model="mistral-medium",
                messages=[
                    {
                        "role": "user",
                        "content": f"Analyze this economic data:\n{prompt}"
                    }
                ]
            )
            return response.choices[0].message.content
            
        except Exception as e:
            error_msg = str(e)
            if "API key" in error_msg.lower():
                return "Error: Invalid or missing MistralAI API key. Please check your environment variables."
            return f"Error during analysis: {error_msg}" 
