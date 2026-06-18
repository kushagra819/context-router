"""Quick script to dump all high rate limit tier models from GitHub Models catalog."""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("GITHUB_TOKEN") or "YOUR_GITHUB_TOKEN_HERE"
URL = "https://models.github.ai/catalog/models"

headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {TOKEN}",
    "X-GitHub-Api-Version": "2022-11-28"
}

try:
    resp = requests.get(URL, headers=headers, timeout=15)
    if resp.status_code == 200:
        data = resp.json()
        models = data.get("data") if isinstance(data, dict) else data
        if not isinstance(models, list) and isinstance(data, list):
            models = data
            
        if isinstance(models, list):
            print("=== HIGH/STANDARD Rate Limit Tier Models (Available for Free) ===\n")
            count = 0
            for m in models:
                if isinstance(m, dict):
                    tier = m.get("rate_limit_tier", "").lower()
                    if tier in ["high", "standard"]:
                        count += 1
                        print(f"Model ID:  {m.get('id')}")
                        print(f"Name:      {m.get('name')}")
                        print(f"Publisher: {m.get('publisher')}")
                        print(f"Tier:      {m.get('rate_limit_tier')}")
                        print(f"Summary:   {m.get('summary')}")
                        limits = m.get("limits", {})
                        print(f"Context:   {limits.get('max_input_tokens', 'N/A')} input / {limits.get('max_output_tokens', 'N/A')} output")
                        print("-" * 50)
            print(f"Total High/Standard models: {count}")
        else:
            print("Response structure was not a list.")
    else:
        print(f"Error {resp.status_code}: {resp.text}")
except Exception as e:
    print(f"Request failed: {e}")
