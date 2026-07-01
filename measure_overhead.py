"""Diagnostic: measure model-switching overhead and per-tier latency (LIVE).

Relevant to the paper's latency/throughput discussion. ASCII-only output.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.models import get_model

# Prompt for testing
PROMPT = "Explain gravity in 5 words."

def measure_call(model, name: str):
    print(f"  Calling {name}...")
    start = time.perf_counter()
    try:
        response = model.generate(PROMPT)
        latency = time.perf_counter() - start
        tokens = response.input_tokens + response.output_tokens
        print(f"    OK: {latency:.2f}s ({tokens} tokens, output: '{response.text.strip()[:60]}')")
        return latency
    except Exception as e:
        latency = time.perf_counter() - start
        print(f"    FAILED: {e} ({latency:.2f}s)")
        return None

def main():
    print("=" * 60)
    print("  Context-Aware Router — Switching & Latency Overhead Diagnostic")
    print("=" * 60)
    
    # 1. Instantiate models
    print("\n[1] Initializing model clients...")
    try:
        m1 = get_model(1)  # Gemma 4B (Ollama)
        m2 = get_model(2)  # Llama 3.3 70B (Groq)
        m3 = get_model(3)  # Llama 3.1 405B (GitHub)
        m4 = get_model(4)  # GPT-4.1 (GitHub)
        print("  OK: All model clients initialized.")
    except Exception as e:
        print(f"  ERROR initializing models: {e}")
        return

    # 2. Test Cold-Start vs Warm-Start for Local Ollama (Gemma 4B)
    print("\n[2] Testing Local Ollama (Gemma 4B) Cold vs. Warm Start...")
    print("  (If Ollama was idle, the first call will load it to GPU/RAM)")
    cold_lat = measure_call(m1, "Gemma 4B (Ollama) - Call 1 (Cold?)")
    time.sleep(1.0)
    warm_lat = measure_call(m1, "Gemma 4B (Ollama) - Call 2 (Warm)")
    
    if cold_lat and warm_lat:
        diff = cold_lat - warm_lat
        print(f"  [stats]Local Load/Cold-start overhead: {diff:.2f}s")
    
    # 3. Test Cloud APIs (Groq, GitHub Models)
    print("\n[3] Testing Cloud APIs Connection/Network Latency...")
    measure_call(m2, "Llama 3.3 70B (Groq)")
    measure_call(m3, "Llama 3.1 405B (GitHub)")
    measure_call(m4, "GPT-4.1 (GitHub)")

    # 4. Measure Model-Switching Overhead
    print("\n[4] Measuring Sequential Switching Latency...")
    print("  We will run a 3-agent simulation in two modes:")
    print("  Mode A: Static (Same model thrice: Groq -> Groq -> Groq)")
    print("  Mode B: Routed (Switching models: Ollama -> Groq -> GPT-4.1)")
    
    # Mode A: Static
    print("\n  --- Running Mode A: Static (Groq x3) ---")
    start_static = time.perf_counter()
    measure_call(m2, "Groq (Agent 1)")
    measure_call(m2, "Groq (Agent 2)")
    measure_call(m2, "Groq (Agent 3)")
    total_static = time.perf_counter() - start_static
    print(f"  [stats]Mode A (Static) Total Time: {total_static:.2f}s")

    # Mode B: Routed
    print("\n  --- Running Mode B: Routed (Ollama -> Groq -> GPT-4.1) ---")
    start_routed = time.perf_counter()
    measure_call(m1, "Ollama (Agent 1)")
    measure_call(m2, "Groq (Agent 2)")
    measure_call(m4, "GPT-4.1 (Agent 3)")
    total_routed = time.perf_counter() - start_routed
    print(f"  [stats]Mode B (Routed) Total Time: {total_routed:.2f}s")

    print("\n" + "=" * 60)
    print("  DIAGNOSTIC COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
