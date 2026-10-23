"""Graph persistence adapters for the Neo4j and local demo modes."""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from uuid import uuid4

from curriculum import CONCEPTS, GOALS, RESOURCE_URLS

logger = logging.getLogger(__name__)
APP_NAMESPACE = "learnpath-ai"  # Keep the existing graph namespace for data compatibility.
LEARNER_ID = "learnpath-demo-learner"  # Preserve existing learner assessment history.

try:
    from neo4j import GraphDatabase
except ImportError:
    GraphDatabase = None


class DemoStore:
    """A deterministic process-local data store for demos without Neo4j."""

    def __init__(self):
        self.goal_id = GOALS[0][0]
        self.level = "beginner"
        self.minutes = 30
        self.results: list[dict] = []

    def setup(self, goal_id, level, minutes):
        self.goal_id, self.level, self.minutes = goal_id, level, minutes

    def snapshot(self, goal_id=None):
        concepts = []
        for item in CONCEPTS:
            title, url = RESOURCE_URLS[item[2]]
            concepts.append({
                "id": item[0], "name": item[1], "domain": item[2], "level": item[3],
                "prerequisites": item[4], "description": item[5],
                "resource": {"title": title, "url": url},
            })
        selected_goal = goal_id or self.goal_id
        goals = [{"id": goal[0], "name": goal[1]} for goal in GOALS]
        required = next((goal[2] for goal in GOALS if goal[0] == selected_goal), GOALS[0][2])
        learner = {"level": self.level, "minutes": self.minutes, "goalId": selected_goal}
        return concepts, goals, required, list(self.results), learner

    def record(self, concept_id, correct, answer, question):
        self.results.append({
            "id": f"demo-{uuid4().hex[:12]}", "conceptId": concept_id,
            "score": 1.0 if correct else 0.0, "correct": bool(correct),
            "answer": answer[:500], "question": question[:500], "timestamp": datetime.now(timezone.utc).isoformat(),
        })


