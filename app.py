from __future__ import annotations

import logging
import os
import re
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

from coach_ai import coach_content
from curriculum import CONCEPTS, GOALS, recommendation
from graph_store import DemoStore, build_store


ROOT = Path(__file__).parent
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())
logger = logging.getLogger(__name__)


def load_local_env():
    """Load simple KEY=value entries from .env without printing their values."""
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for raw in env_file.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            os.environ.setdefault(key, value)


load_local_env()
store, mode, mode_message = build_store()
app = Flask(__name__)
question_cache: dict[tuple, dict] = {}
last_state: dict | None = None


def _demo_fallback(exc):
    """Switch to a visible local fallback after a runtime database failure."""
    global store, mode, mode_message
    previous = store
    fallback = DemoStore()
    # Keep progress already fetched from Neo4j in this process when possible.
    if last_state:
        fallback.results = list(previous.results) if isinstance(previous, DemoStore) else list(last_state.get("results", []))
        fallback.setup(last_state.get("goalId", GOALS[0][0]), last_state.get("level", "beginner"), last_state.get("minutes", 30))
    store, mode = fallback, "demo"
    mode_message = "Demo fallback · Neo4j is unavailable; new results are local"
    logger.warning("Neo4j request failed; switched to demo mode (%s)", type(exc).__name__)


def _graph_payload(concepts, goals, required, results, learner, selected_goal):
    relationships = []
    for concept in concepts:
        for prereq_id in concept.get("prerequisites") or []:
            relationships.append({"source": prereq_id, "type": "PREREQUISITE_OF", "target": concept["id"]})
        resource = concept.get("resource") or {}
        if resource.get("url"):
            relationships.append({"source": concept["id"], "type": "EXPLAINED_IN", "target": resource["url"], "label": resource.get("title", "Resource")})
    goal_name = next((goal["name"] for goal in goals if goal["id"] == selected_goal), "Selected goal")
    relationships.extend({"source": selected_goal, "type": "REQUIRES", "target": concept_id} for concept_id in required)
    relationships.append({"source": "learnpath-demo-learner", "type": "PURSUING", "target": selected_goal, "label": goal_name})
    for result in results:
        relationships.append({"source": result.get("id"), "type": "ASSESSES", "target": result.get("conceptId")})
    return {"nodes": concepts, "relationships": relationships}


def _build_state(goal_id=None, level_override=None, minutes_override=None):
    global store, mode, mode_message, last_state
    try:
        concepts, goals, required, results, learner = store.snapshot(goal_id)
    except Exception as exc:
        if mode != "neo4j":
            logger.error("Learning data could not be loaded (%s)", type(exc).__name__)
            raise
        _demo_fallback(exc)
        concepts, goals, required, results, learner = store.snapshot(goal_id)

    selected_goal = goal_id or (learner or {}).get("goalId") or getattr(store, "goal_id", GOALS[0][0])
    valid_goal_ids = {goal["id"] for goal in goals}
    if selected_goal not in valid_goal_ids:
        selected_goal = GOALS[0][0]
        concepts, goals, required, results, learner = store.snapshot(selected_goal)
    learner = learner or {"level": "beginner", "minutes": 30, "goalId": selected_goal}
    level = level_override or learner.get("level") or "beginner"
    minutes = minutes_override or learner.get("minutes") or 30
    plan = recommendation(concepts, required, results, level, minutes)
    cache_key = (
        plan["concept"]["id"], level,
        tuple((item["id"], item["status"]) for item in plan["prerequisiteStatus"]),
    )
    content = question_cache.get(cache_key)
    if content is None:
        content = coach_content(plan["concept"], plan["prerequisiteStatus"], level)
        question_cache[cache_key] = content
    plan["lesson"] = content["lesson"]
    plan["question"] = content["question"]
    plan["coachSource"] = content["source"]
    plan["coachNotice"] = content["notice"]
    plan["aiConfigured"] = bool(os.getenv("OPENAI_API_KEY", "").strip())

    state = {
        "mode": mode,
        "modeMessage": mode_message,
        "coachSource": content["source"],
        "goalId": selected_goal,
        "level": level,
        "minutes": minutes,
        "goals": goals,
        "required": required,
        "plan": plan,
        "results": results,
        "concepts": concepts,
        "graph": _graph_payload(concepts, goals, required, results, learner, selected_goal),
    }
    last_state = state
    return state


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/bootstrap")
def bootstrap():
    requested_goal = request.args.get("goal")
    return jsonify(_build_state(requested_goal))


