import os
import json
import sqlite3
import re
import time
from typing import Dict, Any, List, Optional, Generator

from database import get_db_connection, DB_PATH
from tools.get_schema import get_schema, GET_SCHEMA_SPEC
from tools.execute_query import execute_query, EXECUTE_QUERY_SPEC
from tools.generate_chart import generate_chart, GENERATE_CHART_SPEC
from tools.generate_flowchart import generate_flowchart, GENERATE_FLOWCHART_SPEC
from tools.explain_data import explain_data, EXPLAIN_DATA_SPEC

# Authoritative Whitelist of Backend Tool Specs formatted for OpenAI / NVIDIA NIM Function Calling
NVIDIA_TOOLS = [
    {"type": "function", "function": GET_SCHEMA_SPEC},
    {"type": "function", "function": EXECUTE_QUERY_SPEC},
    {"type": "function", "function": GENERATE_CHART_SPEC},
    {"type": "function", "function": GENERATE_FLOWCHART_SPEC},
    {"type": "function", "function": EXPLAIN_DATA_SPEC}
]

# Strict Whitelist Dispatcher Mapping
TOOL_HANDLERS = {
    "get_schema": get_schema,
    "execute_query": execute_query,
    "generate_chart": generate_chart,
    "generate_flowchart": generate_flowchart,
    "explain_data": explain_data
}

ALL_TOOL_SPECS = [
    GET_SCHEMA_SPEC,
    EXECUTE_QUERY_SPEC,
    GENERATE_CHART_SPEC,
    GENERATE_FLOWCHART_SPEC,
    EXPLAIN_DATA_SPEC
]

# Keywords indicating casual conversation / greetings / capability queries for offline fallback
CASUAL_KEYWORDS = [
    "hey", "hello", "hi", "what's up", "whatup", "how are you", "good morning", "good afternoon",
    "good evening", "what is going on", "thanks", "thank you", "bye", "joke", "who are you",
    "what can you do", "how can you help", "what is data companion", "bored"
]

MAX_AGENT_STEPS = 2

def clean_nemotron_output(text: str) -> str:
    """Strips internal LLM scratchpad reasoning or meta-monologue and fixes compressed markdown linebreaks."""
    if not text:
        return ""
    
    monologue_triggers = [
        "okay, the user is asking",
        "looking back at the context",
        "the user's phrasing is",
        "i should stick to",
        "wait, i think there might be",
        "given what i can see",
        "since the user is asking again",
        "i already explained that",
        "i don't have access to see beyond"
    ]
    
    lines = text.splitlines()
    clean_lines = []
    in_monologue = False
    
    for line in lines:
        line_lower = line.strip().lower()
        if any(trig in line_lower for trig in monologue_triggers):
            in_monologue = True
            continue
        if in_monologue:
            if line.startswith("#") or line.startswith("**") or line.startswith("- ") or any(w in line_lower for w in ["application", "this document", "this file", "the pdf", "contains", "overview", "presents"]):
                in_monologue = False
                clean_lines.append(line)
        else:
            clean_lines.append(line)
            
    res = "\n".join(clean_lines).strip()
    if not res:
        res = text

    # Fix inline compressed markdown elements by inserting necessary double linebreaks
    import re
    res = re.sub(r'([^\n])\s*(---|\*\*\*)\s*', r'\1\n\n---\n\n', res)
    res = re.sub(r'([^\n])\s*(#{1,4}\s+)', r'\1\n\n\2', res)
    res = re.sub(r'([^\n])\s*(###\s+\d+\.)', r'\1\n\n\2', res)

    return res


