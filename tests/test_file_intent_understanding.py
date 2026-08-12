import unittest
import os
import sys
import json
import sqlite3

sys.path.insert(0, os.path.abspath("backend"))

from agent import DatabaseAgent
from file_handler import process_uploaded_file

class TestFileIntentUnderstanding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = "c:/Users/Shabaz-shaik/Downloads/sairam_hackathon-main/sairam_hackathon-main/data/ecommerce_sample.db"
        cls.agent = DatabaseAgent(db_path=cls.db_path)

        # Create dummy PDF table representing SEM 6.pdf
        conn = sqlite3.connect(cls.db_path)
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS sem_6;")
        cursor.execute("""
            CREATE TABLE sem_6 (
                page_number INT,
                line_number INT,
                content TEXT
            );
        """)
        pdf_lines = [
            (1, 1, "Department of Computer Science and Engineering"),
            (1, 2, "Anna University Regulations 2021 - Semester VI Syllabus"),
            (1, 3, "Course Code: CS8651 - Internet Programming"),
            (1, 4, "Course Code: CS8691 - Artificial Intelligence"),
            (1, 5, "Course Code: CS8601 - Mobile Computing"),
            (2, 1, "Lab Work: Web Application Development Lab"),
            (2, 2, "Exam Schedule: Theory Exams commence on May 15th, 2026.")
        ]
        cursor.executemany("INSERT INTO sem_6 VALUES (?, ?, ?);", pdf_lines)

        # Create dummy Excel table representing Sri Sai Ram Institute of Technology, Chennai (5).xlsx
        cursor.execute("DROP TABLE IF EXISTS sri_sai_ram_institute_of_technology__chennai__5_;")
        cursor.execute("""
            CREATE TABLE sri_sai_ram_institute_of_technology__chennai__5_ (
                college_name TEXT,
                superset_id INT,
                department TEXT,
                total_students INT,
                placement_status TEXT
            );
        """)
        excel_rows = [
            ("Sri Sai Ram Institute of Technology", 101, "Computer Science", 120, "95% Placed"),
            ("Sri Sai Ram Institute of Technology", 102, "Information Technology", 110, "92% Placed"),
            ("Sri Sai Ram Institute of Technology", 103, "Electronics & Comm", 115, "88% Placed"),
            ("Sri Sai Ram Institute of Technology", 104, "Mechanical Engineering", 90, "82% Placed")
        ]
        cursor.executemany("INSERT INTO sri_sai_ram_institute_of_technology__chennai__5_ VALUES (?, ?, ?, ?, ?);", excel_rows)

        conn.commit()
        conn.close()

    def test_a_pdf_overview_intent(self):
        """TEST A: PDF 'What is inside this file?' -> Text summary of extracted PDF text, NO forced chart!"""
        res = self.agent.process_message(
            user_message="What is inside this file?",
            target_table="sem_6",
            attached_file_name="SEM 6.pdf"
        )
        self.assertIsNone(res.get("chart"), "Must NOT force a chart for PDF content overview!")
        self.assertIn("sem_6", res.get("data_source", {}).get("table", ""))
        print("\n--- TEST A Output ('SEM 6.pdf' -> 'What is inside this file?') ---")
        print(res.get("content"))

    def test_b_excel_overview_intent(self):
        """TEST B: Excel 'What's inside this file?' -> Natural language overview based on real spreadsheet facts, NO forced chart!"""
        res = self.agent.process_message(
            user_message="What's inside this file?",
            target_table="sri_sai_ram_institute_of_technology__chennai__5_",
            attached_file_name="Sri Sai Ram Institute of Technology, Chennai (5).xlsx"
        )
        self.assertIsNone(res.get("chart"), "Must NOT force a chart for Excel dataset overview!")
        print("\n--- TEST B Output (Excel -> 'What's inside this file?') ---")
        print(res.get("content"))

    def test_c_excel_columns_intent(self):
        """TEST C: Excel 'What columns are present?' -> Lists actual column names, NO forced chart!"""
        res = self.agent.process_message(
            user_message="What columns are present?",
            target_table="sri_sai_ram_institute_of_technology__chennai__5_",
            attached_file_name="Sri Sai Ram Institute of Technology, Chennai (5).xlsx"
        )
        self.assertIsNone(res.get("chart"), "Must NOT force a chart for column list query!")

    def test_d_excel_record_count_intent(self):
        """TEST D: Excel 'How many records are there?' -> Returns actual record count, NO forced chart!"""
        res = self.agent.process_message(
            user_message="How many records are there?",
            target_table="sri_sai_ram_institute_of_technology__chennai__5_",
            attached_file_name="Sri Sai Ram Institute of Technology, Chennai (5).xlsx"
        )
        self.assertIsNone(res.get("chart"), "Must NOT force a chart for record count query!")

    def test_e_excel_show_data_intent(self):
        """TEST E: Excel 'Show me the data.' -> Retrieves table records."""
        res = self.agent.process_message(
            user_message="Show me the data.",
            target_table="sri_sai_ram_institute_of_technology__chennai__5_",
            attached_file_name="Sri Sai Ram Institute of Technology, Chennai (5).xlsx"
        )
        self.assertIsNotNone(res.get("sql_info"), "Must execute SQL query to retrieve data records!")

    def test_f_excel_analytical_chart_intent(self):
        """TEST F: Excel 'Show me a chart of total_students by department' -> Generates real chart!"""
        res = self.agent.process_message(
            user_message="Show me a chart of total_students by department",
            target_table="sri_sai_ram_institute_of_technology__chennai__5_",
            attached_file_name="Sri Sai Ram Institute of Technology, Chennai (5).xlsx"
        )
        self.assertIsNotNone(res.get("chart"), "Must generate chart when explicitly requested!")

    def test_g_pdf_summarize_intent(self):
        """TEST G: PDF 'Summarize this document.' -> Natural language summary of extracted PDF text!"""
        res = self.agent.process_message(
            user_message="Summarize this document.",
            target_table="sem_6",
            attached_file_name="SEM 6.pdf"
        )
        self.assertIsNone(res.get("chart"), "Must NOT force a chart for PDF document summary!")

    def test_h_pdf_topic_search_intent(self):
        """TEST H: PDF 'Find the section about Exam Schedule' -> Relevant document content explanation!"""
        res = self.agent.process_message(
            user_message="Find the section about Exam Schedule",
            target_table="sem_6",
            attached_file_name="SEM 6.pdf"
        )
        self.assertIsNone(res.get("chart"), "Must NOT force a chart for topic search query!")

    def test_i_casual_chat_with_attachment(self):
        """TEST I: Casual chat with attachment ('Hey, what's up?') -> Conversational response, 0 database queries!"""
        res = self.agent.process_message(
            user_message="Hey, what's up?",
            target_table="sem_6",
            attached_file_name="SEM 6.pdf"
        )
        self.assertEqual(len(res.get("tools_called", [])), 0, "Must NOT call database tools for casual chat!")
        self.assertIsNone(res.get("chart"), "Must NOT generate chart for casual chat!")

    def test_j_database_analysis_without_attachment(self):
        """TEST J: Database analysis ('Show me the top 5 products by revenue.') -> Existing native tool calling workflow preserved!"""
        res = self.agent.process_message(
            user_message="Show me the top 5 products by revenue."
        )
        self.assertTrue(any(t.get("tool") == "execute_query" for t in res.get("tools_called", [])), "Must execute SQL query for database analysis!")
        self.assertIsNotNone(res.get("chart"), "Must generate chart for revenue breakdown!")

if __name__ == "__main__":
    unittest.main()