class Neo4jStore:
    def __init__(self, driver, database):
        self.driver, self.database = driver, database

    def seed(self):
        constraints = [
            "CREATE CONSTRAINT alien_concept_key IF NOT EXISTS FOR (n:Concept) REQUIRE (n.app, n.id) IS UNIQUE",
            "CREATE CONSTRAINT alien_goal_key IF NOT EXISTS FOR (n:LearningGoal) REQUIRE (n.app, n.id) IS UNIQUE",
            "CREATE CONSTRAINT alien_learner_key IF NOT EXISTS FOR (n:Learner) REQUIRE (n.app, n.id) IS UNIQUE",
            "CREATE CONSTRAINT alien_activity_key IF NOT EXISTS FOR (n:LearningActivity) REQUIRE (n.app, n.id) IS UNIQUE",
            "CREATE CONSTRAINT alien_result_key IF NOT EXISTS FOR (n:AssessmentResult) REQUIRE (n.app, n.id) IS UNIQUE",
            "CREATE CONSTRAINT alien_resource_key IF NOT EXISTS FOR (n:Resource) REQUIRE (n.app, n.url) IS UNIQUE",
        ]
        with self.driver.session(database=self.database) as session:
            for query in constraints:
                session.run(query)
            session.run("""
                UNWIND $concepts AS row
                MERGE (c:Concept {id: row.id, app: $app})
                SET c.name=row.name, c.domain=row.domain, c.level=row.level, c.description=row.description
                MERGE (r:Resource {url: row.resourceUrl, app: $app})
                SET r.title=row.resourceTitle
                MERGE (c)-[:EXPLAINED_IN]->(r)
            """, concepts=self._concept_rows(), app=APP_NAMESPACE)
            # Keep the graph aligned with the current three-tier curriculum.
            # Only app-owned learning-path edges are replaced; learner history
            # and unrelated graph data are left intact.
            session.run("""
                MATCH (pre:Concept {app:$app})-[edge:PREREQUISITE_OF]->(next:Concept {app:$app})
                DELETE edge
            """, app=APP_NAMESPACE)
            session.run("""
                MATCH (goal:LearningGoal {app:$app})-[edge:REQUIRES]->(concept:Concept {app:$app})
                DELETE edge
            """, app=APP_NAMESPACE)
            session.run("""
                UNWIND $edges AS edge
                MATCH (pre:Concept {id: edge[0], app: $app}), (next:Concept {id: edge[1], app: $app})
                MERGE (pre)-[:PREREQUISITE_OF]->(next)
            """, edges=[[pre, item[0]] for item in CONCEPTS for pre in item[4]], app=APP_NAMESPACE)
            session.run("""
                UNWIND $goals AS row
                MERGE (g:LearningGoal {id: row.id, app: $app}) SET g.name=row.name
                WITH g, row
                UNWIND row.requires AS conceptId
                MATCH (c:Concept {id: conceptId, app: $app})
                MERGE (g)-[:REQUIRES]->(c)
            """, goals=[{"id": item[0], "name": item[1], "requires": item[2]} for item in GOALS], app=APP_NAMESPACE)

    @staticmethod
    def _concept_rows():
        return [{
            "id": item[0], "name": item[1], "domain": item[2], "level": item[3],
            "description": item[5], "resourceTitle": RESOURCE_URLS[item[2]][0],
            "resourceUrl": RESOURCE_URLS[item[2]][1],
        } for item in CONCEPTS]

    def setup(self, goal_id, level, minutes):
        with self.driver.session(database=self.database) as session:
            session.run("""
                MERGE (l:Learner {id:$id, app:$app})
                SET l.level=$level, l.dailyMinutes=$minutes, l.updatedAt=datetime()
                WITH l
                OPTIONAL MATCH (l)-[old:PURSUING]->(:LearningGoal {app:$app})
                DELETE old
                WITH DISTINCT l
                MATCH (g:LearningGoal {id:$goal, app:$app})
                MERGE (l)-[:PURSUING]->(g)
            """, id=LEARNER_ID, level=level, minutes=minutes, goal=goal_id, app=APP_NAMESPACE)

    def snapshot(self, goal_id=None):
        with self.driver.session(database=self.database) as session:
            concepts = [record.data() for record in session.run("""
                MATCH (c:Concept {app:$app})
                OPTIONAL MATCH (pre:Concept {app:$app})-[:PREREQUISITE_OF]->(c)
                OPTIONAL MATCH (c)-[:EXPLAINED_IN]->(res:Resource {app:$app})
                RETURN c.id AS id, c.name AS name, c.domain AS domain, c.level AS level,
                       c.description AS description, collect(DISTINCT pre.id) AS prerequisites,
                       head(collect(DISTINCT CASE WHEN res IS NULL THEN null
                            ELSE {title:res.title, url:res.url} END)) AS resource
                ORDER BY c.level, c.name
            """, app=APP_NAMESPACE)]
            for concept in concepts:
                if not concept.get("resource") or not concept["resource"].get("url"):
                    title, url = RESOURCE_URLS.get(concept.get("domain"), ("Learning resource", ""))
                    concept["resource"] = {"title": title, "url": url}
            goals = [record.data() for record in session.run(
                "MATCH (g:LearningGoal {app:$app}) RETURN g.id AS id, g.name AS name ORDER BY name",
                app=APP_NAMESPACE,
            )]
            learner_record = session.run("""
                MATCH (l:Learner {id:$id, app:$app})
                OPTIONAL MATCH (l)-[:PURSUING]->(g:LearningGoal {app:$app})
                RETURN l.level AS level, l.dailyMinutes AS minutes, g.id AS goalId
            """, id=LEARNER_ID, app=APP_NAMESPACE).single()
            learner = dict(learner_record) if learner_record else None
            selected_goal = goal_id or (learner or {}).get("goalId") or GOALS[0][0]
            required = [record["id"] for record in session.run("""
                MATCH (:LearningGoal {id:$id, app:$app})-[:REQUIRES]->(c:Concept {app:$app})
                RETURN c.id AS id
            """, id=selected_goal, app=APP_NAMESPACE)]
            results = [record.data() for record in session.run("""
                MATCH (:Learner {id:$id, app:$app})-[:COMPLETED]->
                      (:LearningActivity {app:$app})-[:ASSESSED_BY]->
                      (r:AssessmentResult {app:$app})-[:FOR_CONCEPT]->(c:Concept {app:$app})
                RETURN r.id AS id, c.id AS conceptId, r.score AS score,
                       r.correct AS correct, toString(r.createdAt) AS timestamp
                ORDER BY r.createdAt
            """, id=LEARNER_ID, app=APP_NAMESPACE)]
            return concepts, goals, required, results, learner

    def record(self, concept_id, correct, answer, question):
        result_id = uuid4().hex
        with self.driver.session(database=self.database) as session:
            result = session.run("""
                MATCH (l:Learner {id:$learner, app:$app}), (c:Concept {id:$concept, app:$app})
                CREATE (a:LearningActivity {id:$activity, app:$app, type:'practice',
                       conceptId:$concept, completedAt:datetime()})
                CREATE (r:AssessmentResult {id:$result, app:$app, score:$score,
                       correct:$correct, answer:$answer, question:$question, createdAt:datetime()})
                CREATE (l)-[:COMPLETED]->(a)-[:ASSESSED_BY]->(r)
                CREATE (r)-[:FOR_CONCEPT]->(c)
                RETURN r.id AS id
            """, learner=LEARNER_ID, concept=concept_id, activity=f"activity-{result_id}",
                 result=f"result-{result_id}", score=1.0 if correct else 0.0,
                 correct=correct, answer=answer[:500], question=question[:500], app=APP_NAMESPACE).single()
            if result is None:
                raise RuntimeError("Learner or concept was not found in the AlienMentor graph")


def build_store():
    """Use Neo4j only after credentials, driver, and explicit write access are present."""
    configured = all(os.getenv(key) for key in ("NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD"))
    partially_configured = any(os.getenv(key) for key in ("NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD"))
    writable = os.getenv("NEO4J_READ_ONLY", "true").lower() not in {"1", "true", "yes"}
    if not configured and partially_configured:
        return DemoStore(), "demo", "Setup required · set the URI, username, and password to connect Neo4j"
    if not configured:
        return DemoStore(), "demo", "Demo mode · Neo4j credentials not configured"
    if not writable:
        return DemoStore(), "demo", "Demo mode · Neo4j writes are disabled"
    if GraphDatabase is None:
        return DemoStore(), "demo", "Demo mode · install the Neo4j Python driver to connect"
    try:
        driver = GraphDatabase.driver(
            os.environ["NEO4J_URI"],
            auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
        )
        driver.verify_connectivity()
        store = Neo4jStore(driver, os.getenv("NEO4J_DATABASE", "neo4j"))
        store.seed()
        return store, "neo4j", "Neo4j graph connected · curriculum seeded"
    except Exception as exc:
        try:
            driver.close()
        except Exception:
            pass
        logger.warning("Neo4j connection unavailable; using demo mode (%s)", type(exc).__name__)
        return DemoStore(), "demo", "Demo mode · Neo4j connection unavailable"
