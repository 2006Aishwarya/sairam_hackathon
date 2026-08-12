import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))
from agent import DatabaseAgent

UNSEEN_QUERIES = [
    "Which product has the highest average order quantity?",
    "What percentage of customers have never placed an order?",
    "Which month had the highest revenue?",
    "Show me top 3 categories by average order value.",
    "Which products are low in stock but high in demand?",
    "Compare average product price against units sold.",
    "What is the distribution of orders by payment method?",
    "Which customers have placed more than 3 orders?",
    "Show revenue concentration among the top 10 products.",
    "What is the average review rating by category?",
    "How many total orders are in the system?",
    "What is the total revenue generated across all time?",
    "Show customer signup distribution by country.",
    "Which user segment spends the most per order?",
    "Show inventory restocking log history."
]

def main():
    agent = DatabaseAgent()
    print("==========================================================")
    print("TESTING 15 UNSEEN NATURAL LANGUAGE DATABASE QUERIES")
    print("==========================================================")
    
    success_count = 0
    for idx, q in enumerate(UNSEEN_QUERIES, 1):
        try:
            res = agent.process_message(q)
            sql = res.get("sql_info", {}).get("query") if res.get("sql_info") else "None"
            row_count = res.get("sql_info", {}).get("row_count", 0) if res.get("sql_info") else 0
            chart = res.get("chart", {}).get("chart_type") if res.get("chart") else "No chart"
            
            print(f"\n[Query {idx:02d}] '{q}'")
            print(f"  * Status: OK")
            print(f"  * SQL: {sql}")
            print(f"  * Rows Returned: {row_count}")
            print(f"  * Chart Rendered: {chart}")
            success_count += 1
        except Exception as e:
            print(f"\n[Query {idx:02d}] '{q}' -> Error: {e}")

    print("\n==========================================================")
    print(f"RESULT: {success_count}/{len(UNSEEN_QUERIES)} Unseen Queries Processed Successfully.")
    print("==========================================================")

if __name__ == "__main__":
    main()
