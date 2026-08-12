import os
import io
import re
import json
import sqlite3
import pandas as pd
from typing import Dict, Any, List

def sanitize_table_name(name: str) -> str:
    base = os.path.splitext(name)[0]
    clean = re.sub(r'[^a-zA-Z0-9_]', '_', base)
    if not clean or clean[0].isdigit():
        clean = f"data_{clean}"
    return clean.lower()

def sanitize_column_name(col_name: str) -> str:
    clean = re.sub(r'[^a-zA-Z0-9_]', '_', str(col_name).strip())
    if not clean or clean[0].isdigit():
        clean = f"col_{clean}"
    return clean.lower()

def process_uploaded_file(file_bytes: bytes, filename: str, db_path: str) -> Dict[str, Any]:
    """
    Universal ingestor for user attached data supporting files:
    Excel (.xlsx/.xls), CSV (.csv), JSON (.json), Markdown (.md), Text (.txt/.log), PDF (.pdf), Word (.docx).
    Loads parsed dataset into SQLite tables for dynamic query execution and visualization.
    """
    ext = os.path.splitext(filename)[1].lower()
    table_name = sanitize_table_name(filename)

    conn = sqlite3.connect(db_path)
    created_tables = []
    total_rows_imported = 0

    try:
        if ext in ['.xlsx', '.xls']:
            # Excel spreadsheet parsing (multiple sheets supported)
            excel_file = pd.ExcelFile(io.BytesIO(file_bytes))
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                df.columns = [sanitize_column_name(c) for c in df.columns]
                
                sheet_tbl = f"{table_name}_{sanitize_table_name(sheet_name)}" if len(excel_file.sheet_names) > 1 else table_name
                df.to_sql(sheet_tbl, conn, if_exists='replace', index=False)
                created_tables.append(sheet_tbl)
                total_rows_imported += len(df)

        elif ext == '.csv':
            # CSV parsing
            df = pd.read_csv(io.BytesIO(file_bytes))
            df.columns = [sanitize_column_name(c) for c in df.columns]
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            created_tables.append(table_name)
            total_rows_imported += len(df)

        elif ext == '.json':
            # JSON robust parsing handling dicts, list of dicts, and nested objects
            json_str = file_bytes.decode('utf-8', errors='ignore')
            parsed_json = json.loads(json_str)

            if isinstance(parsed_json, list):
                df = pd.json_normalize(parsed_json)
            elif isinstance(parsed_json, dict):
                # Try to extract internal list if present, else convert single dict
                list_key = next((k for k, v in parsed_json.items() if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict)), None)
                if list_key:
                    df = pd.json_normalize(parsed_json[list_key])
                else:
                    df = pd.json_normalize([parsed_json])
            else:
                df = pd.DataFrame([{"value": str(parsed_json)}])

            df.columns = [sanitize_column_name(c) for c in df.columns]
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            created_tables.append(table_name)
            total_rows_imported += len(df)

        elif ext in ['.md', '.txt', '.log']:
            # Text / Markdown line-by-line structured document ingestion
            text_str = file_bytes.decode('utf-8', errors='ignore')
            lines = text_str.splitlines()
            records = []
            current_section = "General"

            for idx, line in enumerate(lines, 1):
                clean_line = line.strip()
                if not clean_line:
                    continue
                if clean_line.startswith('#'):
                    current_section = clean_line.lstrip('#').strip()
                records.append({
                    "line_number": idx,
                    "section": current_section,
                    "content": clean_line
                })

            df = pd.DataFrame(records if records else [{"line_number": 1, "section": "General", "content": text_str}])
            df.columns = [sanitize_column_name(c) for c in df.columns]
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            created_tables.append(table_name)
            total_rows_imported += len(df)

        elif ext == '.pdf':
            # PDF Document Parsing
            records = []
            try:
                import pypdf
                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                for page_idx, page in enumerate(reader.pages, 1):
                    page_text = page.extract_text() or ""
                    for line_idx, line in enumerate(page_text.splitlines(), 1):
                        if line.strip():
                            records.append({
                                "page_number": page_idx,
                                "line_number": line_idx,
                                "content": line.strip()
                            })
            except Exception:
                records = [{"page_number": 1, "line_number": 1, "content": "Failed to extract PDF text."}]

            df = pd.DataFrame(records if records else [{"page_number": 1, "line_number": 1, "content": "Empty PDF document."}])
            df.columns = [sanitize_column_name(c) for c in df.columns]
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            created_tables.append(table_name)
            total_rows_imported += len(df)

        elif ext in ['.docx', '.doc']:
            # Word Document Parsing
            records = []
            try:
                import docx
                doc = docx.Document(io.BytesIO(file_bytes))
                for idx, para in enumerate(doc.paragraphs, 1):
                    if para.text.strip():
                        records.append({
                            "paragraph_number": idx,
                            "content": para.text.strip()
                        })
            except Exception:
                records = [{"paragraph_number": 1, "content": "Failed to extract Word document text."}]

            df = pd.DataFrame(records if records else [{"paragraph_number": 1, "content": "Empty Word document."}])
            df.columns = [sanitize_column_name(c) for c in df.columns]
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            created_tables.append(table_name)
            total_rows_imported += len(df)

        else:
            conn.close()
            return {
                "status": "error",
                "message": f"Unsupported file format '{ext}'. Supported formats: .xlsx, .xls, .csv, .json, .md, .txt, .pdf, .docx"
            }

        conn.commit()
        conn.close()

        return {
            "status": "success",
            "filename": filename,
            "table_names": created_tables,
            "primary_table": created_tables[0] if created_tables else table_name,
            "rows_imported": total_rows_imported,
            "message": f"Successfully imported '{filename}' into SQLite table(s): {', '.join(created_tables)}"
        }

    except Exception as e:
        conn.close()
        return {
            "status": "error",
            "message": f"Failed to parse attached file '{filename}': {str(e)}"
        }
