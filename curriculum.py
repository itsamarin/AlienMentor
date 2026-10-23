from __future__ import annotations

# Core concepts keep the first demo recommendation short and predictable.
CONCEPTS = [
    ("python-basics", "Python basics", "Python", 1, [], "Variables, expressions, and control flow form the foundation for data work.", "In Python, what does `len([3, 5, 8])` return?", ["3", "2", "8"]),
    ("python-functions", "Functions and modules", "Python", 2, ["python-basics"], "Functions package reusable logic and modules help organize a project.", "What keyword defines a function in Python?", ["def", "func", "lambda"]),
    ("python-collections", "Lists and dictionaries", "Python", 2, ["python-basics"], "Choose a collection that matches the way your data will be accessed.", "Which collection maps unique keys to values?", ["dictionary", "list", "tuple"]),
    ("python-data", "Working with tabular data", "Data science", 3, ["python-collections", "python-functions"], "Structured rows and columns make real-world datasets easier to inspect and transform.", "In a table, what does one row usually represent?", ["One record", "A column type", "A chart axis"]),
    ("statistics", "Descriptive statistics", "Data science", 3, ["python-data"], "Summaries such as mean and median help describe a dataset before modeling.", "Which measure is less affected by an extreme outlier: mean or median?", ["Median", "Mean", "They are always equal"]),
    ("data-visualization", "Data visualization", "Data science", 3, ["python-data", "statistics"], "A suitable chart can reveal trends, outliers, and comparisons.", "Which chart is usually a good first choice for comparing category totals?", ["Bar chart", "Network graph", "Scatter plot"]),
    ("ml-basics", "Machine learning foundations", "Data science", 4, ["statistics", "python-data"], "A model learns patterns from examples and is evaluated on data it did not train on.", "Why keep a test set separate from training data?", ["To estimate performance on unseen data", "To make training faster only", "To remove all outliers"]),
    ("neo4j-modeling", "Graph modeling with Neo4j", "Neo4j", 2, ["python-basics"], "Modeling entities as nodes and named relationships makes connections explicit.", "In a property graph, where can properties be stored?", ["On nodes and relationships", "Only on nodes", "Only in indexes"]),
    ("cypher-match", "Cypher MATCH and RETURN", "Cypher", 3, ["neo4j-modeling"], "MATCH finds graph patterns; RETURN shapes the result sent to the client.", "Which Cypher clause finds a pattern in the graph?", ["MATCH", "RETURN", "CREATE"]),
    ("cypher-create", "Cypher CREATE and MERGE", "Cypher", 3, ["cypher-match"], "CREATE adds new patterns; MERGE matches or creates a pattern idempotently.", "Which clause is usually preferred for an idempotent seed operation?", ["MERGE", "CREATE", "DELETE"]),
    ("cypher-paths", "Paths and variable-length patterns", "Cypher", 4, ["cypher-match"], "Path patterns let you traverse multiple relationship hops.", "What does `[:KNOWS*1..3]` describe?", ["One to three KNOWS relationships", "Exactly three nodes", "A relationship property"]),
    ("cypher-aggregation", "Cypher aggregation", "Cypher", 4, ["cypher-match"], "Aggregation turns many matched rows into useful summaries.", "Which function counts rows in a Cypher result?", ["count()", "size()", "rows()"]),
    ("vector-search", "Embeddings and vector search", "GraphRAG", 4, ["python-functions", "neo4j-modeling"], "Embeddings represent text as vectors that can be compared for semantic similarity.", "What does vector similarity search retrieve?", ["Items with nearby embedding vectors", "Only exact keyword matches", "The shortest graph path"]),
    ("retrieval", "Retrieval-augmented generation", "GraphRAG", 5, ["vector-search", "cypher-paths"], "Retrieval provides relevant evidence to a language model before it answers.", "In RAG, what is retrieved before generation?", ["Relevant source context", "A final answer", "A model's weights"]),
    ("graph-rag", "GraphRAG context building", "GraphRAG", 5, ["retrieval", "neo4j-modeling"], "Graph structure adds connected entities and relationships to retrieved context.", "What can a graph add to text retrieval?", ["Connected entities and relationships", "Guaranteed factual answers", "More model parameters"]),
    ("llm-basics", "Language model prompting", "AI agents", 4, ["python-functions"], "Clear instructions and structured context make model behavior easier to guide.", "What is a useful way to constrain an LLM response shape?", ["Request a specific schema", "Remove all context", "Use a longer random prompt"]),
    ("tool-calling", "LLM tool calling", "AI agents", 5, ["llm-basics", "python-functions"], "Tool calling lets a model request a defined operation through application code.", "Who should execute and validate a requested tool call?", ["The application", "The prompt alone", "The database automatically"]),
    ("agent-loops", "Agent loops and state", "AI agents", 5, ["tool-calling"], "An agent loop coordinates observation, action, and stopping conditions.", "Why should an agent loop have a stopping condition?", ["To bound repeated actions", "To increase token count", "To avoid using state"]),
    ("agent-evaluation", "Evaluating AI agents", "AI agents", 6, ["agent-loops", "ml-basics"], "Evaluation checks whether an agent completes tasks reliably and safely.", "What is a useful agent evaluation?", ["A repeatable task with a measurable expected outcome", "One impressive example", "A longer system prompt"]),
    ("neo4j-graphrag", "Neo4j GraphRAG workflows", "GraphRAG", 6, ["graph-rag", "cypher-aggregation"], "A graph-backed retrieval workflow combines semantic retrieval with graph context.", "What should be checked before using retrieved graph context in an answer?", ["That it is relevant and supported by the retrieved records", "That it has the most nodes", "That it is always complete"]),
    ("german-foundations", "German language foundations", "German language", 1, [], "Start with everyday greetings, useful phrases, and beginner listening practice.", "What does “Guten Morgen” mean?", ["Good morning", "Good evening", "Good night"]),
    ("thai-dance-foundations", "Thai dance foundations", "Thai dance", 1, [], "Explore Thai classical dance through posture, hand gestures, rhythm, and cultural context.", "What is a useful way to begin learning a traditional dance movement?", ["Follow a qualified teacher's slow demonstration", "Rush through the sequence without guidance", "Ignore posture and timing"]),
    ("muay-thai-foundations", "Muay Thai foundations", "Thai boxing", 1, [], "Learn Muay Thai's history, stance, guard, and movement through structured instruction.", "What is one purpose of keeping a balanced stance and guard?", ["Protect yourself while staying ready to move", "Make it harder to see your coach", "Replace warm-up and instruction"]),
]

