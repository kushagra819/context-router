"""
GSM8K 3-Agent Pipeline: Analyzer → Solver → Verifier

Each agent has a specific role in solving grade-school math problems.
The pipeline chains them: the output of one feeds into the next.
"""

from src.agents.base_agent import BaseAgent
from src.models.base import BaseModel, ModelResponse


# ──────────────────────────────────────────
# PROMPT TEMPLATES
# ──────────────────────────────────────────

ANALYZER_SYSTEM = "You are a math problem analyzer. Be concise and precise."

ANALYZER_USER = """Read this math problem and identify:
1. What quantity is being asked for (the final answer)
2. Key numbers and their relationships
3. The step-by-step approach needed to solve it

Problem: {problem}

Provide a clear, concise analysis. Do NOT solve the problem yet."""


SOLVER_SYSTEM = "You are a math solver. Show your work step by step. Always end with exactly: Final Answer: [number]"

SOLVER_USER = """Solve this math problem step by step using the analysis provided.

Problem: {problem}

Analysis: {analysis}

Show each calculation step clearly. 
You MUST end your response with exactly this format:
Final Answer: [your numerical answer]"""


VERIFIER_SYSTEM = "You are a math verifier. Check calculations carefully. Always end with exactly: Final Answer: [number]"

VERIFIER_USER = """Check this math solution for calculation errors.

Original Problem: {problem}

Proposed Solution: {solution}

Verify each step. If the solution is correct, confirm it.
If there is an error, fix it and show the correct calculation.

You MUST end your response with exactly this format:
Final Answer: [your numerical answer]"""


# ──────────────────────────────────────────
# AGENT FACTORY
# ──────────────────────────────────────────

def create_gsm8k_agents(model: BaseModel) -> dict[str, BaseAgent]:
    """Create the 3 GSM8K agents all using the same model."""
    return {
        "analyzer": BaseAgent(
            role="analyzer",
            task_type="extraction",
            system_prompt=ANALYZER_SYSTEM,
            user_prompt_template=ANALYZER_USER,
            model=model,
        ),
        "solver": BaseAgent(
            role="solver",
            task_type="reasoning",
            system_prompt=SOLVER_SYSTEM,
            user_prompt_template=SOLVER_USER,
            model=model,
        ),
        "verifier": BaseAgent(
            role="verifier",
            task_type="verification",
            system_prompt=VERIFIER_SYSTEM,
            user_prompt_template=VERIFIER_USER,
            model=model,
        ),
    }


def run_gsm8k_pipeline(agents: dict[str, BaseAgent], problem: str) -> dict:
    """
    Run the full 3-agent pipeline on a single GSM8K problem.
    
    Flow: problem → analyzer → solver → verifier → final_answer
    
    Returns dict with all intermediate outputs and metadata.
    """
    results = {
        "problem": problem,
        "agent_responses": {},
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_latency": 0.0,
        "total_cost": 0.0,
    }

    # Step 1: Analyzer
    analyzer_response = agents["analyzer"].run(problem=problem)
    results["agent_responses"]["analyzer"] = analyzer_response
    results["total_input_tokens"] += analyzer_response.input_tokens
    results["total_output_tokens"] += analyzer_response.output_tokens
    results["total_latency"] += analyzer_response.latency
    results["total_cost"] += analyzer_response.cost_usd

    # Step 2: Solver (receives problem + analysis)
    solver_response = agents["solver"].run(
        problem=problem,
        analysis=analyzer_response.text,
    )
    results["agent_responses"]["solver"] = solver_response
    results["total_input_tokens"] += solver_response.input_tokens
    results["total_output_tokens"] += solver_response.output_tokens
    results["total_latency"] += solver_response.latency
    results["total_cost"] += solver_response.cost_usd

    # Step 3: Verifier (receives problem + solution)
    verifier_response = agents["verifier"].run(
        problem=problem,
        solution=solver_response.text,
    )
    results["agent_responses"]["verifier"] = verifier_response
    results["total_input_tokens"] += verifier_response.input_tokens
    results["total_output_tokens"] += verifier_response.output_tokens
    results["total_latency"] += verifier_response.latency
    results["total_cost"] += verifier_response.cost_usd

    # Final answer comes from verifier
    results["final_output"] = verifier_response.text

    return results
