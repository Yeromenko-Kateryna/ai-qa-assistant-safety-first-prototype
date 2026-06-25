from app.pipeline import run_requirement_analysis_pipeline_from_text
from app.renderer import render_requirement_analysis_markdown


def run_local_demo(raw_text: str) -> str:
    """Composes the deterministic safety gate, requirement analysis pipeline, and renderer."""
    # 1. Execute the requirement analysis pipeline from text
    result = run_requirement_analysis_pipeline_from_text(raw_text)

    # 2. Render the pipeline result as Markdown and return it
    return render_requirement_analysis_markdown(result)
