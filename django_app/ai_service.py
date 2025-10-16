"""
AI service for analyzing financial chart images using OpenAI GPT-4 Vision.
"""

import os
import base64
import time
import random
from pathlib import Path
from dotenv import dotenv_values
from openai import OpenAI
from .chart_examples import CHART_ANALYSIS_EXAMPLES


def _read_config_parameter(param_name: str) -> str | None:
    """
    Read a configuration parameter from the .env.local file without mutating the current environment.
    Note that it's important that the function reads the parameter from the .env.local file first,
    and then from the environment variables.
    Case-insensitive.
    """
    param_name = param_name.upper()
    file = Path(".env.local")
    env_map = dotenv_values(file) if file.exists() else {}
    value_from_env_local = env_map.get(param_name)
    value_from_env = os.getenv(param_name)
    return value_from_env_local or value_from_env or None


def encode_image(image_path: str) -> str:
    """
    Encode image to base64 string for OpenAI API.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def get_few_shot_examples() -> str:
    """
    Create few-shot examples string for the AI prompt.
    """
    examples_text = "Here are some examples of the style we want:\n\n"

    # Use a random selection of examples to provide variety
    selected_examples = random.sample(CHART_ANALYSIS_EXAMPLES, min(3, len(CHART_ANALYSIS_EXAMPLES)))

    for i, example in enumerate(selected_examples, 1):
        examples_text += f"Example {i}:\n"
        examples_text += f"Visual Description: {example['visual_description']}\n"
        examples_text += f"Pattern Analysis: {example['pattern_analysis']}\n"
        examples_text += f"Humorous Prediction: {example['humorous_prediction']}\n"
        examples_text += f"Technical Explanation: {example['technical_explanation']}\n\n"

    return examples_text


def create_analysis_prompt() -> str:
    """
    Create the main prompt for chart analysis.
    """
    few_shot_examples = get_few_shot_examples()

    prompt = f"""You are a hilarious financial chart analyst who combines serious technical analysis knowledge with absurd humor and creative pattern recognition. Your job is to analyze financial charts and provide entertaining, witty commentary while maintaining the structure of legitimate technical analysis.

{few_shot_examples}

Now, analyze the provided financial chart image and provide your response in the following format:

Visual Description: [Describe what you literally see in the chart - trends, patterns, movements]

Pattern Analysis: [Identify technical patterns but with creative, funny names and interpretations]

Humorous Prediction: [Make a witty, humorous prediction about where the price might go, using creative analogies and metaphors]

Technical Explanation: [Provide a mock-serious technical analysis using real financial terms but with humorous twists and clearly tongue-in-cheek interpretations]

Remember to:
- Be genuinely funny and creative
- Use real financial/technical analysis terminology
- Make absurd but entertaining observations
- Include creative pattern names
- Keep it light-hearted but structured like real analysis
- Don't give actual financial advice - this is purely for entertainment
"""

    return prompt


class ChartAnalysisService:
    """
    Service for analyzing financial chart images using AI.
    """

    def __init__(self):
        self.api_key = _read_config_parameter('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables or .env.local file")

        self.client = OpenAI(api_key=self.api_key)

    def analyze_chart(self, image_path: str) -> dict:
        """
        Analyze a chart image and return structured analysis results.

        Args:
            image_path (str): Path to the image file

        Returns:
            dict: Analysis results with keys:
                - visual_description
                - pattern_analysis
                - humorous_prediction
                - technical_explanation
                - processing_time_seconds
                - confidence_score
        """
        start_time = time.time()

        try:
            # Encode the image
            base64_image = encode_image(image_path)

            # Create the prompt
            prompt = create_analysis_prompt()

            # Make API call to OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.8  # Higher temperature for more creative responses
            )

            # Extract the response content
            content = response.choices[0].message.content

            # Parse the structured response
            analysis_results = self._parse_analysis_response(content)

            # Add metadata
            processing_time = time.time() - start_time
            analysis_results['processing_time_seconds'] = processing_time
            analysis_results['confidence_score'] = random.uniform(0.85, 0.98)  # Mock confidence score

            return analysis_results

        except Exception as e:
            # Return error analysis
            processing_time = time.time() - start_time
            return {
                'visual_description': f"Error analyzing chart: {str(e)}",
                'pattern_analysis': "The 'Technical Difficulties' pattern - very bearish for our AI systems.",
                'humorous_prediction': "Our AI crystal ball seems to have cracked. Try again later when the digital spirits are more cooperative!",
                'technical_explanation': f"The error logs show classic signs of API fatigue. Recommendation: Feed the AI more coffee and try again. Error details: {str(e)}",
                'processing_time_seconds': processing_time,
                'confidence_score': 0.0
            }

    def _parse_analysis_response(self, content: str) -> dict:
        """
        Parse the AI response into structured components.
        """
        result = {
            'visual_description': '',
            'pattern_analysis': '',
            'humorous_prediction': '',
            'technical_explanation': ''
        }

        try:
            lines = content.strip().split('\n')
            current_section = None
            current_content = []

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if line.startswith('Visual Description:'):
                    if current_section and current_content:
                        result[current_section] = ' '.join(current_content).strip()
                    current_section = 'visual_description'
                    current_content = [line[len('Visual Description:'):].strip()]
                elif line.startswith('Pattern Analysis:'):
                    if current_section and current_content:
                        result[current_section] = ' '.join(current_content).strip()
                    current_section = 'pattern_analysis'
                    current_content = [line[len('Pattern Analysis:'):].strip()]
                elif line.startswith('Humorous Prediction:'):
                    if current_section and current_content:
                        result[current_section] = ' '.join(current_content).strip()
                    current_section = 'humorous_prediction'
                    current_content = [line[len('Humorous Prediction:'):].strip()]
                elif line.startswith('Technical Explanation:'):
                    if current_section and current_content:
                        result[current_section] = ' '.join(current_content).strip()
                    current_section = 'technical_explanation'
                    current_content = [line[len('Technical Explanation:'):].strip()]
                else:
                    if current_section:
                        current_content.append(line)

            # Don't forget the last section
            if current_section and current_content:
                result[current_section] = ' '.join(current_content).strip()

        except Exception as e:
            # If parsing fails, use the raw content
            result['visual_description'] = content
            result['pattern_analysis'] = "The 'Parsing Error' pattern - our AI got a bit too creative with formatting."
            result['humorous_prediction'] = "The prediction is unclear, much like my ability to follow instructions about response formatting."
            result['technical_explanation'] = f"Technical analysis suggests our parser needs more coffee. Raw response: {content}"

        # Ensure no empty fields
        for key, value in result.items():
            if not value.strip():
                result[key] = "The AI was speechless about this section - a rare occurrence indeed!"

        return result


# Convenience function for easy importing
def analyze_chart_image(image_path: str) -> dict:
    """
    Convenience function to analyze a chart image.
    """
    service = ChartAnalysisService()
    return service.analyze_chart(image_path)