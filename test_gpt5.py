"""Test script to probe different OpenAI/GPT model IDs on GitHub Models API."""
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Get one of the tokens
token = os.getenv("GITHUB_TOKEN_4") or os.getenv("GITHUB_TOKEN") or "YOUR_GITHUB_TOKEN_HERE"
print(f"Using token: {token[:8]}...")

client = OpenAI(
    base_url="https://models.github.ai/inference",
    api_key=token,
)

candidate_models = [
    "openai/gpt-5",
    "openai/gpt-4.1",
    "openai/gpt-4.1-mini",
    "openai/gpt-4o",
    "openai/gpt-4o-mini"
]

print("Probing candidate OpenAI models on GitHub Models inference endpoint...")
for model_id in candidate_models:
    print(f"\nTesting: {model_id} ...")
    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "user", "content": "Hello! Respond in 3 words."}
            ],
            temperature=0.1,
            max_tokens=10
        )
        print(f"  ✅ Success! Response: {response.choices[0].message.content.strip()}")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