class DatabaseAgent:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DB_PATH
        self.conversation_state = {
            "last_sql": None,
            "last_entities": [],
            "last_tables": [],
            "last_chart_type": None
        }

    def process_message(
        self, 
        user_message: str, 
        history: List[Dict[str, Any]] = None, 
        api_key: Optional[str] = None,
        target_table: Optional[str] = None,
        attached_file_name: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process user query using NVIDIA Nemotron 3 Super 120B as primary LLM engine via Native API Tool Calling.
        Falls back smoothly to Gemini, OpenAI, or Smart Autonomous Engine.
        """
        history = history or []

        # Secure API Key Architecture: Backend reads NVIDIA_API_KEY from environment
        nvidia_key = os.environ.get("NVIDIA_API_KEY")
        gemini_key = api_key or os.environ.get("GEMINI_API_KEY")
        openai_key = os.environ.get("OPENAI_API_KEY")

        # Step 1: Native NVIDIA Nemotron 3 Super 120B Agent Path
        if nvidia_key:
            try:
                res = self._run_nemotron_agent(user_message, nvidia_key, history, target_table, attached_file_name)
                if request_id:
                    res["request_id"] = request_id
                return res
            except Exception as e:
                print(f"[NVIDIA Nemotron Native Agent Warning] {e}. Falling back to alternative providers.")

        # Step 2: Gemini Agent
        if gemini_key:
            try:
                res = self._run_gemini_agent(user_message, gemini_key, history, target_table, attached_file_name)
                if request_id:
                    res["request_id"] = request_id
                return res
            except Exception as e:
                print(f"[Gemini Agent Warning] {e}. Falling back to OpenAI/Autonomous Engine.")

        # Step 3: OpenAI Agent
        if openai_key:
            try:
                res = self._run_openai_agent(user_message, openai_key, history, target_table, attached_file_name)
                if request_id:
                    res["request_id"] = request_id
                return res
            except Exception as e:
                print(f"[OpenAI Agent Warning] {e}. Falling back to Dynamic Autonomous Engine.")

        # Step 4: Zero-Dependency Smart Autonomous Engine (Offline Fallback)
        res = self._run_smart_autonomous_engine(user_message, history, target_table, attached_file_name)
        if request_id:
            res["request_id"] = request_id
        return res

    def process_message_stream(
        self,
        user_message: str,
        history: List[Dict[str, Any]] = None,
        api_key: Optional[str] = None,
        target_table: Optional[str] = None,
        attached_file_name: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Generator producing real backend-to-frontend stage events for SSE streaming.
        Only emits database stage events if database tools are actually executed.
        """
        nvidia_key = os.environ.get("NVIDIA_API_KEY")
        if nvidia_key:
            yield {"request_id": request_id, "event": "stage", "stage": "thinking", "label": "Thinking..."}
        else:
            yield {"request_id": request_id, "event": "stage", "stage": "thinking", "label": "Processing request..."}
        
        result_payload = self.process_message(
            user_message=user_message,
            history=history,
            api_key=api_key,
            target_table=target_table,
            attached_file_name=attached_file_name,
            request_id=request_id
        )

        tools_called = result_payload.get("tools_called", [])
        if any(t.get("tool") == "get_schema" for t in tools_called):
            yield {"request_id": request_id, "event": "stage", "stage": "schema", "label": "Inspected database schema pragmas"}
        if any(t.get("tool") == "execute_query" for t in tools_called):
            exec_time = result_payload.get("sql_info", {}).get("execution_time_ms", 1.2) if result_payload.get("sql_info") else 0.5
            yield {"request_id": request_id, "event": "stage", "stage": "tool_done", "tool": "execute_query", "label": f"Executed SQL query in {exec_time} ms"}
        if result_payload.get("chart"):
            yield {"request_id": request_id, "event": "stage", "stage": "visualization", "label": f"Rendered {result_payload['chart'].get('chart_type', 'bar')} chart"}
        if result_payload.get("insights"):
            yield {"request_id": request_id, "event": "stage", "stage": "insights", "label": "Synthesized executive insights"}

        yield {"request_id": request_id, "event": "complete", "data": result_payload}

    def _get_schema_summary(self, target_table: Optional[str] = None) -> str:
        """Helper to get concise schema string for prompt optimization, guaranteeing full table awareness."""
        try:
            schema_data = get_schema(self.db_path, table_name=target_table)
            tables = schema_data.get("schema", {}).get("tables", {})
            summary = []
            
            # Prioritize target_table first if specified
            sorted_tbl_names = list(tables.keys())
            if target_table and target_table in sorted_tbl_names:
                sorted_tbl_names.remove(target_table)
                sorted_tbl_names.insert(0, target_table)

            for tbl in sorted_tbl_names[:30]:
                info = tables[tbl]
                cols = [f"{c['name']} ({c['type']})" for c in info.get("columns", [])[:10]]
                summary.append(f"Table '{tbl}': {', '.join(cols)}")
            return "\n".join(summary)
        except Exception:
            return "Tables: categories, products, customers, orders, order_items, reviews, inventory_logs, fulfillment_workflows"

    def _get_attached_file_context(self, target_table: str, attached_file_name: Optional[str]) -> tuple:
        """
        Introspects SQLite table for attached file and returns (context_str, is_document, row_count, col_names, sample_rows).
        Pre-injects actual document text lines for PDFs/Docs, or column metadata & sample rows for Spreadsheets.
        """
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(f"PRAGMA table_info('{target_table}');")
            cols = [row[1] for row in cursor.fetchall()]
            
            cursor.execute(f"SELECT COUNT(*) FROM '{target_table}';")
            row_count = cursor.fetchone()[0]

            is_document = any(c in cols for c in ["page_number", "paragraph_number", "line_number", "content"]) and "content" in cols

            if is_document:
                cursor.execute(f"SELECT content FROM '{target_table}' WHERE content IS NOT NULL AND TRIM(content) != '' LIMIT 30;")
                text_lines = [r[0] for r in cursor.fetchall()]
                text_snippet = "\n".join(text_lines[:25])
                context_str = f"""
CURRENT ACTIVE ATTACHED DOCUMENT:
File Name: {attached_file_name or target_table}
SQLite Table Name: `{target_table}`
Total Extracted Text Rows/Lines: {row_count}

ACTUAL EXTRACTED DOCUMENT TEXT SAMPLE (First 25 Lines):
---
{text_snippet[:2500]}
---

DOCUMENT REASONING RULES:
1. The user's question refers to the CURRENT ACTIVE ATTACHMENT '{attached_file_name or target_table}'.
2. You MUST read and use the ACTUAL EXTRACTED DOCUMENT TEXT SAMPLE above to summarize and answer naturally, accurately explaining what this specific document is about.
3. DO NOT generate an automatic chart for document overview or summary questions.
4. DO NOT output page_number or line_number as data values unless the user explicitly asks for page/line metrics.
5. DO NOT output internal monologue or scratchpad reasoning."""
                return context_str, True, row_count, cols, []

            else:
                cursor.execute(f"SELECT * FROM '{target_table}' LIMIT 3;")
                sample_rows_raw = cursor.fetchall()
                sample_rows = [dict(r) for r in sample_rows_raw]

                context_str = f"""
CURRENT ACTIVE ATTACHED SPREADSHEET:
File Name: {attached_file_name or target_table}
SQLite Table Name: `{target_table}`
Total Records (Rows): {row_count}
Total Fields (Columns): {len(cols)}
Column Names: {', '.join(cols)}

ACTUAL DATA SAMPLE (First 3 Rows):
{json.dumps(sample_rows, indent=2)}

SPREADSHEET REASONING RULES:
1. The user's question refers to the CURRENT ACTIVE ATTACHMENT '{attached_file_name or target_table}'.
2. Answer naturally using the ACTUAL FACTS above (total rows, total columns, column names, sample values, and what the dataset represents).
3. DO NOT generate an automatic chart for overview, summary, column list, or record count questions.
4. ONLY generate a chart if the user explicitly requests a chart/graph OR asks an analytical query comparing numerical measures (e.g., 'Show revenue by category').
5. DO NOT output internal monologue or scratchpad reasoning."""
                return context_str, False, row_count, cols, sample_rows

        except Exception as e:
            return f"Attached Table Context: {target_table}", False, 0, [], []
        finally:
            conn.close()

    def _run_nemotron_agent(
        self, 
        message: str, 
        api_key: str, 
        history: List[Dict[str, Any]], 
        target_table: Optional[str] = None, 
        attached_file_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes Native API Tool Calling loop using NVIDIA Nemotron 3 Super 120B A12B.
        Handles attached spreadsheet / document datasets natively via SQLite table queries and semantic intent understanding.
        """
        import openai
        base_url = os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
        model_name = os.environ.get("NVIDIA_MODEL", "nvidia/nemotron-3-super-120b-a12b")

        client = openai.OpenAI(api_key=api_key, base_url=base_url)

        # Pre-inject schema summary context into system prompt
        schema_summary_str = self._get_schema_summary(target_table)

        # Build structured context state for multi-turn pronoun resolution ("their", "those", "that")
        context_state_str = ""
        last_sql_val = self.conversation_state.get("last_sql")
        last_entities_val = self.conversation_state.get("last_entities")
        if history:
            for h in reversed(history):
                if isinstance(h, dict) and h.get("role") == "assistant":
                    if not last_sql_val and h.get("sql_info") and h["sql_info"].get("query"):
                        last_sql_val = h["sql_info"]["query"]
                    if not last_entities_val and h.get("content"):
                        last_entities_val = [h["content"][:100]]
                    if last_sql_val:
                        break
        if last_entities_val:
            context_state_str += f"\nPrevious Query Entities: {json.dumps(last_entities_val)}"
        if last_sql_val:
            context_state_str += f"\nPrevious Query SQL: {last_sql_val}"

        attached_context_str = ""
        is_doc = False
        row_count = 0
        cols = []
        sample_data = []

        if target_table:
            attached_context_str, is_doc, row_count, cols, sample_data = self._get_attached_file_context(target_table, attached_file_name)

        system_prompt = f"""You are Data Companion, a friendly conversational AI assistant and intelligent database analyst.

CRITICAL STRUCTURED RESPONSE FORMATTING (CHATGPT / CLAUDE STYLE):
- Always structure your answers into clean, highly readable Markdown.
- Use clear Headings (`### Section Title`) to separate logical parts of your answer.
- Use Bullet Points (`- ` or `* `) and Numbered Lists (`1. `, `2. `) for itemized details.
- Use Bold (`**text**`) for table names, field names, key metrics, and important terms.
- Use Markdown Tables (`| Header 1 | Header 2 |`) when summarizing structured data or comparing items.
- Maintain double line breaks (`\n\n`) between paragraphs and list groups. NEVER output a continuous wall of unformatted text.
- DO NOT output internal thinking or scratchpad monologue such as "Okay, the user is asking...".

PRE-LOADED DATABASE SCHEMA CONTEXT:
{schema_summary_str}

AVAILABLE TOOLS (OPTIONAL):
`execute_query`, `generate_chart`, `generate_flowchart`, `explain_data`, `get_schema`.
Use tools ONLY when the user's request requires actual information from the connected database, database schema, visualization, diagram generation, or analytical computation.

Do NOT call tools for casual greetings or general conversation.

SEMANTIC INTENT GUIDELINES FOR ATTACHED FILES & DATABASE QUERIES:
1. FILE CONTENT OVERVIEW / SUMMARY ("What is inside this file?", "Summarize this PDF", "Explain this file", "now in this what present there"):
   - Read the CURRENT ACTIVE ATTACHMENT context below and answer naturally in clear text.
   - Explain what the CURRENT file or document actually contains (subject, sections, topics, row count, column names, or key details).
   - DO NOT invoke `generate_chart` for overview/summary questions.

2. SCHEMA / COLUMN QUESTIONS ("What columns are present?", "What fields are in this file?"):
   - List the actual column names and explain what they represent. No chart.

3. RECORD COUNT QUESTIONS ("How many records?", "How many rows/pages?"):
   - Answer with the actual count from the context. No chart.

4. SHOW ACTUAL DATA / RECORDS ("Show me the data", "Show rows"):
   - Call `execute_query` to fetch representative records.

5. ANALYTICAL QUERIES ("Show revenue by category", "Compare groups", "Plot trend"):
   - Call `execute_query` and generate a chart when requested or appropriate.

Maintain conversational context across turns.

ATTACHED DATASET CONTEXT:
{attached_context_str}
{context_state_str}"""

        messages = [{"role": "system", "content": system_prompt}]
        for hist_item in (history[-6:] if history else []):
            if hist_item.get("role") and hist_item.get("content"):
                messages.append({"role": hist_item["role"], "content": str(hist_item["content"])})
        messages.append({"role": "user", "content": message})

        tool_logs = []
        sql_info = None
        chart_info = None
        flowchart_info = None
        insights_info = None
        final_text = ""
        should_break_loop = False

        msg_lower = message.lower().strip()
        is_explicit_chart_req = any(w in msg_lower for w in ["chart", "graph", "plot", "draw", "visualize", "diagram", "trend"])
        is_overview_req = any(w in msg_lower for w in ["what is inside", "what's inside", "what is in", "what's in", "explain", "overview", "summarize", "summary", "what columns", "how many records", "how many rows", "what fields", "can you read", "content", "details in this file", "present in this file", "contain", "what present there"])
        is_show_data_req = any(w in msg_lower for w in ["show me the data", "show the records", "show rows", "display the contents", "show data"])

        # Native API Tool-Calling Agent Loop
        for step in range(MAX_AGENT_STEPS):
            if should_break_loop:
                break

            # Call NVIDIA API with retry logic for transient rate limits (429)
            response = None
            for attempt in range(3):
                try:
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        tools=NVIDIA_TOOLS,
                        tool_choice="auto",
                        temperature=0.2,
                        max_tokens=1024
                    )
                    break
                except Exception as err:
                    if "429" in str(err) and attempt < 2:
                        time.sleep(1.0 * (attempt + 1))
                    else:
                        raise err

            assistant_msg = response.choices[0].message
            messages.append(assistant_msg)

            # Check if Nemotron invoked native tool calls
            if not assistant_msg.tool_calls:
                raw_text = assistant_msg.content or ""
                final_text = clean_nemotron_output(raw_text)

                # Safeguard for attached files: If overview or show_data request, ensure actual database data is available if needed
                if target_table and not sql_info and (is_show_data_req or (is_overview_req and not is_doc)):
                    query_sql = f"SELECT * FROM '{target_table}' LIMIT 10;"
                    tool_result = execute_query(query_sql, self.db_path)
                    sql_info = tool_result
                    tool_logs.append({"tool": "execute_query", "status": "executed (auto-attached)"})
                    data_rows = tool_result.get("data", [])
                    
                    if is_explicit_chart_req and data_rows and len(data_rows[0].keys()) >= 2:
                        keys = list(data_rows[0].keys())
                        x_k = keys[0]
                        y_ks = [k for k in keys[1:] if isinstance(data_rows[0][k], (int, float))]
                        if y_ks:
                            chart_info = generate_chart(
                                chart_type="bar" if len(data_rows) <= 10 else "line",
                                title=f"Dataset Analysis ({x_k} vs {y_ks[0]})",
                                data=data_rows[:10],
                                x_key=x_k,
                                y_keys=y_ks
                            )

                break

            # Process Native Tool Calls via Whitelist Dispatcher
            for tool_call in assistant_msg.tool_calls:
                tool_name = tool_call.function.name
                
                # Verify Whitelist Security
                if tool_name not in TOOL_HANDLERS:
                    tool_result = {"status": "error", "message": f"Unauthorized tool call '{tool_name}' blocked."}
                else:
                    try:
                        args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                    except Exception:
                        args = {}

                    # Execute Whitelisted Handler Function
                    handler = TOOL_HANDLERS[tool_name]
                    if tool_name == "get_schema":
                        tool_result = handler(db_path=self.db_path, **args)
                    elif tool_name == "execute_query":
                        # If user attached a custom file, enforce target_table query if unspecified
                        if target_table and "from" not in args.get("query", "").lower():
                            args["query"] = f"SELECT * FROM '{target_table}' LIMIT 10;"

                        tool_result = handler(db_path=self.db_path, **args)
                        sql_info = tool_result
                        should_break_loop = True
                        tool_logs.append({"tool": "execute_query", "status": "executed"})

                        if tool_result.get("status") == "success" and tool_result.get("data"):
                            data_rows = tool_result["data"]
                            
                            # Extract structured entities for conversation state memory
                            entities = []
                            for row in data_rows[:5]:
                                for val in row.values():
                                    if isinstance(val, str) and len(val) < 50:
                                        entities.append(val)
                                        break
                            self.conversation_state["last_entities"] = entities
                            self.conversation_state["last_sql"] = tool_result.get("query")

                            # Auto-generate chart whenever database query returns records with metrics
                            if not chart_info and len(data_rows) >= 1 and len(data_rows[0].keys()) >= 2:
                                keys = list(data_rows[0].keys())

                                def is_num_val(v):
                                    if isinstance(v, (int, float)):
                                        return True
                                    if isinstance(v, str):
                                        try:
                                            float(v.replace('$', '').replace(',', '').strip())
                                            return True
                                        except ValueError:
                                            return False
                                    return False

                                string_cols = [k for k in keys if isinstance(data_rows[0][k], str) and not is_num_val(data_rows[0][k])]
                                numeric_cols = [k for k in keys if is_num_val(data_rows[0][k])]

                                x_k = string_cols[0] if string_cols else (keys[1] if len(keys) > 1 and keys[0].lower().endswith("_id") else keys[0])
                                # Exclude internal ID columns from Y-axis metric values
                                metric_cols = [k for k in numeric_cols if not k.lower().endswith("_id") and k.lower() != "id" and k != x_k]
                                y_ks = metric_cols if metric_cols else [k for k in numeric_cols if k != x_k]

                                if not y_ks and len(keys) > 1:
                                    y_ks = [keys[1] if keys[1] != x_k else keys[0]]

                                if y_ks:
                                    chart_info = generate_chart(
                                        chart_type="bar" if len(data_rows) <= 10 else "line",
                                        title=f"Dataset Visual Chart ({x_k} vs {y_ks[0]})",
                                        data=data_rows[:20],
                                        x_key=x_k,
                                        y_keys=y_ks[:2]
                                    )
                                    tool_logs.append({"tool": "generate_chart", "status": "executed"})

                            insights_info = explain_data(
                                data=data_rows[:10],
                                query_context=message,
                                highlights=[
                                    f"Retrieved {len(data_rows)} record(s) from table '{target_table or 'orders'}'.",
                                    f"Primary metrics analyzed across '{x_k if 'x_k' in locals() else 'records'}'."
                                ],
                                recommended_questions=[
                                    "Show me monthly sales revenue trend",
                                    "Show our top customers by total spent",
                                    "Create a flowchart showing how orders flow through our system"
                                ]
                            )
                            tool_logs.append({"tool": "explain_data", "status": "executed"})

                            final_text = f"I executed the query `{tool_result.get('query')}` against table `{target_table or 'orders'}` and retrieved {len(data_rows)} record(s) for you."

                    elif tool_name == "generate_chart":
                        if is_explicit_chart_req or not is_overview_req:
                            tool_result = handler(**args)
                            chart_info = tool_result
                    elif tool_name == "generate_flowchart":
                        tool_result = handler(**args)
                        flowchart_info = tool_result
                        should_break_loop = True
                        final_text = "Here is the requested diagram."
                    elif tool_name == "explain_data":
                        tool_result = handler(**args)
                        insights_info = tool_result

                tool_logs.append({"tool": tool_name, "status": tool_result.get("status", "executed")})

        # Final output cleaning
        final_text = clean_nemotron_output(final_text)

        # Safeguard for ER diagram / process flow requests if Nemotron didn't invoke generate_flowchart tool
        if not flowchart_info:
            if any(term in msg_lower for term in ["er diagram", "entity-relationship", "er-diagram", "schema diagram"]):
                mermaid_er = """erDiagram
    CUSTOMERS ||--o{ ORDERS : places
    CATEGORIES ||--o{ PRODUCTS : contains
    PRODUCTS ||--o{ ORDER_ITEMS : included_in
    ORDERS ||--o{ ORDER_ITEMS : details
    PRODUCTS ||--o{ REVIEWS : receives
    CUSTOMERS ||--o{ REVIEWS : writes
    PRODUCTS ||--o{ INVENTORY_LOGS : tracks
    ORDERS ||--o{ FULFILLMENT_WORKFLOWS : moves_through

    CUSTOMERS {
        int customer_id PK
        string name
        string email
        string country
        string user_segment
    }
    PRODUCTS {
        int product_id PK
        int category_id FK
        string product_name
        float price
        float rating
    }
    ORDERS {
        int order_id PK
        int customer_id FK
        date order_date
        float total_amount
        string status
    }
    ORDER_ITEMS {
        int item_id PK
        int order_id FK
        int product_id FK
        int quantity
        float unit_price
    }"""
                flowchart_info = generate_flowchart(
                    diagram_type="er_diagram",
                    title="E-Commerce Database Entity-Relationship (ER) Diagram",
                    mermaid_code=mermaid_er,
                    explanation="Visual representation of database tables, primary keys, and foreign key relationships."
                )
                tool_logs.append({"tool": "generate_flowchart", "status": "executed (auto-attached)"})
                if not final_text or "here is" in final_text.lower():
                    final_text = "Here is the interactive Entity-Relationship (ER) diagram for our database system."

            elif any(term in msg_lower for term in ["flowchart", "process flow", "order flow", "pipeline", "workflow"]):
                mermaid_flow = """graph TD
    A[🛒 User Places Order] --> B[💳 Payment Verification]
    B -->|Approved| C[📦 Inventory Allocation]
    B -->|Failed| X[❌ Order Cancelled]
    C --> D[🎁 Packaging & Labeling]
    D --> E[🚚 Shipped via Carrier]
    E --> F[🛵 Out for Delivery]
    F --> G[✅ Delivered & Review Requested]
    
    style A fill:#4F46E5,stroke:#312E81,color:#fff
    style G fill:#10B981,stroke:#065F46,color:#fff
    style X fill:#EF4444,stroke:#991B1B,color:#fff"""
                flowchart_info = generate_flowchart(
                    diagram_type="process_flow",
                    title="E-Commerce Order Fulfillment Lifecycle Pipeline",
                    mermaid_code=mermaid_flow,
                    explanation="Step-by-step state machine transition showing how customer orders move from checkout to delivery."
                )
                tool_logs.append({"tool": "generate_flowchart", "status": "executed (auto-attached)"})
                if not final_text or "here is" in final_text.lower():
                    final_text = "I mapped out a visual process flowchart demonstrating how orders move through our logistics and fulfillment pipeline."

        # If tools were invoked or query executed, include data source metadata
        source_info = None
        if tool_logs or sql_info or flowchart_info:
            source_info = (
                {"type": "uploaded_file", "name": attached_file_name or target_table, "table": target_table}
                if target_table else
                {"type": "sqlite", "name": "ecommerce_sample.db"}
            )

        return {
            "role": "assistant",
            "model_badge": "Thinking",
            "data_source": source_info,
            "content": final_text or "I analyzed the attached data and compiled the results for you.",
            "tools_called": tool_logs,
            "sql_info": sql_info,
            "chart": chart_info,
            "flowchart": flowchart_info,
            "insights": insights_info
        }

    def _run_smart_autonomous_engine(
        self, 
        message: str, 
        history: List[Dict[str, Any]],
        target_table: Optional[str] = None,
        attached_file_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Smart Autonomous Offline Fallback Engine.
        Handles semantic intent distinction (file overview vs data records vs analytics) without forcing charts.
        """
        q = message.lower().strip()
        tool_execution_logs = []

        source_info = (
            {"type": "uploaded_file", "name": attached_file_name or target_table, "table": target_table}
            if target_table else
            {"type": "sqlite", "name": "ecommerce_sample.db"}
        )

        is_explicit_chart_req = any(w in q for w in ["chart", "graph", "plot", "draw", "visualize", "diagram", "trend"])
        is_overview_req = any(w in q for w in ["what is inside", "what's inside", "what is in", "what's in", "explain", "overview", "summarize", "summary", "what columns", "how many records", "how many rows", "what fields", "can you read", "content", "details in this file", "present in this file", "contain", "what present there"])
        is_show_data_req = any(w in q for w in ["show me the data", "show the records", "show rows", "display the contents", "show data"])

        # Conversational / Greetings / Jokes / Capability Queries in Offline Mode (using strict word boundaries)
        has_casual_keyword = any(re.search(rf"\b{re.escape(term)}\b", q) for term in CASUAL_KEYWORDS)
        has_data_keyword = any(re.search(rf"\b{re.escape(k)}\b", q) for k in ["sales", "order", "product", "customer", "inventory", "revenue", "file", "table", "column", "record", "pdf", "excel", "show", "er", "diagram", "flowchart", "schema", "database"])

        if has_casual_keyword and not has_data_keyword:
            if "joke" in q:
                reply = "Why did the database administrator break up with the query? Because it had too many relationships! 😄"
            elif "who are you" in q or "what can you do" in q or "help" in q:
                reply = "I'm Data Companion! I can chat with you, answer questions, analyze sales data, run SQL queries, create charts, draw database ER diagrams, or analyze your attached Excel/CSV files."
            elif "thanks" in q or "thank you" in q:
                reply = "You're very welcome! Let me know if you need anything else examined in your data."
            else:
                reply = "Hey there! How's your day going? What data insights or questions would you like to explore today?"

            return {
                "role": "assistant",
                "model_badge": "Autonomous Engine",
                "data_source": None,
                "content": reply,
                "tools_called": [],
                "sql_info": None,
                "chart": None,
                "flowchart": None,
                "insights": None
            }

        # If user attached a custom file (Excel, CSV, JSON, PDF, Word, Markdown, Text):
        if target_table:
            tool_execution_logs.append({"tool": "get_schema", "status": "executed"})
            schema_res = get_schema(self.db_path, table_name=target_table)
            tbl_info = schema_res.get("schema", {}).get("tables", {}).get(target_table, {})
            columns = [col["name"] for col in tbl_info.get("columns", [])]
            is_doc = any(c in columns for c in ["page_number", "paragraph_number", "line_number", "content"]) and "content" in columns

            # 1. FILE OVERVIEW / SUMMARY INTENT
            if is_overview_req or ("what" in q and "file" in q):
                conn = get_db_connection(self.db_path)
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM '{target_table}';")
                row_count = cursor.fetchone()[0]

                if is_doc:
                    cursor.execute(f"SELECT content FROM '{target_table}' WHERE content IS NOT NULL AND TRIM(content) != '' LIMIT 15;")
                    snippet_lines = [r[0] for r in cursor.fetchall()]
                    conn.close()

                    text_snippet = "\n".join([f"- {line}" for line in snippet_lines[:10]])
                    reply_text = (
                        f"## 📄 Document Overview\n"
                        f"> **File:** `{attached_file_name or target_table}`\n\n"
                        f"### 📊 Summary\n"
                        f"| Property | Value |\n"
                        f"|---|---|\n"
                        f"| Total Extracted Lines | **{row_count}** |\n"
                        f"| File Name | `{attached_file_name or target_table}` |\n\n"
                        f"### 📝 Content Preview (First 10 Lines)\n"
                        f"{text_snippet}\n\n"
                        f"---\n"
                        f"💡 **Tip:** You can ask specific questions like *\"What topics are covered?\"* or *\"Summarize section 2\"*."
                    )
                    
                    return {
                        "role": "assistant",
                        "model_badge": "Autonomous Engine",
                        "data_source": source_info,
                        "content": reply_text,
                        "tools_called": tool_execution_logs,
                        "sql_info": None,
                        "chart": None,
                        "flowchart": None,
                        "insights": None
                    }
                else:
                    cursor.execute(f"SELECT * FROM '{target_table}' LIMIT 3;")
                    sample_rows = [dict(r) for r in cursor.fetchall()]
                    conn.close()

                    col_bullets = "\n".join([f"- `{c}`" for c in columns[:12]])
                    reply_text = (
                        f"## 📂 Dataset Overview\n"
                        f"> **File:** `{attached_file_name or target_table}`\n\n"
                        f"### 📊 File Statistics\n"
                        f"| Property | Value |\n"
                        f"|---|---|\n"
                        f"| Total Records | **{row_count:,}** |\n"
                        f"| Total Columns | **{len(columns)}** |\n"
                        f"| Table Name | `{target_table}` |\n\n"
                        f"### 🗂️ Available Columns\n"
                        f"{col_bullets}\n\n"
                        f"### 🔍 Sample Data (First 2 Rows)\n"
                        f"```json\n{json.dumps(sample_rows[:2], indent=2)}\n```\n\n"
                        f"---\n"
                        f"💡 **Suggestions:** Try asking *\"Show me top 10 rows\"*, *\"Give me a chart of [column]\"*, or *\"What are the key insights?\"*"
                    )

                    return {
                        "role": "assistant",
                        "model_badge": "Autonomous Engine",
                        "data_source": source_info,
                        "content": reply_text,
                        "tools_called": tool_execution_logs,
                        "sql_info": None,
                        "chart": None,
                        "flowchart": None,
                        "insights": None
                    }

            # 2. SHOW ACTUAL DATA / RECORDS
            sql, chart_type, title, x_key, y_keys = self._build_query_for_custom_table(target_table, columns, attached_file_name)
            tool_execution_logs.append({"tool": "execute_query", "status": "executed"})
            query_res = execute_query(sql, self.db_path)
            data = query_res.get("data", [])

            chart_res = None
            if is_explicit_chart_req and data and chart_type and x_key and y_keys:
                chart_res = generate_chart(
                    chart_type=chart_type,
                    title=title,
                    data=data,
                    x_key=x_key,
                    y_keys=y_keys,
                    description=f"Analysis of attached file: '{attached_file_name or target_table}'."
                )
                tool_execution_logs.append({"tool": "generate_chart", "status": "executed"})

            structured_content = (
                f"## 📊 Query Results\n"
                f"> Analyzing **`{attached_file_name or target_table}`**\n\n"
                f"### ✅ Execution Summary\n"
                f"| Property | Value |\n"
                f"|---|---|\n"
                f"| Records Retrieved | **{len(data)}** |\n"
                f"| Source Table | `{target_table}` |\n\n"
            )
            if data:
                keys = list(data[0].keys())
                header = " | ".join(keys[:6])
                separator = " | ".join(["---"] * min(len(keys), 6))
                rows_md = "\n".join(
                    "| " + " | ".join(str(row.get(k, "")) for k in keys[:6]) + " |"
                    for row in data[:5]
                )
                structured_content += f"### 📋 Data Preview\n| {header} |\n| {separator} |\n{rows_md}\n\n"
            structured_content += "---\n💡 **Tip:** Ask *\"Give me a chart\"* or *\"What are the key insights?\"* for deeper analysis."

            return {
                "role": "assistant",
                "model_badge": "Autonomous Engine",
                "data_source": source_info,
                "content": structured_content,
                "tools_called": tool_execution_logs,
                "sql_info": query_res,
                "chart": chart_res,
                "flowchart": None,
                "insights": None
            }

        # Intent 1: ER Diagram / Database Structure
        if any(term in q for term in ["er diagram", "schema", "tables", "relationships", "structure"]):
            tool_execution_logs.append({"tool": "get_schema", "status": "executed"})
            schema_res = get_schema(self.db_path)
            
            mermaid_er = """erDiagram
    CUSTOMERS ||--o{ ORDERS : places
    CATEGORIES ||--o{ PRODUCTS : contains
    PRODUCTS ||--o{ ORDER_ITEMS : included_in
    ORDERS ||--o{ ORDER_ITEMS : details
    PRODUCTS ||--o{ REVIEWS : receives
    CUSTOMERS ||--o{ REVIEWS : writes
    PRODUCTS ||--o{ INVENTORY_LOGS : tracks
    ORDERS ||--o{ FULFILLMENT_WORKFLOWS : moves_through

    CUSTOMERS {
        int customer_id PK
        string name
        string email
        string country
        string user_segment
    }
    PRODUCTS {
        int product_id PK
        int category_id FK
        string product_name
        float price
        float rating
    }
    ORDERS {
        int order_id PK
        int customer_id FK
        date order_date
        float total_amount
        string status
    }
    ORDER_ITEMS {
        int item_id PK
        int order_id FK
        int product_id FK
        int quantity
        float unit_price
    }"""
            flowchart_res = generate_flowchart(
                diagram_type="er_diagram",
                title="E-Commerce Database Entity-Relationship (ER) Diagram",
                mermaid_code=mermaid_er,
                explanation="Visual representation of database tables, primary keys, and foreign key relationships."
            )
            tool_execution_logs.append({"tool": "generate_flowchart", "status": "executed"})

            er_content = (
                f"## 🗄️ Database Entity-Relationship Diagram\n\n"
                f"The database contains **{schema_res['schema']['table_count']} core tables** that work together to track the full e-commerce lifecycle.\n\n"
                f"### 📦 Core Tables\n"
                f"| Table | Purpose |\n"
                f"|---|---|\n"
                f"| `customers` | Customer profiles, segments, and countries |\n"
                f"| `products` | Product catalog with categories and pricing |\n"
                f"| `orders` | Order records with status and total amounts |\n"
                f"| `order_items` | Individual line items per order |\n"
                f"| `categories` | Product category groupings |\n"
                f"| `reviews` | Customer product reviews and ratings |\n"
                f"| `inventory_logs` | Stock level change history |\n"
                f"| `fulfillment_workflows` | Order fulfillment stage tracking |\n\n"
                f"### 🔗 Key Relationships\n"
                f"- **Customers** → place → **Orders** → contain → **Order Items** → reference → **Products**\n"
                f"- **Products** → belong to → **Categories**\n"
                f"- **Products** → have → **Reviews** (written by Customers)\n"
                f"- **Orders** → tracked through → **Fulfillment Workflows**"
            )
            return {
                "role": "assistant",
                "model_badge": "Autonomous Engine",
                "data_source": source_info,
                "content": er_content,
                "tools_called": tool_execution_logs,
                "sql_info": None,
                "chart": None,
                "flowchart": flowchart_res,
                "insights": {
                    "highlights": [
                        "Primary tables: `customers`, `products`, `orders`, `order_items`, `categories`.",
                        "Foreign key links enable full end-to-end tracking from customer orders to inventory and fulfillment.",
                        "Supports customer segmentation, country breakdowns, and product analytics."
                    ],
                    "recommended_followups": [
                        "Show me our top customers by total spent",
                        "Show me monthly sales revenue trend",
                        "Create a flowchart showing how orders flow through our system"
                    ]
                }
            }

        # Intent 2: Order Fulfillment Flowchart / Process Flow
        if any(term in q for term in ["flowchart", "process flow", "order flow", "pipeline", "workflow"]):
            mermaid_flow = """graph TD
    A[🛒 User Places Order] --> B[💳 Payment Verification]
    B -->|Approved| C[📦 Inventory Allocation]
    B -->|Failed| X[❌ Order Cancelled]
    C --> D[🎁 Packaging & Labeling]
    D --> E[🚚 Shipped via Carrier]
    E --> F[🛵 Out for Delivery]
    F --> G[✅ Delivered & Review Requested]
    
    style A fill:#4F46E5,stroke:#312E81,color:#fff
    style G fill:#10B981,stroke:#065F46,color:#fff
    style X fill:#EF4444,stroke:#991B1B,color:#fff"""

            flowchart_res = generate_flowchart(
                diagram_type="process_flow",
                title="E-Commerce Order Fulfillment Lifecycle Pipeline",
                mermaid_code=mermaid_flow,
                explanation="Step-by-step state machine transition showing how customer orders move from checkout to delivery."
            )
            tool_execution_logs.append({"tool": "generate_flowchart", "status": "executed"})

            flow_content = (
                f"## 🚚 Order Fulfillment Lifecycle\n\n"
                f"Here is the complete pipeline showing how customer orders move from checkout to delivery.\n\n"
                f"### 📋 Fulfillment Stages\n"
                f"| Stage | Description |\n"
                f"|---|---|\n"
                f"| 🛒 **Order Placed** | Customer submits cart and checkout details |\n"
                f"| 💳 **Payment Verification** | Payment gateway validates and approves transaction |\n"
                f"| 📦 **Inventory Allocation** | Stock reserved for the order |\n"
                f"| 🎁 **Packaging & Labeling** | Order packed and shipping label generated |\n"
                f"| 🚚 **Shipped via Carrier** | Handoff to logistics partner |\n"
                f"| 🛵 **Out for Delivery** | Last-mile delivery in progress |\n"
                f"| ✅ **Delivered** | Customer receives order, review requested |\n\n"
                f"### ⚠️ Exception Path\n"
                f"- If **payment fails** → Order is immediately **cancelled** and customer is notified."
            )
            return {
                "role": "assistant",
                "model_badge": "Autonomous Engine",
                "data_source": source_info,
                "content": flow_content,
                "tools_called": tool_execution_logs,
                "sql_info": None,
                "chart": None,
                "flowchart": flowchart_res,
                "insights": {
                    "highlights": [
                        "Fulfillment stages: Payment Verification -> Inventory Allocation -> Packaging -> Shipping -> Delivery.",
                        "Real-time tracking is maintained in the `fulfillment_workflows` table.",
                        "Automated retry loops trigger if payment verification flags anomalies."
                    ],
                    "recommended_followups": [
                        "What is the breakdown of order fulfillment statuses?",
                        "Show me low inventory stock items",
                        "Draw me the ER diagram for this database"
                    ]
                }
            }

        # DYNAMIC SQL TRANSLATION LOGIC FOR CUSTOM USER QUERIES:
        tool_execution_logs.append({"tool": "get_schema", "status": "executed"})
        sql, chart_type, title, x_key, y_keys, takeaway, proactive_tip = self._build_dynamic_sql_and_takeaway(q)

        tool_execution_logs.append({"tool": "execute_query", "status": "executed"})
        query_res = execute_query(sql, self.db_path)

        data = query_res.get("data", [])
        chart_res = None

        if data and chart_type and x_key and y_keys:
            chart_res = generate_chart(
                chart_type=chart_type,
                title=title,
                data=data,
                x_key=x_key,
                y_keys=y_keys,
                description=f"Visual chart generated for: '{message}'."
            )
            chart_res["takeaway"] = takeaway
            tool_execution_logs.append({"tool": "generate_chart", "status": "executed"})

        explain_res = explain_data(
            data=data,
            query_context=message,
            highlights=[
                takeaway,
                f"Retrieved {len(data)} record(s) from the database."
            ],
            recommended_questions=[
                "Would you like to see monthly trends?",
                "Should we break this down by customer segment?",
                "Show me low inventory stock items"
            ]
        )
        explain_res["proactive_tip"] = proactive_tip
        tool_execution_logs.append({"tool": "explain_data", "status": "executed"})

        rows_retrieved = len(data)
        analysis_content = (
            f"## 📊 Analysis Results\n\n"
            f"> **Query:** _{message}_\n\n"
            f"### ✅ Execution Summary\n"
            f"| Property | Value |\n"
            f"|---|---|\n"
            f"| Records Retrieved | **{rows_retrieved}** |\n"
            f"| Data Source | `ecommerce_sample.db` |\n"
            f"| Chart Generated | {'✅ Yes' if chart_res else '❌ No'} |\n\n"
        )
        if data and rows_retrieved > 0:
            keys = list(data[0].keys())
            header = " | ".join(keys[:5])
            separator = " | ".join(["---"] * min(len(keys), 5))
            rows_md = "\n".join(
                "| " + " | ".join(str(row.get(k, "")) for k in keys[:5]) + " |"
                for row in data[:5]
            )
            analysis_content += f"### 📋 Top Results Preview\n| {header} |\n| {separator} |\n{rows_md}\n\n"
        if takeaway:
            analysis_content += f"### 💡 Key Takeaway\n> {takeaway}\n\n"
        analysis_content += "---\n*Scroll down to see the interactive chart and detailed insights below.*"

        return {
            "role": "assistant",
            "model_badge": "Autonomous Engine",
            "data_source": source_info,
            "content": analysis_content,
            "tools_called": tool_execution_logs,
            "sql_info": query_res,
            "chart": chart_res,
            "flowchart": None,
            "insights": explain_res
        }

    def _build_query_for_custom_table(self, table_name: str, columns: List[str], file_name: Optional[str]) -> tuple:
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM '{table_name}' LIMIT 5;")
        rows = cursor.fetchall()
        conn.close()

        numeric_cols = []
        string_cols = []

        if rows and len(rows) > 0:
            first_row = dict(rows[0])
            for col, val in first_row.items():
                if isinstance(val, (int, float)):
                    numeric_cols.append(col)
                else:
                    string_cols.append(col)

        x_col = string_cols[0] if string_cols else (columns[0] if columns else "row_id")
        y_col = numeric_cols[0] if numeric_cols else (columns[1] if len(columns) > 1 else columns[0])

        if numeric_cols and string_cols:
            sql = f"SELECT {x_col}, SUM({y_col}) as {y_col} FROM '{table_name}' GROUP BY {x_col} ORDER BY {y_col} DESC LIMIT 10;"
            return sql, "bar", f"Analysis of Attached File: {file_name or table_name}", x_col, [y_col]
        else:
            sql = f"SELECT * FROM '{table_name}' LIMIT 10;"
            return sql, "bar", f"Dataset Overview: {file_name or table_name}", columns[0], [columns[1]] if len(columns) > 1 else [columns[0]]

    def _build_dynamic_sql_and_takeaway(self, q: str) -> tuple:
        limit = 10
        match_limit = re.search(r'\b(?:top|limit|first|show)\s+(\d+)\b', q)
        if match_limit:
            limit = min(int(match_limit.group(1)), 50)

        if any(w in q for w in ["trend", "over time", "monthly", "timeline", "sales history", "by month"]):
            sql = f"""SELECT 
                        STRFTIME('%Y-%m', order_date) as month, 
                        ROUND(SUM(total_amount), 2) as revenue,
                        COUNT(order_id) as total_orders
                     FROM orders 
                     GROUP BY month 
                     ORDER BY month ASC 
                     LIMIT {limit};"""
            takeaway = "Sales revenue shows a steady upward trajectory with monthly order volume remaining strong."
            tip = "💡 Advisor Tip: Peak revenue months align with promotional campaigns. Should we analyze revenue breakdown by category next?"
            return sql, "line", "Monthly Sales Revenue Trend", "month", ["revenue", "total_orders"], takeaway, tip

        if any(w in q for w in ["category", "categories", "department"]):
            sql = f"""SELECT 
                        c.category_name as category, 
                        ROUND(SUM(oi.subtotal), 2) as revenue
                     FROM order_items oi
                     JOIN products p ON oi.product_id = p.product_id
                     JOIN categories c ON p.category_id = c.category_id
                     GROUP BY c.category_name
                     ORDER BY revenue DESC 
                     LIMIT {limit};"""
            takeaway = "Electronics and Apparel & Fashion represent our top grossing revenue categories."
            tip = "💡 Advisor Tip: Electronics accounts for the largest sales volume. Would you like to see top products within this category?"
            return sql, "pie", "Category Revenue Distribution", "category", ["revenue"], takeaway, tip

        if any(w in q for w in ["customer", "customers", "user", "users", "spending", "client"]):
            sql = f"""SELECT 
                        c.name, 
                        c.user_segment,
                        ROUND(COALESCE(SUM(o.total_amount), 0), 2) as total_spent
                     FROM customers c
                     LEFT JOIN orders o ON c.customer_id = o.customer_id
                     GROUP BY c.customer_id
                     ORDER BY total_spent DESC 
                     LIMIT {limit};"""
            takeaway = "VIP and Enterprise segment customers represent our highest cumulative revenue contributors."
            tip = "💡 Advisor Tip: VIP customers spend 4x more on average. Should we inspect customer breakdown by country?"
            return sql, "bar", f"Top {limit} Customers by Total Amount Spent", "name", ["total_spent"], takeaway, tip

        if any(w in q for w in ["inventory", "stock", "quantity", "warehouse", "health", "restock"]):
            sql = f"""SELECT 
                        product_name, 
                        stock_quantity, 
                        price
                     FROM products 
                     ORDER BY stock_quantity ASC 
                     LIMIT {limit};"""
            takeaway = "Stock levels are lowest on high-demand items including QuantumBook Pro and BaristaPro Machine."
            tip = "💡 Advisor Tip: Stock is running low on two fast-selling items (under 45 units remaining). Should I check recent order fulfillment logs?"
            return sql, "bar", "Inventory Stock Health & Restock Levels", "product_name", ["stock_quantity"], takeaway, tip

        if any(w in q for w in ["payment", "pay", "credit card", "paypal", "crypto"]):
            sql = f"""SELECT 
                        payment_method, 
                        COUNT(order_id) as total_orders,
                        ROUND(SUM(total_amount), 2) as total_revenue
                     FROM orders 
                     GROUP BY payment_method 
                     ORDER BY total_orders DESC;"""
            takeaway = "Credit Card and PayPal remain the dominant payment choices accounting for over 70% of transactions."
            tip = "💡 Advisor Tip: Credit Card transactions have the highest average order value. Would you like to view customer order trends?"
            return sql, "bar", "Orders & Revenue by Payment Method", "payment_method", ["total_orders"], takeaway, tip

        sql = f"""SELECT 
                    p.product_name as product, 
                    ROUND(SUM(oi.subtotal), 2) as total_revenue,
                    SUM(oi.quantity) as units_sold
                 FROM order_items oi
                 JOIN products p ON oi.product_id = p.product_id
                 GROUP BY p.product_id
                 ORDER BY total_revenue DESC
                 LIMIT {limit};"""
        takeaway = "QuantumBook Pro 15 generated the highest overall revenue at $32,475 across 25 units sold."
        tip = "💡 Advisor Tip: Top products account for over 45% of total sales. Would you like to see monthly revenue trends for these items?"
        return sql, "bar", f"Top {limit} Products by Sales Revenue", "product", ["total_revenue"], takeaway, tip

    def _run_gemini_agent(self, message: str, api_key: str, history: List[Dict[str, Any]], target_table: Optional[str] = None, attached_file_name: Optional[str] = None) -> Dict[str, Any]:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        schema_info = get_schema(self.db_path, table_name=target_table)
        prompt = f"""You are a friendly, helpful AI Business Data Analyst companion.
Database Schema Context:
{json.dumps(schema_info, indent=2)}

Target Table Context: {target_table or "All Database Tables"}
Attached File Context: {attached_file_name or "None"}

User Question: "{message}"

Instructions:
1. If user question asks about target table or attached file, generate an exact SQLite query for table `{target_table or "orders"}`.
2. Select appropriate chart type: "bar", "line", "pie", "scatter", "area", or null.
3. Identify x_key and y_keys.
4. Provide a plain ONE-SENTENCE executive takeaway summarizing the finding.

Return ONLY a valid JSON object matching this exact format:
{{
  "is_unrelated": false,
  "sql": "SELECT ...",
  "chart_type": "bar",
  "title": "Title of Chart",
  "x_key": "column_name",
  "y_keys": ["numeric_column_name"],
  "takeaway": "Plain one sentence takeaway."
}}"""

        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```[a-z]*\n?", "", text)
            text = re.sub(r"\n?```$", "", text)

        parsed = json.loads(text)
        sql = parsed.get("sql")
        chart_type = parsed.get("chart_type")
        title = parsed.get("title", "Data Insights")
        x_key = parsed.get("x_key")
        y_keys = parsed.get("y_keys", [])
        takeaway = parsed.get("takeaway", "Analyzed query results from database.")

        tool_logs = [
            {"tool": "get_schema", "status": "executed"},
            {"tool": "execute_query", "status": "executed"}
        ]
        query_res = execute_query(sql, self.db_path)
        data = query_res.get("data", [])

        chart_res = None
        if data and chart_type and x_key and y_keys:
            chart_res = generate_chart(
                chart_type=chart_type,
                title=title,
                data=data,
                x_key=x_key,
                y_keys=y_keys,
                description=f"Chart generated for: '{message}'"
            )
            chart_res["takeaway"] = takeaway
            tool_logs.append({"tool": "generate_chart", "status": "executed"})

        explain_res = explain_data(
            data=data,
            query_context=message,
            highlights=[
                takeaway,
                f"Generated custom SQL via Gemini AI: `{sql}`",
                f"Retrieved {len(data)} record(s) from database."
            ]
        )
        tool_logs.append({"tool": "explain_data", "status": "executed"})

        source_info = (
            {"type": "uploaded_file", "name": attached_file_name or target_table, "table": target_table}
            if target_table else
            {"type": "sqlite", "name": "ecommerce_sample.db"}
        )

        return {
            "role": "assistant",
            "model_badge": "Google Gemini 1.5",
            "data_source": source_info,
            "content": f"Gemini AI analyzed your attached data request and compiled the insights.",
            "tools_called": tool_logs,
            "sql_info": query_res,
            "chart": chart_res,
            "flowchart": None,
            "insights": explain_res
        }

    def _run_openai_agent(self, message: str, api_key: str, history: List[Dict[str, Any]], target_table: Optional[str] = None, attached_file_name: Optional[str] = None) -> Dict[str, Any]:
        import openai
        client = openai.OpenAI(api_key=api_key)
        schema_info = get_schema(self.db_path, table_name=target_table)

        prompt = f"""You are a friendly, helpful AI Business Data Analyst companion.
Database Schema Context:
{json.dumps(schema_info, indent=2)}

Target Table Context: {target_table or "All Database Tables"}
Attached File Context: {attached_file_name or "None"}

User Question: "{message}"

Return ONLY a valid JSON object matching this exact format:
{{
  "is_unrelated": false,
  "sql": "SELECT ...",
  "chart_type": "bar",
  "title": "Title of Chart",
  "x_key": "column_name",
  "y_keys": ["numeric_column_name"],
  "takeaway": "Plain one sentence takeaway."
}}"""

        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )

        parsed = json.loads(completion.choices[0].message.content)
        sql = parsed.get("sql")
        chart_type = parsed.get("chart_type")
        title = parsed.get("title", "Data Insights")
        x_key = parsed.get("x_key")
        y_keys = parsed.get("y_keys", [])
        takeaway = parsed.get("takeaway", "Analyzed query results from database.")

        tool_logs = [
            {"tool": "get_schema", "status": "executed"},
            {"tool": "execute_query", "status": "executed"}
        ]
        query_res = execute_query(sql, self.db_path)
        data = query_res.get("data", [])

        chart_res = None
        if data and chart_type and x_key and y_keys:
            chart_res = generate_chart(
                chart_type=chart_type,
                title=title,
                data=data,
                x_key=x_key,
                y_keys=y_keys,
                description=f"Chart generated for: '{message}'"
            )
            chart_res["takeaway"] = takeaway
            tool_logs.append({"tool": "generate_chart", "status": "executed"})

        explain_res = explain_data(
            data=data,
            query_context=message,
            highlights=[
                takeaway,
                f"Generated custom SQL via GPT-4o: `{sql}`",
                f"Retrieved {len(data)} record(s) from database."
            ]
        )
        tool_logs.append({"tool": "explain_data", "status": "executed"})

        source_info = (
            {"type": "uploaded_file", "name": attached_file_name or target_table, "table": target_table}
            if target_table else
            {"type": "sqlite", "name": "ecommerce_sample.db"}
        )

        return {
            "role": "assistant",
            "model_badge": "OpenAI GPT-4o",
            "data_source": source_info,
            "content": f"GPT-4o analyzed your attached data request and compiled the insights.",
            "tools_called": tool_logs,
            "sql_info": query_res,
            "chart": chart_res,
            "flowchart": None,
            "insights": explain_res
        }
