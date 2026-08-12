import sqlite3
from typing import Dict, Any, Optional
from database import get_db_connection

def get_schema(db_path: Optional[str] = None, table_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve database schema including table names, columns, data types, primary keys,
    and foreign key relationships.

    Args:
        db_path (Optional[str]): Optional custom path to SQLite database.
        table_name (Optional[str]): Optional specific table to fetch schema for.

    Returns:
        Dict[str, Any]: JSON-formatted schema representation of database structure.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    try:
        # Get list of tables
        if table_name:
            tables = [table_name]
        else:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = [row[0] for row in cursor.fetchall()]

        schema_info = {
            "database_type": "SQLite",
            "table_count": len(tables),
            "tables": {}
        }

        for tbl in tables:
            # Columns metadata
            cursor.execute(f"PRAGMA table_info('{tbl}');")
            columns_raw = cursor.fetchall()
            columns = [
                {
                    "cid": col["cid"],
                    "name": col["name"],
                    "type": col["type"],
                    "notnull": bool(col["notnull"]),
                    "default_value": col["dflt_value"],
                    "pk": bool(col["pk"])
                }
                for col in columns_raw
            ]

            # Foreign keys metadata
            cursor.execute(f"PRAGMA foreign_key_list('{tbl}');")
            fk_raw = cursor.fetchall()
            foreign_keys = [
                {
                    "id": fk["id"],
                    "from_column": fk["from"],
                    "target_table": fk["table"],
                    "target_column": fk["to"]
                }
                for fk in fk_raw
            ]

            # Total row count
            cursor.execute(f"SELECT COUNT(*) FROM '{tbl}';")
            row_count = cursor.fetchone()[0]

            schema_info["tables"][tbl] = {
                "columns": columns,
                "foreign_keys": foreign_keys,
                "total_rows": row_count
            }

        conn.close()
        return {
            "status": "success",
            "schema": schema_info
        }
    except Exception as e:
        conn.close()
        return {
            "status": "error",
            "message": f"Failed to retrieve schema: {str(e)}"
        }

# Tool spec for LLM function calling
GET_SCHEMA_SPEC = {
    "name": "get_schema",
    "description": "Retrieves the database schema including all tables, column names, data types, primary keys, and foreign key relations.",
    "parameters": {
        "type": "object",
        "properties": {
            "table_name": {
                "type": "string",
                "description": "Optional specific table name to inspect. Leave empty to retrieve the entire database schema."
            }
        },
        "required": []
    }
}
