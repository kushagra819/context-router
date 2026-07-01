"""
MuSiQue 3-Agent Pipeline: Analyzer → Solver → Verifier

Each agent has a specific role in performing multi-hop reasoning over documents.
The pipeline chains them: the output of one feeds into the next.
"""

from src.agents.base_agent import BaseAgent
from src.models.base import BaseModel, ModelResponse


# ──────────────────────────────────────────
# PROMPT TEMPLATES
# ──────────────────────────────────────────

ANALYZER_SYSTEM = "You are an information extraction and reasoning planner. Be concise and precise."

ANALYZER_USER = """Given a multi-hop Question and a set of Context Paragraphs, perform the following tasks:
1. Identify the sub-questions (reasoning hops) required to answer the question.
2. Select only the relevant facts and paragraphs from the context that are needed for each hop.

Question: {question}

Context Paragraphs:
{formatted_context}

Provide a structured analysis identifying the required reasoning path and the relevant facts. Do NOT answer the question yet."""


SOLVER_SYSTEM = "You are a multi-hop reasoning solver. Always show your reasoning steps and propose an answer."

SOLVER_USER = """Solve this multi-hop question using the provided context paragraphs and the step-by-step plan/facts identified by the analyzer.

Question: {question}

Context Paragraphs:
{formatted_context}

Analyzer's Fact Selection & Reasoning Path:
{analysis}

Resolve each reasoning hop step-by-step. Propose a final concise answer based on the facts."""


VERIFIER_SYSTEM = ("You are a factual verifier. Check reasoning carefully against the context. "
                   "You MUST end with a line exactly 'Final Answer: <span>' where <span> is ONLY "
                   "the short answer (a name, entity, date, number, or yes/no) with NO Markdown, "
                   "NO asterisks, and NO explanatory sentence.")

VERIFIER_USER = """Verify this multi-hop reasoning solution for factual accuracy using the original context.

Question: {question}

Context Paragraphs:
{formatted_context}

Proposed Solution:
{solution}

Ensure that:
1. All steps in the reasoning are fully supported by the context paragraphs.
2. The final answer is concise and directly answers the question.

If correct, confirm it. If there is a factual error, correct the reasoning and fix the answer.
Your response MUST end with a single line in EXACTLY this format (no Markdown, no bold, no asterisks):
Final Answer: <only the short answer span — a name, entity, date, number, or yes/no; nothing else>"""


# ──────────────────────────────────────────
# AGENT FACTORY
# ──────────────────────────────────────────

def create_musique_agents(model: BaseModel) -> dict[str, BaseAgent]:
    """Create the 3 MuSiQue agents all using the same model."""
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


def format_musique_context(paragraphs_list: list[dict]) -> str:
    """Format the paragraphs list from MuSiQue dataset into a clean string for prompts."""
    formatted_context = ""
    for para in paragraphs_list:
        title = para.get("title", "Untitled")
        text = para.get("paragraph_text", "").strip()
        formatted_context += f"Document: {title}\nContent: {text}\n\n"
    return formatted_context.strip()


def run_musique_pipeline(agents: dict[str, BaseAgent], question: str, paragraphs_list: list[dict]) -> dict:
    """
    Run the full 3-agent pipeline on a single MuSiQue problem.
    
    Flow: question + context → analyzer → solver → verifier → final_answer
    
    Returns dict with all intermediate outputs and metadata.
    """
    results = {
        "question": question,
        "agent_responses": {},
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_latency": 0.0,
        "total_cost": 0.0,
    }

    formatted_context = format_musique_context(paragraphs_list)

    # Step 1: Analyzer
    analyzer_response = agents["analyzer"].run(
        question=question,
        formatted_context=formatted_context,
    )
    results["agent_responses"]["analyzer"] = analyzer_response
    results["total_input_tokens"] += analyzer_response.input_tokens
    results["total_output_tokens"] += analyzer_response.output_tokens
    results["total_latency"] += analyzer_response.latency
    results["total_cost"] += analyzer_response.cost_usd

    # Step 2: Solver (receives question + context + analysis)
    solver_response = agents["solver"].run(
        question=question,
        formatted_context=formatted_context,
        analysis=analyzer_response.text,
    )
    results["agent_responses"]["solver"] = solver_response
    results["total_input_tokens"] += solver_response.input_tokens
    results["total_output_tokens"] += solver_response.output_tokens
    results["total_latency"] += solver_response.latency
    results["total_cost"] += solver_response.cost_usd

    # Step 3: Verifier (receives question + context + solution)
    verifier_response = agents["verifier"].run(
        question=question,
        formatted_context=formatted_context,
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