GOALS = [
    ("python-data-analyst", "Become a Python data analyst", ["data-visualization", "ml-basics"]),
    ("neo4j-developer", "Build with Neo4j and Cypher", ["cypher-create", "cypher-paths", "cypher-aggregation"]),
    ("graphrag-builder", "Build a GraphRAG application", ["neo4j-graphrag"]),
    ("ai-agent-builder", "Create reliable AI agents", ["agent-evaluation"]),
    ("graph-data-scientist", "Explore data with graphs and Python", ["data-visualization", "graph-rag"]),
    ("german-language-learner", "Learn German", ["german-foundations"]),
    ("thai-dance-learner", "Learn Thai dance", ["thai-dance-foundations"]),
    ("muay-thai-learner", "Learn Thai boxing (Muay Thai)", ["muay-thai-foundations"]),
]

from curriculum_expansion import EXPANSION_TRACKS


_TRACK_STAGE_IDS = {}
for _track in EXPANSION_TRACKS:
    _stage_ids = []
    _tier_start = min(_track["base_level"], 3)
    for _index, (_name, _description) in enumerate(_track["items"], start=1):
        _concept_id = f"{_track['prefix']}-extension-{_index:02d}"
        _layer = min(2, ((_index - 1) * 3) // len(_track["items"]))
        if _layer == 0:
            _prerequisites = list(_track["after"])
        else:
            _previous_layer = _stage_ids[_layer - 1]
            _position = len(_stage_ids[_layer]) if len(_stage_ids) > _layer else 0
            _prerequisites = list(dict.fromkeys((
                _previous_layer[_position % len(_previous_layer)],
                _previous_layer[(_position + 1) % len(_previous_layer)],
            )))
        # Course depth is deliberately limited to three tiers.
        _level = min(6, _tier_start + 2 * _layer)
        _question = f"Which statement best describes {_name}?"
        _options = [
            _description,
            "It guarantees a correct result without checking evidence.",
            "It makes every prerequisite concept unnecessary.",
        ]
        CONCEPTS.append((
            _concept_id, _name, _track["domain"], _level, _prerequisites,
            _description, _question, _options,
        ))
        if len(_stage_ids) <= _layer:
            _stage_ids.append([])
        _stage_ids[_layer].append(_concept_id)
    _TRACK_STAGE_IDS[_track["prefix"]] = _stage_ids

_GOAL_EXTENSIONS = {
    "python-data-analyst": ["python", "data"],
    "neo4j-developer": ["neo4j", "cypher"],
    "graphrag-builder": ["graphrag"],
    "ai-agent-builder": ["agent"],
    "graph-data-scientist": ["data", "graphrag"],
    "german-language-learner": ["german"],
    "thai-dance-learner": ["dance"],
    "muay-thai-learner": ["muaythai"],
}
GOALS = [
    (goal_id, name, required + [concept_id for prefix in _GOAL_EXTENSIONS.get(goal_id, [])
                               for concept_id in _TRACK_STAGE_IDS[prefix][-1]])
    for goal_id, name, required in GOALS
]

for _prefix, _stage_ids in ((track["prefix"], _TRACK_STAGE_IDS[track["prefix"]]) for track in EXPANSION_TRACKS):
    if _prefix in {"dance", "muaythai"}:
        _domain = "Thai dance" if _prefix == "dance" else "Thai boxing"
        for _tier, _stage in (("foundations", _stage_ids[0]), ("intermediate", _stage_ids[1]), ("advanced", _stage_ids[-1])):
            GOALS.append((f"{_prefix}-{_tier}", f"{_domain}: {_tier.title()} course", list(_stage)))

assert len(CONCEPTS) > 200, f"Expected more than 200 curriculum concepts, found {len(CONCEPTS)}"

RESOURCE_URLS = {
    "Python": ("Python Tutorial", "https://docs.python.org/3/tutorial/"),
    "Data science": ("pandas Getting Started", "https://pandas.pydata.org/docs/getting_started/intro_tutorials/"),
    "Neo4j": ("Neo4j GraphAcademy", "https://graphacademy.neo4j.com/"),
    "Cypher": ("Cypher Manual", "https://neo4j.com/docs/cypher-manual/current/"),
    "GraphRAG": ("Neo4j GraphRAG resources", "https://neo4j.com/docs/neo4j-graphrag-python/current/"),
    "AI agents": ("Neo4j GraphAcademy", "https://graphacademy.neo4j.com/"),
    "German language": ("Goethe-Institut free German practice", "https://www.goethe.de/ins/de/en/kur/ueb.html"),
    "Thai dance": ("Thailand Foundation: Rakram Thai Dance Course", "https://thailandfoundation.or.th/rakram-ep-5-central-thai-dance/"),
    "Thai boxing": ("IFMA: Muaythai Rules and Disciplines", "https://muaythai.sport/about-muaythai/muaythai-rules/"),
}



from datetime import datetime, timezone


def question_for(concept_id):
    item = next((c for c in CONCEPTS if c[0] == concept_id), None)
    if item is None:
        raise ValueError("Unknown concept")
    return {"prompt": item[6], "options": item[7]}


def required_path(concepts, required):
    """Return the goal concepts and all prerequisite ancestors from graph data."""
    by_id = {concept["id"]: concept for concept in concepts}
    needed, stack = set(), list(required)
    while stack:
        concept_id = stack.pop()
        if concept_id in needed or concept_id not in by_id:
            continue
        needed.add(concept_id)
        stack.extend(by_id[concept_id].get("prerequisites") or [])
    return needed


def mastery_by_concept(concepts, results):
    out = {}
    for concept in concepts:
        scores = [float(result["score"]) for result in results if result["conceptId"] == concept["id"]]
        out[concept["id"]] = sum(scores) / len(scores) if scores else None
    return out


def current_streak_days(results):
    """Count consecutive UTC dates with at least one recorded practice result."""
    days = set()
    for result in results:
        timestamp = result.get("timestamp")
        if not timestamp:
            continue
        try:
            parsed = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
            days.add(parsed.date())
        except ValueError:
            continue
    if not days:
        return 0
    cursor = datetime.now(timezone.utc).date()
    if cursor not in days:
        cursor = cursor.fromordinal(cursor.toordinal() - 1)
    count = 0
    while cursor in days:
        count += 1
        cursor = cursor.fromordinal(cursor.toordinal() - 1)
    return count


def recommendation(concepts, required, results, level, minutes):
    by_id = {concept["id"]: concept for concept in concepts}
    needed = required_path(concepts, required)
    mastery = mastery_by_concept(concepts, results)
    latest = {}
    for result in results:
        latest[result["conceptId"]] = result
    level_target = {"beginner": 2, "intermediate": 4, "advanced": 6}.get(level, 2)

    def ready(concept):
        return all((mastery.get(pre_id) is not None and mastery[pre_id] >= .7)
                   or bool(latest.get(pre_id, {}).get("correct"))
                   for pre_id in concept.get("prerequisites", []))

    # A latest incorrect answer triggers a review. A later correct answer clears
    # that immediate review; historical averages remain visible as evidence.
    reviews = [by_id[cid] for cid in needed if cid in by_id
               and latest.get(cid) is not None and not latest[cid].get("correct") and ready(by_id[cid])]
    if reviews:
        reviews.sort(key=lambda concept: (mastery[concept["id"]], abs(concept["level"] - level_target), concept["name"]))
        chosen = reviews[0]
    else:
        eligible = [by_id[cid] for cid in needed if cid in by_id
                    and latest.get(cid) is None and ready(by_id[cid])]
        if eligible:
            eligible.sort(key=lambda concept: (abs(concept["level"] - level_target), concept["level"], concept["name"]))
            chosen = eligible[0]
        else:
            # Goal path complete: recommend a review of the least-secure path concept.
            finished = [by_id[cid] for cid in needed if cid in by_id]
            if not finished:
                raise ValueError("The selected goal has no concepts in the learning graph")
            finished.sort(key=lambda concept: (mastery[concept["id"]] if mastery[concept["id"]] is not None else 0, concept["name"]))
            chosen = finished[0]

    observed = mastery[chosen["id"]]
    if latest.get(chosen["id"]) is not None and not latest[chosen["id"]].get("correct"):
        reasons = [f"Your latest answer for {chosen['name']} was incorrect, so review comes before new material."]
    else:
        reasons = [f"{chosen['name']} is on the prerequisite path for your selected goal and fits your {level} level."]
        if observed is None:
            reasons.append("There is no recorded assessment for this concept yet, so this practice establishes a useful checkpoint.")
    prerequisite_status = []
    for pre_id in chosen.get("prerequisites", []):
        prerequisite = by_id.get(pre_id)
        if not prerequisite:
            continue
        score = mastery.get(pre_id)
        latest_result = latest.get(pre_id)
        status = ("mastered" if score is not None and score >= .7 else
                  "review" if latest_result is not None and not latest_result.get("correct") else
                  "passed" if latest_result is not None else "not_assessed")
        prerequisite_status.append({"id": pre_id, "name": prerequisite["name"], "status": status, "observedAverage": score})
    if prerequisite_status:
        reasons.append("Required prerequisites have recorded results at or above the 70% progression threshold.")

    concept = dict(chosen)
    concept.setdefault("resource", {"title": "No resource linked", "url": ""})
    scores = [float(result["score"]) for result in results if result["conceptId"] == chosen["id"]]
    estimated = (0.5 + sum(scores)) / (1 + len(scores))
    total = len(needed)
    mastered = sum(1 for cid in needed if mastery.get(cid) is not None and mastery[cid] >= .7)
    attempts = len(results)
    accuracy = sum(1 for result in results if result.get("correct")) / attempts if attempts else None
    goal_progress = mastered / total if total else 0
    return {
        "concept": concept,
        "minutes": min(minutes, max(10, round(minutes * .35))),
        "reasons": reasons,
        "question": question_for(chosen["id"]),
        "lesson": chosen.get("description", ""),
        "mastery": observed,
        "masteryLabel": "Observed assessment average" if observed is not None else "No observed assessments",
        "estimatedMastery": estimated,
        "estimatedMasteryMethod": "Smoothed score with a 50% prior; estimate only, not a recorded result.",
        "prerequisiteStatus": prerequisite_status,
        "progress": {
            "goalPathCompleted": mastered,
            "goalPathTotal": total,
            "goalPathPercent": round(goal_progress * 100),
            "conceptsTried": len({result["conceptId"] for result in results}),
            "attempts": attempts,
            "overallAccuracy": round(accuracy * 100) if accuracy is not None else None,
            "masteredConcepts": mastered,
            "currentStreakDays": current_streak_days(results),
        },
    }
