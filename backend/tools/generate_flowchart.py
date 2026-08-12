import re
from typing import Dict, Any, Optional

SUPPORTED_DIAGRAM_TYPES = ["er_diagram", "process_flow", "decision_tree", "flowchart"]

def generate_flowchart(
    diagram_type: str,
    title: str,
    mermaid_code: str,
    explanation: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate Mermaid.js markup for ER diagrams, order fulfillment process flows, and decision trees.

    Args:
        diagram_type (str): Type of diagram ('er_diagram', 'process_flow', 'decision_tree', 'flowchart').
        title (str): Title of the diagram.
        mermaid_code (str): Valid Mermaid syntax string representing nodes and relationships.
        explanation (Optional[str]): Explanatory text summarizing the diagram.

    Returns:
        Dict[str, Any]: Structured diagram response containing title, mermaid syntax, and rendering hints.
    """
    normalized_type = diagram_type.lower().strip()
    if normalized_type not in SUPPORTED_DIAGRAM_TYPES:
        normalized_type = "flowchart"

    clean_code = mermaid_code.strip()
    clean_code = re.sub(r"^```(?:mermaid)?\n?", "", clean_code, flags=re.IGNORECASE)
    clean_code = re.sub(r"\n?```$", "", clean_code).strip()

    return {
        "status": "success",
        "diagram_type": normalized_type,
        "title": title,
        "mermaid_code": clean_code,
        "explanation": explanation or f"Diagram showing {title}"
    }

# Tool spec for LLM function calling
GENERATE_FLOWCHART_SPEC = {
    "name": "generate_flowchart",
    "description": "Generates a Mermaid.js diagram (ER Diagram, Process Flow, Decision Tree, Flowchart) to visually illustrate database schemas, order pipelines, or logic trees.",
    "parameters": {
        "type": "object",
        "properties": {
            "diagram_type": {
                "type": "string",
                "enum": ["er_diagram", "process_flow", "decision_tree", "flowchart"],
                "description": "Type of diagram to generate."
            },
            "title": {
                "type": "string",
                "description": "Title of the diagram."
            },
            "mermaid_code": {
                "type": "string",
                "description": "Valid Mermaid syntax block (e.g., 'erDiagram ...' or 'graph TD ...'). Do NOT wrap in markdown code blocks."
            },
            "explanation": {
                "type": "string",
                "description": "Natural language summary explaining what the diagram depicts."
            }
        },
        "required": ["diagram_type", "title", "mermaid_code"]
    }
}
