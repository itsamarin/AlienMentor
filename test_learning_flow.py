import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

import app as coach_app
from coach_ai import coach_content
from graph_store import DemoStore


class LearningFlowTests(unittest.TestCase):
    def setUp(self):
        coach_app.store = DemoStore()
        coach_app.mode = "demo"
        coach_app.mode_message = "Demo mode · test"
        coach_app.question_cache = {}
        coach_app.last_state = None
        self.client = coach_app.app.test_client()
        self.env_patch = patch.dict(os.environ, {"OPENAI_API_KEY": ""})
        self.env_patch.start()

    def tearDown(self):
        self.env_patch.stop()

    def test_home_page_and_bootstrap_show_demo_data_truthfully(self):
        page = self.client.get("/")
        state = self.client.get("/api/bootstrap").get_json()
        self.assertEqual(page.status_code, 200)
        self.assertIn(b"AlienMentor", page.data)
        self.assertEqual(state["mode"], "demo")
        self.assertEqual(state["goalId"], "python-data-analyst")
        self.assertEqual(len(state["concepts"]), 265)
        self.assertEqual(state["plan"]["concept"]["id"], "python-basics")
        self.assertEqual(state["plan"]["coachSource"], "curated")
        self.assertTrue(state["graph"]["relationships"])

    def test_setup_validates_and_builds_a_goal_specific_plan(self):
        invalid = self.client.post("/api/setup", json={"goalId": "made-up", "level": "beginner", "minutes": 30})
        self.assertEqual(invalid.status_code, 400)
        response = self.client.post("/api/setup", json={
            "goalId": "german-language-learner", "level": "intermediate", "minutes": 45,
        })
        self.assertEqual(response.status_code, 200)
        state = response.get_json()
        self.assertEqual(state["goalId"], "german-language-learner")
        self.assertEqual(state["level"], "intermediate")
        self.assertEqual(state["minutes"], 45)
        self.assertEqual(state["plan"]["concept"]["id"], "german-foundations")

    def test_wrong_answer_recommends_review_then_correct_answer_advances(self):
        state = self.client.get("/api/bootstrap").get_json()
        concept_id = state["plan"]["concept"]["id"]
        options = state["plan"]["question"]["options"]
        missed = self.client.post("/api/answer", json={"conceptId": concept_id, "answer": options[1]}).get_json()
        self.assertFalse(missed["correct"])
        self.assertEqual(missed["next"]["plan"]["concept"]["id"], "python-basics")
        self.assertEqual(missed["next"]["plan"]["progress"]["overallAccuracy"], 0)

        next_options = missed["next"]["plan"]["question"]["options"]
        passed = self.client.post("/api/answer", json={"conceptId": concept_id, "answer": next_options[0]}).get_json()
        self.assertTrue(passed["correct"])
        self.assertEqual(passed["next"]["plan"]["concept"]["id"], "python-functions")
        self.assertEqual(len(passed["next"]["results"]), 2)
        self.assertEqual(passed["next"]["plan"]["progress"]["overallAccuracy"], 50)

    def test_answer_must_match_the_current_question_and_option(self):
        state = self.client.get("/api/bootstrap").get_json()
        wrong_concept = self.client.post("/api/answer", json={"conceptId": "statistics", "answer": "Median"})
        wrong_option = self.client.post("/api/answer", json={"conceptId": state["plan"]["concept"]["id"], "answer": "not an option"})
        self.assertEqual(wrong_concept.status_code, 409)
        self.assertEqual(wrong_option.status_code, 400)

    def test_ai_output_is_validated_and_provider_failure_uses_curated_fallback(self):
        concept = coach_app._build_state()["plan"]["concept"]
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}), patch("coach_ai.urlopen", side_effect=TimeoutError):
            result = coach_content(concept, [], "beginner")
        self.assertEqual(result["source"], "curated")
        self.assertIn("AI request failed", result["notice"])
        self.assertNotIn("correctAnswer", coach_app._build_state()["plan"])

    def test_ai_result_is_structured_and_correct_answer_remains_server_side(self):
        concept = coach_app._build_state()["plan"]["concept"]
        payload = {"choices": [{"message": {"content": json.dumps({
            "lesson": "A variable stores a value so a program can reuse it later.",
            "prompt": "Which statement describes a variable?",
            "options": ["A named place for a value", "A Python package", "A loop condition"],
            "answer": "A named place for a value",
        })}}]}

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return json.dumps(payload).encode()

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}), patch("coach_ai.urlopen", return_value=Response()):
            result = coach_content(concept, [], "beginner")
        self.assertEqual(result["source"], "openai")
        self.assertEqual(result["correctAnswer"], result["question"]["options"][0])

    def test_runtime_neo4j_failure_switches_to_labeled_demo(self):
        class BrokenStore:
            def snapshot(self, _goal=None):
                raise OSError("private database detail")

        coach_app.store = BrokenStore()
        coach_app.mode = "neo4j"
        result = self.client.get("/api/bootstrap").get_json()
        self.assertEqual(result["mode"], "demo")
        self.assertIn("Neo4j is unavailable", result["modeMessage"])
        self.assertEqual(result["plan"]["coachSource"], "curated")

    def test_ui_has_keyboard_selectable_graph_and_mobile_concept_list(self):
        page = self.client.get("/").get_data(as_text=True)
        script = Path("static/app.js").read_text(encoding="utf-8")
        stylesheet = Path("static/style.css").read_text(encoding="utf-8")
        self.assertIn('id="graph-mobile"', page)
        self.assertIn('id="node-detail"', page)
        self.assertIn('role="button"', script)
        self.assertIn('event.key==="Enter"', script)
        self.assertIn("@media (max-width: 700px)", stylesheet)


if __name__ == "__main__":
    unittest.main()
