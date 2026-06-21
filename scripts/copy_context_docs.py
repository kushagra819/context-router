import os
import shutil

src_brain_dir = r"C:\Users\Kumud\._gemini\antigravity\brain\c8bfd787-dc87-4063-bf4b-c4fcbb26eb7e".replace('_gemini', 'gemini')
src_active_dir = r"C:\Users\Kumud\._gemini\antigravity-ide\brain\3d9102b2-0219-49e4-9828-f5c0b5bec6af".replace('_gemini', 'gemini')
dest_repo_dir = r"c:\Users\Kumud\Desktop\Research\context-router"

docs_dir = os.path.join(dest_repo_dir, "docs")
planning_dir = os.path.join(docs_dir, "planning")
diagrams_dir = os.path.join(planning_dir, "diagrams")

# Create directories if they do not exist
os.makedirs(docs_dir, exist_ok=True)
os.makedirs(planning_dir, exist_ok=True)
os.makedirs(diagrams_dir, exist_ok=True)

# Copy implementation plan from current session
impl_plan_src = os.path.join(src_active_dir, "implementation_plan.md")
impl_plan_dest = os.path.join(docs_dir, "implementation_plan.md")
if os.path.exists(impl_plan_src):
    shutil.copy2(impl_plan_src, impl_plan_dest)
    print(f"Copied implementation_plan.md to {impl_plan_dest}")
else:
    print("Warning: Active session implementation_plan.md not found!")

# Copy project audit
audit_src = os.path.join(src_brain_dir, "project_audit.md")
audit_dest = os.path.join(docs_dir, "project_audit.md")
if os.path.exists(audit_src):
    shutil.copy2(audit_src, audit_dest)
    print(f"Copied project_audit.md to {audit_dest}")
else:
    print("Warning: project_audit.md not found in old brain directory!")

# Files to copy to docs/planning/
files_to_copy = [
    ("algorithms_and_results.md", "algorithms_and_results.md"),
    ("con_verification.md.resolved", "con_verification.md"),
    ("con_verification.md", "con_verification_orig.md"),
    ("faculty_deliverable.md.resolved", "faculty_deliverable.md"),
    ("faculty_deliverable_graphrag.md.resolved", "faculty_deliverable_graphrag.md"),
    ("faculty_research_review.md", "faculty_research_review.md"),
    ("gamma_slides_prompt.md", "gamma_slides_prompt.md"),
    ("graphrag_assessment.md.resolved", "graphrag_assessment.md"),
    ("llm_hierarchy.md", "llm_hierarchy.md"),
    ("multi_industry_proposal.md", "multi_industry_proposal.md"),
    ("project_summary.md", "project_summary.md"),
    ("research_brief.md.resolved", "research_brief.md"),
    ("research_defense.md", "research_defense.md"),
    ("tier3_replacement_analysis.md", "tier3_replacement_analysis.md"),
    ("tier_comparison_analysis.md", "tier_comparison_analysis.md"),
    ("walkthrough.md", "walkthrough.md"),
    ("task.md.resolved", "task.md")
]

for src_name, dest_name in files_to_copy:
    src_path = os.path.join(src_brain_dir, src_name)
    if not os.path.exists(src_path):
        # try without .resolved extension if applicable
        alt_src_name = src_name.replace(".resolved", "")
        src_path = os.path.join(src_brain_dir, alt_src_name)
        
    if os.path.exists(src_path):
        dest_path = os.path.join(planning_dir, dest_name)
        shutil.copy2(src_path, dest_path)
        print(f"Copied {src_name} -> {dest_path}")
    else:
        print(f"Skip (not found): {src_name}")

# Copy image files
images = [
    "architecture_diagram_1780421238021.png",
    "architecture_v2_1780421832067.png",
    "media__1780421128293.png",
    "routing_comparison_1780421269475.png",
    "tech_stack_1780421302289.png"
]

for img in images:
    src_path = os.path.join(src_brain_dir, img)
    if os.path.exists(src_path):
        dest1 = os.path.join(planning_dir, img)
        dest2 = os.path.join(diagrams_dir, img)
        shutil.copy2(src_path, dest1)
        shutil.copy2(src_path, dest2)
        print(f"Copied image {img} to planning/ and planning/diagrams/")
    else:
        print(f"Warning: Image {img} not found!")

print("All copies completed successfully!")
