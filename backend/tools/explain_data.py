from typing import Dict, Any, List, Optional

def explain_data(
    data: List[Dict[str, Any]],
    query_context: str,
    key_metrics: Optional[Dict[str, Any]] = None,
    highlights: Optional[List[str]] = None,
    recommended_questions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate conversational explanations, key metrics summaries, and actionable insights from data results.

    Args:
        data (List[Dict[str, Any]]): Query result dataset.
        query_context (str): The original user question or objective context.
        key_metrics (Optional[Dict[str, Any]]): Key performance metrics (e.g., total_revenue, avg_order_value).
        highlights (Optional[List[str]]): List of top bullet-point takeaways.
        recommended_questions (Optional[List[str]]): Suggested follow-up queries for the user.

    Returns:
        Dict[str, Any]: Structured natural language summary and business takeaways.
    """
    row_count = len(data)

    # Basic statistical calculations if highlights not provided
    generated_highlights = highlights or []
    if not generated_highlights and row_count > 0:
        first_row = data[0]
        generated_highlights.append(f"Analyzed {row_count} records related to: {query_context}.")
        
        # Look for numeric columns to summarize
        numeric_cols = [k for k, v in first_row.items() if isinstance(v, (int, float))]
        if numeric_cols:
            primary_num_col = numeric_cols[0]
            vals = [r[primary_num_col] for r in data if r.get(primary_num_col) is not None]
            if vals:
                total_val = sum(vals)
                avg_val = round(total_val / len(vals), 2)
                max_val = max(vals)
                generated_highlights.append(f"Total {primary_num_col}: {total_val:,.2f} | Average: {avg_val:,.2f} | Peak: {max_val:,.2f}")

    suggested_followups = recommended_questions or [
        "Would you like to analyze these trends by country or segment?",
        "Should we break this down by product category?",
        "Would you like to export this dataset to CSV or pin it to your dashboard?"
    ]

    return {
        "status": "success",
        "query_context": query_context,
        "row_count": row_count,
        "metrics": key_metrics or {},
        "highlights": generated_highlights,
        "recommended_followups": suggested_followups
    }

# Tool spec for LLM function calling
EXPLAIN_DATA_SPEC = {
    "name": "explain_data",
    "description": "Generates natural language insights, statistical summaries, trend highlights, and recommended follow-up questions from query data.",
    "parameters": {
        "type": "object",
        "properties": {
            "data": {
                "type": "array",
                "items": {"type": "object"},
                "description": "The dataset records to explain."
            },
            "query_context": {
                "type": "string",
                "description": "Context of the natural language query asked."
            },
            "key_metrics": {
                "type": "object",
                "description": "Optional dictionary of calculated metrics (e.g. total_revenue, avg_order_val)."
            },
            "highlights": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Key bullet-point takeaways and insight highlights."
            },
            "recommended_questions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Follow-up questions the user might want to ask next."
            }
        },
        "required": ["data", "query_context"]
    }
}
