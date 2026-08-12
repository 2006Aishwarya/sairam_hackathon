import os
import sys
import unittest

# Add backend directory to path for importing modules
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))

from database import init_and_seed_db
from tools.get_schema import get_schema
from tools.execute_query import execute_query
from tools.generate_chart import generate_chart
from tools.generate_flowchart import generate_flowchart
from tools.explain_data import explain_data

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test_data.db")

class TestAgentTools(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_and_seed_db(TEST_DB_PATH)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

    def test_1_get_schema(self):
        res = get_schema(TEST_DB_PATH)
        self.assertEqual(res["status"], "success")
        self.assertIn("schema", res)
        tables = res["schema"]["tables"]
        self.assertIn("customers", tables)
        self.assertIn("products", tables)
        self.assertIn("orders", tables)
        self.assertIn("order_items", tables)
        self.assertGreaterEqual(len(tables["products"]["columns"]), 5)

    def test_2_execute_query_valid(self):
        sql = "SELECT product_name, price FROM products ORDER BY price DESC LIMIT 5;"
        res = execute_query(sql, TEST_DB_PATH)
        self.assertEqual(res["status"], "success")
        self.assertEqual(len(res["data"]), 5)
        self.assertIn("product_name", res["columns"])
        self.assertGreaterEqual(res["execution_time_ms"], 0)

    def test_3_execute_query_guardrail(self):
        forbidden_sql = "DROP TABLE customers;"
        res = execute_query(forbidden_sql, TEST_DB_PATH)
        self.assertEqual(res["status"], "error")
        self.assertTrue("Violation" in res["message"] or "disabled" in res["message"])

    def test_4_generate_chart_bar(self):
        sample_data = [
            {"product": "Laptop", "revenue": 12000},
            {"product": "Headphones", "revenue": 4500}
        ]
        res = generate_chart(
            chart_type="bar",
            title="Top Sales",
            data=sample_data,
            x_key="product",
            y_keys=["revenue"]
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["chart_type"], "bar")
        self.assertEqual(res["x_key"], "product")
        self.assertEqual(len(res["data"]), 2)

    def test_5_generate_flowchart_er(self):
        mermaid = "erDiagram CUSTOMERS ||--o{ ORDERS : places"
        res = generate_flowchart(
            diagram_type="er_diagram",
            title="Sample ER",
            mermaid_code=mermaid
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["diagram_type"], "er_diagram")
        self.assertIn("erDiagram", res["mermaid_code"])

    def test_6_explain_data(self):
        sample_data = [{"item": "Headphones", "val": 100}, {"item": "Laptop", "val": 500}]
        res = explain_data(
            data=sample_data,
            query_context="Explain top sales",
            highlights=["Laptop had the highest value."]
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["row_count"], 2)
        self.assertGreater(len(res["highlights"]), 0)

if __name__ == "__main__":
    unittest.main()
