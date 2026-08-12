import os
import sys
import unittest

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))

from database import init_and_seed_db
from agent import DatabaseAgent

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test_brain_db.db")

class TestConversationalBrain(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_and_seed_db(TEST_DB_PATH)
        cls.agent = DatabaseAgent(db_path=TEST_DB_PATH)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

    def test_case_1_casual_greeting(self):
        res = self.agent.process_message("hey there, what's up?")
        self.assertEqual(res["role"], "assistant")
        self.assertEqual(res["tools_called"], [])
        self.assertIsNone(res.get("sql_info"))
        self.assertIsNone(res.get("chart"))
        self.assertTrue(len(res["content"]) > 0)
        print("\nTEST 1 ('hey there, what's up?'): Passed - 0 tools called.")

    def test_case_2_identity_question(self):
        res = self.agent.process_message("who are you?")
        self.assertEqual(res["role"], "assistant")
        self.assertEqual(res["tools_called"], [])
        self.assertIsNone(res.get("sql_info"))
        print("TEST 2 ('who are you?'): Passed - 0 tools called.")

    def test_case_3_capabilities_question(self):
        res = self.agent.process_message("what can you do?")
        self.assertEqual(res["role"], "assistant")
        self.assertEqual(res["tools_called"], [])
        self.assertIsNone(res.get("sql_info"))
        print("TEST 3 ('what can you do?'): Passed - 0 tools called.")

    def test_case_4_joke_request(self):
        res = self.agent.process_message("tell me a joke")
        self.assertEqual(res["role"], "assistant")
        self.assertEqual(res["tools_called"], [])
        self.assertIsNone(res.get("sql_info"))
        print("TEST 4 ('tell me a joke'): Passed - 0 tools called.")

    def test_case_5_thanks_message(self):
        res = self.agent.process_message("thanks!")
        self.assertEqual(res["role"], "assistant")
        self.assertEqual(res["tools_called"], [])
        self.assertIsNone(res.get("sql_info"))
        print("TEST 5 ('thanks!'): Passed - 0 tools called.")

    def test_case_6_products_query(self):
        res = self.agent.process_message("Show me the top 5 products by revenue.")
        self.assertEqual(res["role"], "assistant")
        self.assertGreater(len(res["tools_called"]), 0)
        self.assertIsNotNone(res.get("sql_info"))
        print("TEST 6 ('Show me top 5 products'): Passed - Tools called:", [t["tool"] for t in res["tools_called"]])

    def test_case_7_total_revenue(self):
        res = self.agent.process_message("What is the total revenue?")
        self.assertEqual(res["role"], "assistant")
        self.assertGreater(len(res["tools_called"]), 0)
        self.assertIsNotNone(res.get("sql_info"))
        print("TEST 7 ('What is total revenue?'): Passed - Tools called:", [t["tool"] for t in res["tools_called"]])

    def test_case_8_monthly_revenue(self):
        res = self.agent.process_message("Show me monthly revenue.")
        self.assertEqual(res["role"], "assistant")
        self.assertGreater(len(res["tools_called"]), 0)
        self.assertIsNotNone(res.get("sql_info"))
        print("TEST 8 ('Show me monthly revenue'): Passed - Tools called:", [t["tool"] for t in res["tools_called"]])

    def test_case_9_er_diagram(self):
        res = self.agent.process_message("Draw the ER diagram.")
        self.assertEqual(res["role"], "assistant")
        self.assertGreater(len(res["tools_called"]), 0)
        self.assertIsNotNone(res.get("flowchart"))
        print("TEST 9 ('Draw the ER diagram'): Passed - Flowchart generated.")

    def test_case_10_multiturn_memory(self):
        res1 = self.agent.process_message("Show me the top 5 products by revenue.")
        history = [
            {"role": "user", "content": "Show me the top 5 products by revenue."},
            {"role": "assistant", "content": res1["content"]}
        ]
        res2 = self.agent.process_message("Now show their monthly trend.", history=history)
        self.assertEqual(res2["role"], "assistant")
        self.assertGreater(len(res2["tools_called"]), 0)
        print("TEST 10 ('Now show their monthly trend'): Passed - Multi-turn memory preserved.")

if __name__ == "__main__":
    unittest.main()
