"""
Diagnostic script to test every configured API key for all providers.
Checks whether each key is active (200 OK), temporarily rate-limited, or permanently exhausted.
"""
import os
import sys
import requests
import json
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.config import (
    GROQ_API_KEYS,
    GOOGLE_API_KEYS,
    GITHUB_TOKENS,
    OPENROUTER_API_KEYS,
    SAMBANOVA_API_KEYS,
)

def test_groq_key(key, idx):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    body = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 1,
    }
    try:
        resp = requests.post(url, headers=headers, json=body, timeout=10)
        return resp.status_code, resp.text
    except Exception as e:
        return 0, str(e)

def test_github_key(key, idx):
    url = "https://models.github.ai/inference/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    body = {
        "model": "Meta-Llama-3.1-405B-Instruct",
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 1,
    }
    try:
        resp = requests.post(url, headers=headers, json=body, timeout=10)
        return resp.status_code, resp.text
    except Exception as e:
        return 0, str(e)

def test_openrouter_key(key, idx):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/Kumud/context-router",
        "X-Title": "Context-Aware LLM Router Research Project",
    }
    body = {
        "model": "nousresearch/hermes-3-llama-3.1-405b:free",
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 1,
    }
    try:
        resp = requests.post(url, headers=headers, json=body, timeout=10)
        return resp.status_code, resp.text
    except Exception as e:
        return 0, str(e)

def test_gemini_key(key, idx):
    # Using the standard Google GenAI API endpoint for generateContent
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    body = {
        "contents": [{"parts": [{"text": "ping"}]}]
    }
    try:
        resp = requests.post(url, headers=headers, json=body, timeout=10)
        return resp.status_code, resp.text
    except Exception as e:
        return 0, str(e)

def test_sambanova_key(key, idx):
    url = "https://api.sambanova.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    body = {
        "model": "DeepSeek-V3.1",
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 1,
    }
    try:
        resp = requests.post(url, headers=headers, json=body, timeout=10)
        return resp.status_code, resp.text
    except Exception as e:
        return 0, str(e)

def classify_status(status_code, response_text):
    if status_code == 200:
        return "✅ ACTIVE (200 OK)", None
    elif status_code == 401 or status_code == 403:
        return "❌ EXHAUSTED (Invalid / Unauthorized)", response_text
    elif status_code == 429:
        # Check if it is a daily limit or TPM/RPM
        lower = response_text.lower()
        if any(kw in lower for kw in ["byday", "daily", "quota", "credit", "balance", "limit reached"]):
            return "❌ EXHAUSTED (Quota Exceeded)", response_text
        return "⏳ RATE LIMITED (Temporary TPM/RPM)", response_text
    else:
        return f"❓ ERROR ({status_code})", response_text

def run_tests():
    providers = {
        "Groq": (GROQ_API_KEYS, test_groq_key),
        "GitHub Models": (GITHUB_TOKENS, test_github_key),
        "OpenRouter": (OPENROUTER_API_KEYS, test_openrouter_key),
        "Gemini": (GOOGLE_API_KEYS, test_gemini_key),
        "SambaNova": (SAMBANOVA_API_KEYS, test_sambanova_key),
    }

    print("=" * 60)
    print("           API KEY EXHAUSTION DIAGNOSTIC")
    print("=" * 60)

    summary = {}

    for name, (keys, test_func) in providers.items():
        print(f"\n📡 Testing {name} Keys ({len(keys)} configured)...")
        print("─" * 60)
        
        summary[name] = {"total": len(keys), "active": 0, "exhausted": 0, "temp_limit": 0, "error": 0}
        
        for idx, key in enumerate(keys, 1):
            masked = key[:8] + "..." + key[-6:] if len(key) > 14 else "..."
            sys.stdout.write(f"  🔑 Key #{idx} ({masked}): Checking... ")
            sys.stdout.flush()
            
            code, text = test_func(key, idx)
            status, detail = classify_status(code, text)
            
            print(status)
            
            if "ACTIVE" in status:
                summary[name]["active"] += 1
            elif "EXHAUSTED" in status:
                summary[name]["exhausted"] += 1
                # Print clean snippet of the error message for exhaustion debugging
                try:
                    err_json = json.loads(text)
                    clean_err = err_json.get("error", {}).get("message", text[:120])
                except:
                    clean_err = text[:120]
                print(f"      Reason: {clean_err.strip()}")
            elif "RATE LIMITED" in status:
                summary[name]["temp_limit"] += 1
                print(f"      Wait/Retry needed (temporary limits)")
            else:
                summary[name]["error"] += 1
                print(f"      Detail: {text[:120]}")

    print("\n" + "=" * 60)
    print("                  DIAGNOSTIC SUMMARY")
    print("=" * 60)
    for name, stats in summary.items():
        print(f"{name:15}: Total: {stats['total']} | Active: {stats['active']} | Exhausted: {stats['exhausted']} | Temp Rate Limit: {stats['temp_limit']} | Error: {stats['error']}")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