@app.post("/api/setup")
def setup():
    body = request.get_json(silent=True) or {}
    goal_id, level = body.get("goalId"), body.get("level")
    try:
        minutes = int(body.get("minutes", 30))
        if (goal_id not in {goal[0] for goal in GOALS}
                or level not in {"beginner", "intermediate", "advanced"}
                or not 10 <= minutes <= 180):
            raise ValueError
    except (TypeError, ValueError):
        return jsonify(error="Choose a listed goal and level; daily study time must be 10–180 minutes."), 400

    try:
        store.setup(goal_id, level, minutes)
    except Exception as exc:
        if mode != "neo4j":
            logger.error("Learning plan setup failed (%s)", type(exc).__name__)
            return jsonify(error="The learning plan could not be built. Please try again."), 503
        _demo_fallback(exc)
        store.setup(goal_id, level, minutes)
    return jsonify(_build_state(goal_id, level, minutes))


@app.post("/api/answer")
def answer():
    body = request.get_json(silent=True) or {}
    concept_id, chosen = body.get("conceptId"), body.get("answer")
    if concept_id not in {concept[0] for concept in CONCEPTS} or not isinstance(chosen, str) or len(chosen) > 500:
        return jsonify(error="Choose an answer for the current practice question."), 400
    if not last_state or concept_id != last_state["plan"]["concept"]["id"]:
        return jsonify(error="This practice question is no longer current. Build a fresh plan and try again."), 409

    plan = last_state["plan"]
    cache_key = (
        plan["concept"]["id"], last_state["level"],
        tuple((item["id"], item["status"]) for item in plan["prerequisiteStatus"]),
    )
    content = question_cache.get(cache_key)
    if not content or chosen not in content["question"]["options"]:
        return jsonify(error="Choose one of the answer options shown for this question."), 400
    correct = chosen == content["correctAnswer"]
    try:
        store.record(concept_id, correct, chosen, content["question"]["prompt"])
    except Exception as exc:
        if mode != "neo4j":
            logger.error("Assessment result could not be saved (%s)", type(exc).__name__)
            return jsonify(error="Your result could not be saved. Please try again."), 503
        _demo_fallback(exc)
        store.setup(last_state["goalId"], last_state["level"], last_state["minutes"])
        store.record(concept_id, correct, chosen, content["question"]["prompt"])

    feedback = (
        "Correct — your result is recorded and the coach will check the next eligible concept."
        if correct else f"Not quite. The expected answer is “{content['correctAnswer']}”. Review this concept before moving on."
    )
    next_state = _build_state(last_state["goalId"])
    return jsonify({"correct": correct, "feedback": feedback, "resultRecordedIn": next_state["mode"], "next": next_state})


@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "mode": mode,
        "modeMessage": mode_message,
        "aiConfigured": bool(os.getenv("OPENAI_API_KEY", "").strip()),
        "conceptCount": len(CONCEPTS),
    })


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    if isinstance(error, HTTPException):
        return error
    if request.path.startswith("/api/"):
        logger.error("Unhandled learning coach API error (%s)", type(error).__name__)
        return jsonify(error="The coach could not complete that request. Please retry."), 500
    logger.error("Unhandled page error (%s)", type(error).__name__)
    return "The learning coach could not load this page.", 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
