"""Diagnostic script to check rate limit headers and API behavior for all configured GITHUB_TOKENS."""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# Gather all tokens
tokens = {}
for i in range(1, 16):
    env_var = "GITHUB_TOKEN" if i == 1 else f"GITHUB_TOKEN_{i}"
    val = os.getenv(env_var)
    if val and not val.startswith("your_"):
        tokens[env_var] = val.strip()

print(f"Loaded {len(tokens)} GitHub tokens from environment/dotenv.")

# Endpoints and models
URL = "https://models.github.ai/inference/chat/completions"

models = {
    "Tier 3 (Llama 405B)": "Meta-Llama-3.1-405B-Instruct",
    "Tier 4 (GPT-4.1)": "openai/gpt-4.1"
}

print("\nProbing rate limits for each token/model combination...")

for token_name, token in sorted(tokens.items()):
    masked = token[:8] + "..." + token[-6:] if len(token) > 14 else "..."
    print(f"\n==========================================")
    print(f"🔑 Token: {token_name} ({masked})")
    print(f"==========================================")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    body = {
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 5,
        "temperature": 0.1
    }
    
    for tier_name, model_id in models.items():
        print(f"\nTesting {tier_name} ({model_id}):")
        body["model"] = model_id
        
        try:
            # Using requests directly to inspect response headers
            resp = requests.post(URL, headers=headers, json=body, timeout=10)
            
            # Print status
            print(f"  HTTP Status: {resp.status_code}")
            
            # Print rate limit headers
            rate_headers = {k: v for k, v in resp.headers.items() if "ratelimit" in k.lower() or "retry" in k.lower()}
            if rate_headers:
                print("  Rate Limit Headers:")
                for k, v in rate_headers.items():
                    print(f"    {k}: {v}")
            else:
                print("  No rate limit headers found in response.")
                
            if resp.status_code == 200:
                print("  ✅ Success")
            elif resp.status_code == 429:
                print(f"  ❌ Rate Limited (429): {resp.text[:300]}")
            else:
                print(f"  ❌ Error {resp.status_code}: {resp.text[:300]}")
                
        except Exception as e:
            print(f"  ❌ Request Failed: {e}")
