# Context-Aware LLM Routing — Documentation Directory & Trajectory Map

This directory serves as the documentation and research history for the **Context-Aware LLM Routing for Multi-Agent AI Systems** project. 

Because research projects evolve, the documents stored under `docs/planning/` represent different chronological milestones in our research trajectory. This map aligns the planning history with the **final implementation** currently present in the codebase.

---

## 1. Ground Truth Codebase Implementation

The active codebase implements a **4-Tier LLM Hierarchy** configured as follows:

| Tier | Model | Provider / API | Parameter Scale | Cost per 1M Tokens (Input/Output) | Role in Multi-Agent Pipeline |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **Tier 1** 🟢 | **Gemma 4B** | Ollama (Local) | 4B | $0.03 / $0.06 | **Edge Baseline:** Handles routine analysis, syntax parsing, and simple checks. |
| **Tier 2** 🔵 | **Llama 3.3 70B** | Groq API | 70B | $0.59 / $0.79 | **Reasoning Workhorse:** Handles standard problem solving and mathematical steps. |
| **Tier 3** 🟡 | **Llama 3.1 405B** | GitHub Models API | 405B | $2.66 / $2.66 | **Advanced Reasoning:** Handles complex step execution and validation. |
| **Tier 4** 🔴 | **GPT-4.1** | GitHub Models API | ~1.8T (est.) | $2.00 / $8.00 | **Proprietary Oracle:** Ultimate fallback for edge cases and final verification. |

*Note: In the codebase, Tier 4 is implemented as `GPT41Model` (`src/models/gpt41_model.py`) and executes `openai/gpt-4.1`.*

---

## 2. Topic Alignment

Our primary research topic is **Topic A: Context-Aware Compute Routing**. 
The alternative topic **Topic B: GraphRAG** was assessed and rejected during the feasibility phase (documented in the deprecated files).

---

## 3. Documentation Map

Below is a guide to every document in `docs/` and `docs/planning/`, categorized by its role and version:

### Core Project Specifications (Ground Truth)
These files represent the final specification of the project as built:
*   [docs/project_audit.md](file:///c:/Users/Kumud/Desktop/Research/context-router/docs/project_audit.md) — The comprehensive audit of the codebase, baseline runs, and identified code issues.
*   [docs/implementation_plan.md](file:///c:/Users/Kumud/Desktop/Research/context-router/docs/implementation_plan.md) — The active execution plan for Stage 1 (Cleanup, Docs, and Truth-Locking).

---

### Planning & Context Archive (`docs/planning/`)

These documents represent our research progression and are kept to provide context for academic defenses and presentations:

| File | Research Milestone | Tier Stack Described | Key Relevance to Final System |
| :--- | :--- | :---: | :--- |
| [algorithms_and_results.md](file:///c:/Users/Kumud/Desktop/Research/context-router/docs/planning/algorithms_and_results.md) | Early Prototype Summary | 3-Tier (Gemma 4B / Llama 70B / GPT-4o-mini) | Captures initial findings where the multi-agent pipeline boosted Gemma 4B to 94.5% accuracy. |
| [con_verification.md](file:///c:/Users/Kumud/Desktop/Research/context-router/docs/planning/con_verification.md) | Feasibility Critique | Multi-Tier | Analyzes and mitigates potential academic/reviewer criticisms of the routing topic. |
| [faculty_deliverable.md](file:///c:/Users/Kumud/Desktop/Research/context-router/docs/planning/faculty_deliverable.md) | Dr. Deshpande Submission | 3-Tier (Llama 8B / Llama 70B / GPT-4o-mini) | The formal proposal submitted to Dr. Himani Deshpande on May 30, 2026. |
| [gamma_slides_prompt.md](file:///c:/Users/Kumud/Desktop/Research/context-router/docs/planning/gamma_slides_prompt.md) | Presentation Design | 3-Tier (Llama 8B / GPT-4o-mini / GPT-4o) | Structured prompts used to generate the 8-slide pitch deck for the department. |
| [llm_hierarchy.md](file:///c:/Users/Kumud/Desktop/Research/context-router/docs/planning/llm_hierarchy.md) | Model Survey | 3-Tier (Gemma 4B / Llama 70B / Llama 405B) | Initial mapping of open-weight models available for the research stack. |
| [multi_industry_proposal.md](file:///c:/Users/Kumud/Desktop/Research/context-router/docs/planning/multi_industry_proposal.md) | Expansion Proposal | 3-Tier (Llama 8B / Llama 70B / GPT-4o) | Proposes expanding the router from GSM8K to Tech (HumanEval), Legal (LegalBench), and Medical (MedQA). |
| [project_summary.md](file:///c:/Users/Kumud/Desktop/Research/context-router/docs/planning/project_summary.md) | Discussion Pitch | 3-Tier (Gemma 4B / Llama 70B / GPT-4o-mini) | A concise, interview-ready summary of the project's business case and research landscape. |
| [research_brief.md](file:///c:/Users/Kumud/Desktop/Research/context-router/docs/planning/research_brief.md) | Literature Survey | 2-Tier (Llama 8B / GPT-4o-mini) | Contains a deep literature map of related routing papers (RouteLLM, BEST-Route, etc.). |
| [research_defense.md](file:///c:/Users/Kumud/Desktop/Research/context-router/docs/planning/research_defense.md) | Reviewer Q&A | 3-Tier (Gemma 4B / Llama 70B / GPT-4o-mini) | A study guide providing defensive arguments for dataset sufficiency and metric selection. |
| [walkthrough.md](file:///c:/Users/Kumud/Desktop/Research/context-router/docs/planning/walkthrough.md) | Development Log | 4-Tier | Detailed walkthrough of the key rotation and terminal failure management built in June. |

---

### Deprecated Archive
These files contain rejected work on the GraphRAG alternative. They are marked **[DEPRECATED]** inside:
*   [docs/planning/faculty_deliverable_graphrag.md](file:///c:/Users/Kumud/Desktop/Research/context-router/docs/planning/faculty_deliverable_graphrag.md)
*   [docs/planning/graphrag_assessment.md](file:///c:/Users/Kumud/Desktop/Research/context-router/docs/planning/graphrag_assessment.md)
*   [docs/planning/task_graphrag_deprecated.md](file:///c:/Users/Kumud/Desktop/Research/context-router/docs/planning/task_graphrag_deprecated.md)
