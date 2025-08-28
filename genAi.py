import openai
import json
import re
from openai import OpenAI
import markdown

openai.api_key = "sk-b0b211a091df40c0acac8b9bfba45720"
openai.base_url = "https://api.deepseek.com"
perturbation_data = None
openai.api_key = "sk-b0b211a091df40c0acac8b9bfba45720"
openai.base_url = "https://api.deepseek.com"

client = OpenAI(api_key="sk-b0b211a091df40c0acac8b9bfba45720", base_url="https://api.deepseek.com")

def generate_perturbation(columns):

    prompt = f"""I have a dataset with the following columns: {columns}. I want you to generate realistic perturbations for this dataset. The perturbation should reflect a plausible real-world scenario where a value for one or more of these columns changes. For example, if "Qualité" (a quality score) drops to zero, this could mean the supplier's product quality has drastically worsened. Similarly, if "Cost" increases significantly, this might indicate price hikes due to changes in the market or supply chain issues.
    
     Please create a JSON objects that will be generic for all suppliers, representing a perturbation. The keys in the JSON objects will be the column names, and the values will be the perturbed values. Think about realistic situations where these values could change, and make sure the resulting changes reflect realistic business scenarios to test resilience.
    
     all weights should be positive and scaled
     
     weight should be between 0 and 1
    
     only one scenario
    
     exemple of result:
     {{
       "Qualité": 0.2,
       "Cost": 0.5
     }}
     
     with well formated and detailed explanation of scenario
     """

    def is_valid(data):
        """Check that all numeric values are between 0 and 1 (exclusive)."""
        return all(isinstance(v, (int, float)) and 0 < v < 1 for v in data.values())

    for attempt in range(5):
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": prompt}
            ],
            stream=False
        )

        print(response)
        resp = response.choices[0].message.content
        resp = markdown.markdown(resp)
        match = re.search(r'\{.*\}', resp, re.DOTALL)
        if not match:
            continue  # try again if no JSON found

        json_str = match.group(0)

        try:
            perturbation_data = json.loads(json_str)
        except json.JSONDecodeError:
            continue  # invalid JSON, try again

        if is_valid(perturbation_data):
            return resp, perturbation_data
        # else: retry until valid

    raise ValueError("Failed to generate valid perturbation after several retries")
