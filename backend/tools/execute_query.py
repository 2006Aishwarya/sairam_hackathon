import sqlite3
import time
from typing import Dict, Any, Optional
from database import get_db_connection

FORBIDDEN_KEYWORDS = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "REPLACE", "CREATE", "GRANT"]

def execute_query(query: str, db_path: Optional[str] = None, max_rows: int = 100) -> Dict[str, Any]:
    """
    Safely execute a SQL query against the SQLite database and return results as JSON with execution metrics.

    Args:
        query (str): SQL SELECT query string to execute.
        db_path (Optional[str]): Optional custom SQLite database path.
        max_rows (int): Maximum row limit to safeguard response size.

    Returns:
        Dict[str, Any]: Execution result containing columns, rows, execution_time_ms, row_count, or error message.
    """
    clean_query = query.strip()

    # Safety guardrails check
    query_upper = clean_query.upper()
    for kw in FORBIDDEN_KEYWORDS:
        if kw in query_upper.split():
            return {
                "status": "error",
                "message": f"Security Guardrail Violation: Direct modification statement '{kw}' is disabled. Only read-only SELECT queries are allowed.",
                "query": query
            }

    # Ensure LIMIT exists if not aggregated
    if "LIMIT" not in query_upper and max_rows > 0:
        clean_query = f"{clean_query.rstrip(';')} LIMIT {max_rows};"

    start_time = time.perf_counter()
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(clean_query)
        rows_raw = cursor.fetchall()
        end_time = time.perf_counter()

        duration_ms = round((end_time - start_time) * 1000, 2)
        columns = [description[0] for description in cursor.description] if cursor.description else []
        
        # Convert sqlite3.Row to list of dicts and list of lists for tabular rendering
        data = [dict(row) for row in rows_raw]

        conn.close()

        return {
            "status": "success",
            "query": clean_query,
            "columns": columns,
            "data": data,
            "row_count": len(data),
            "execution_time_ms": duration_ms
        }
    except Exception as e:
        conn.close()
        return {
            "status": "error",
            "message": f"SQL Execution Error: {str(e)}",
            "query": clean_query
        }

# Tool spec for LLM function calling
EXECUTE_QUERY_SPEC = {
    "name": "execute_query",
    "description": "Executes a SQL SELECT query against the connected database and returns tabular JSON results, execution time, and row metadata.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The exact SQL SELECT query statement to run."
            },
            "max_rows": {
                "type": "integer",
                "description": "Maximum number of rows to return (default 100)."
            }
        },
        "required": ["query"]
    }
}
