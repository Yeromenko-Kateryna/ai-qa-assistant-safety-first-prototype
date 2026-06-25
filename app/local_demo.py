from app.pipeline import run_requirement_analysis_pipeline_from_text
from app.renderer import render_requirement_analysis_markdown
from app.output_safety import validate_markdown_output


def run_local_demo(raw_text: str) -> str:
    """Composes the deterministic safety gate, requirement analysis pipeline, renderer, and output safety gate."""
    # 1. Execute the requirement analysis pipeline from text
    result = run_requirement_analysis_pipeline_from_text(raw_text)

    # 2. Render the pipeline result as Markdown
    markdown = render_requirement_analysis_markdown(result)

    # 3. Validate Markdown output using the safety gate and return
    return validate_markdown_output(markdown)
