import os
import sys
import unittest
import asyncio
import time
from typing import List, Dict, Any

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))

from database import init_and_seed_db
from agent import DatabaseAgent

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test_concurrency_db.db")

class TestConcurrencyAndCancellation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_and_seed_db(TEST_DB_PATH)
        cls.agent = DatabaseAgent(db_path=TEST_DB_PATH)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

    def test_1_request_id_in_stream_events(self):
        req_id = "test_req_001"
        events = list(self.agent.process_message_stream("Show top products", request_id=req_id))
        self.assertGreater(len(events), 0)
        for ev in events:
            self.assertEqual(ev.get("request_id"), req_id)
        self.assertEqual(events[-1]["event"], "complete")
        self.assertEqual(events[-1]["data"].get("request_id"), req_id)

    def test_2_concurrent_requests_isolation(self):
        """Simulate two concurrent queries A and B with independent request_ids."""
        events_a = []
        events_b = []

        def worker_a():
            for ev in self.agent.process_message_stream("Show me the top 5 products by revenue", request_id="req_A"):
                events_a.append(ev)

        def worker_b():
            for ev in self.agent.process_message_stream("What is the total number of customers?", request_id="req_B"):
                events_b.append(ev)

        import threading
        t1 = threading.Thread(target=worker_a)
        t2 = threading.Thread(target=worker_b)

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertGreater(len(events_a), 0)
        self.assertGreater(len(events_b), 0)

        # All events for A have req_A
        for ev in events_a:
            self.assertEqual(ev.get("request_id"), "req_A")

        # All events for B have req_B
        for ev in events_b:
            self.assertEqual(ev.get("request_id"), "req_B")

        # Payloads are independent
        complete_a = events_a[-1]["data"]
        complete_b = events_b[-1]["data"]
        self.assertIsNotNone(complete_a.get("sql_info"))
        self.assertIsNotNone(complete_b.get("sql_info"))
        self.assertNotEqual(complete_a["sql_info"]["query"], complete_b["sql_info"]["query"])

    def test_3_multi_turn_memory_preservation(self):
        """Test multi-turn query resolution ('Show me top 5 products' -> 'Now show their monthly trend')."""
        res1 = self.agent.process_message("Show me top 5 products by revenue", request_id="turn_1")
        history = [
            {"role": "user", "content": "Show me top 5 products by revenue"},
            {"role": "assistant", "content": res1["content"], "sql_info": res1.get("sql_info")}
        ]
        res2 = self.agent.process_message("Now show their monthly trend", history=history, request_id="turn_2")
        self.assertEqual(res2["role"], "assistant")
        self.assertIsNotNone(res2.get("sql_info"))
        self.assertIn("request_id", res2)
        self.assertEqual(res2["request_id"], "turn_2")

if __name__ == "__main__":
    unittest.main()
