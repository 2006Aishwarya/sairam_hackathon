from typing import Dict, Any, List, Optional

SUPPORTED_CHART_TYPES = ["bar", "line", "pie", "scatter", "area"]

def generate_chart(
    chart_type: str,
    title: str,
    data: List[Dict[str, Any]],
    x_key: str,
    y_keys: List[str],
    description: Optional[str] = None,
    color_palette: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate a dynamic visualization specification (Bar, Line, Pie, Scatter, Area) for frontend rendering.

    Args:
        chart_type (str): Type of chart ('bar', 'line', 'pie', 'scatter', 'area').
        title (str): Title for the visualization.
        data (List[Dict[str, Any]]): Query result dataset as list of key-value dictionaries.
        x_key (str): Column name to use for X-axis / Categorical dimension / Labels.
        y_keys (List[str]): List of column names to plot on Y-axis / Numeric values.
        description (Optional[str]): Explanatory caption for the chart.
        color_palette (Optional[List[str]]): Custom hex color palette override.

    Returns:
        Dict[str, Any]: Structured JSON chart specification ready for Recharts / frontend rendering.
    """
    normalized_type = chart_type.lower().strip()
    if normalized_type not in SUPPORTED_CHART_TYPES:
        normalized_type = "bar"

    default_colors = ["#6366F1", "#10B981", "#F59E0B", "#EC4899", "#8B5CF6", "#3B82F6", "#14B8A6"]
    colors = color_palette if color_palette else default_colors

    # Format data specifically for Pie charts if needed
    formatted_dataset = data
    if normalized_type == "pie":
        # Ensure pie data has both 'name'/'value' and original keys mapped
        val_key = y_keys[0] if y_keys else "value"
        formatted_dataset = [
            {
                "name": str(item.get(x_key, f"Item {i}")),
                "value": float(item.get(val_key, 0)) if item.get(val_key) is not None else 0,
                x_key: str(item.get(x_key, f"Item {i}")),
                val_key: float(item.get(val_key, 0)) if item.get(val_key) is not None else 0
            }
            for i, item in enumerate(data)
        ]

    chart_spec = {
        "status": "success",
        "chart_type": normalized_type,
        "title": title,
        "description": description or f"{title} visualization",
        "x_key": x_key,
        "y_keys": y_keys,
        "colors": colors[:max(len(y_keys), len(formatted_dataset))],
        "data": formatted_dataset,
        "total_items": len(formatted_dataset)
    }

    return chart_spec

# Tool spec for LLM function calling
GENERATE_CHART_SPEC = {
    "name": "generate_chart",
    "description": "Generates a structured data chart specification (bar, line, pie, scatter, area) to render interactive graphs from query results.",
    "parameters": {
        "type": "object",
        "properties": {
            "chart_type": {
                "type": "string",
                "enum": ["bar", "line", "pie", "scatter", "area"],
                "description": "Type of visualization to construct."
            },
            "title": {
                "type": "string",
                "description": "Descriptive title for the chart."
            },
            "data": {
                "type": "array",
                "items": {"type": "object"},
                "description": "The dataset records returned from execute_query."
            },
            "x_key": {
                "type": "string",
                "description": "The column name for X-axis / category labels."
            },
            "y_keys": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Array of column names containing numeric values for the Y-axis."
            },
            "description": {
                "type": "string",
                "description": "Brief summary of what the chart illustrates."
            }
        },
        "required": ["chart_type", "title", "data", "x_key", "y_keys"]
    }
}
