# The MIT License (MIT)
# Copyright © 2024 PrimeInsightsDAO, philanthrope

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import json
import random
import logging
from typing import Dict
from openai import OpenAI
from .config import get_validation_config, DATA_TYPE_MAP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_sample(data: list, filename: str, openai_api_key: str, validation_config: Dict[str, any]) -> dict:
    client = OpenAI(api_key=openai_api_key)

    sample_size = validation_config["SAMPLE_SIZE"]
    threshold_score = validation_config["THRESHOLD_SCORE"]

    sample = random.sample(data, min(sample_size, len(data)))
    scores = []

    data_type = DATA_TYPE_MAP.get(filename, "Amazon data")

    system_message = create_system_message(data_type)

    for order in sample:
        order_text = "\n".join([f"{key}: {value}" for key, value in order.items()])

        response = client.chat.completions.create(
            model=validation_config["GPT_MODEL"],
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"# Data to evaluate:\n\n{order_text}"}
            ],
        )

        score_json = response.choices[0].message.content.strip()
        logger.info(f"LLM validation response: {score_json}")

        try:
            score_data = json.loads(score_json)
            score = int(score_data["score"]) / 100.0
            scores.append(score)
        except (json.JSONDecodeError, KeyError, ValueError):
            logger.error("Failed to get a valid JSON response.")
            return {
                'is_valid': False,
                'score': 0.0
            }

    avg_score = sum(scores) / len(scores)
    logger.info(f"Average LLM validation score: {avg_score}")

    return {
        'is_valid': avg_score >= (threshold_score/100),
        'score': avg_score
    }

def create_system_message(data_type: str) -> str:
    return (
        f"You are an AI language model assigned to evaluate the following Amazon {data_type} for consistency, validity, data quality, and authenticity (likelihood of being genuine and not fabricated). Carefully analyze the data, considering factors such as:\n\n"
        "- **Data Consistency**: Are the values logically coherent (e.g., dates are in valid formats and sequences, quantities are positive integers, prices make sense)?\n"
        "- **Data Validity**: Are all required fields present and correctly formatted? Do the field values adhere to expected patterns (e.g., Order IDs match the standard format)?\n"
        "- **Data Quality**: Is the data complete and accurate? Are there any missing or anomalous values?\n"
        "- **Authenticity**: Is there any indication that the data might be fabricated or manipulated (e.g., unrealistic values, obviously repeating patterns, inconsistencies, etc)?\n\n"
        "Based on your analysis, assign an overall integer score from 0 to 100, where:\n\n"
        "- **0** indicates the data is invalid, of poor quality, and likely fabricated.\n"
        "- **50** indicates the data is likely genuine but of questionable quality.\n"
        "- **100** indicates the data is highly consistent, valid, of excellent quality, and likely genuine.\n\n"
        "**Important Instructions**:\n\n"
        "- **Output Format**: Provide your response as a single JSON object containing only the key \"score\" and its numerical value (e.g., {\"score\": 85}).\n"
        "- **Do Not Include**: Any additional text, explanations, or commentary. Do not wrap the JSON object in markdown or any other formatting.\n"
        "- **Compliance**: Follow these instructions precisely to ensure accurate evaluation.\n"
    )
