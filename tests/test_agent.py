import os
import sys
import unittest

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))

from database import init_and_seed_db
from agent import DatabaseAgent, NVIDIA_TOOLS, TOOL_HANDLERS

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test_agent_native_db.db")

class TestDatabaseAgentNative(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_and_seed_db(TEST_DB_PATH)
        cls.agent = DatabaseAgent(db_path=TEST_DB_PATH)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

    def test_1_native_tool_specs(self):
        self.assertEqual(len(NVIDIA_TOOLS), 5)
        tool_names = [t["function"]["name"] for t in NVIDIA_TOOLS]
        self.assertIn("get_schema", tool_names)
        self.assertIn("execute_query", tool_names)
        self.assertIn("generate_chart", tool_names)
        self.assertIn("generate_flowchart", tool_names)
        self.assertIn("explain_data", tool_names)

    def test_2_tool_handlers_whitelist(self):
        self.assertIn("execute_query", TOOL_HANDLERS)
        res = TOOL_HANDLERS["execute_query"]("SELECT COUNT(*) as total FROM products;", db_path=TEST_DB_PATH)
        self.assertEqual(res["status"], "success")
        self.assertGreater(res["data"][0]["total"], 0)

    def test_3_autonomous_fallback_agent(self):
        res = self.agent.process_message("Show me top 5 products by revenue")
        self.assertEqual(res["role"], "assistant")
        self.assertIn("tools_called", res)
        self.assertIsNotNone(res.get("sql_info"))
        self.assertIsNotNone(res.get("chart"))
        self.assertIsNotNone(res.get("insights"))

    def test_4_streaming_generator(self):
        events = list(self.agent.process_message_stream("Show top customers by spending"))
        self.assertGreater(len(events), 3)
        self.assertEqual(events[0]["event"], "stage")
        self.assertEqual(events[-1]["event"], "complete")
        self.assertIn("sql_info", events[-1]["data"])

    def test_5_nvidia_native_call_skips_when_key_missing(self):
        # When NVIDIA_API_KEY is missing, native agent skips and falls back cleanly without crashing
        if "NVIDIA_API_KEY" not in os.environ:
            res = self.agent.process_message("Show me revenue trends")
            self.assertEqual(res["role"], "assistant")
            self.assertIn("model_badge", res)

if __name__ == "__main__":
    unittest.main()
