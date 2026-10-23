"""Optional, graph-grounded OpenAI content with a deterministic local fallback."""
from __future__ import annotations

import json
import logging
import os
from urllib.request import Request, urlopen

from curriculum import question_for

logger = logging.getLogger(__name__)


def _fallback(concept, reason):
    question = question_for(concept["id"])
    return {
        "lesson": concept.get("description", ""),
        "question": question,
        "correctAnswer": question["options"][0],
        "source": "curated",
        "notice": reason,
    }


def coach_content(concept, prerequisites, level):
    """Generate a short lesson and quiz strictly from retrieved graph facts.

    No network request is made unless OPENAI_API_KEY is explicitly configured.
    The correct answer stays server-side and is validated against the options.
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return _fallback(concept, "Curated practice · AI provider not configured")

    schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "alienmentor_lesson",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "lesson": {"type": "string"},
                    "prompt": {"type": "string"},
                    "options": {"type": "array", "items": {"type": "string"}, "minItems": 3, "maxItems": 3},
                    "answer": {"type": "string"},
                },
                "required": ["lesson", "prompt", "options", "answer"],
                "additionalProperties": False,
            },
        },
    }
    graph_facts = {
        "concept": {
            "id": concept["id"],
            "name": concept["name"],
            "domain": concept["domain"],
            "description": concept.get("description", ""),
            "resource": concept.get("resource", {}),
        },
        "prerequisites": [
            {"id": item.get("id"), "name": item.get("name"), "status": item.get("status")}
            for item in prerequisites
        ],
        "learner_level": level,
    }
    payload = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "messages": [
            {
                "role": "developer",
                "content": (
                    "You are AlienMentor, a concise daily learning coach. Use only the supplied graph facts. "
                    "Do not invent concepts, prerequisite links, resource claims, or learner results. "
                    "Explain the named concept at the learner's level. Write one short multiple-choice question "
                    "that tests only the supplied concept description. Provide exactly three distinct options "
                    "and set answer to the exact text of one correct option. Return the required JSON only."
                ),
            },
            {"role": "user", "content": json.dumps(graph_facts, ensure_ascii=False)},
        ],
        "response_format": schema,
        "max_completion_tokens": 450,
        "store": False,
    }
    request = Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=18) as response:
            response_data = json.loads(response.read().decode("utf-8"))
        content = response_data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        lesson, prompt = parsed.get("lesson"), parsed.get("prompt")
        options, answer = parsed.get("options"), parsed.get("answer")
        if not isinstance(lesson, str) or not 20 <= len(lesson.strip()) <= 700:
            raise ValueError("Invalid lesson")
        if not isinstance(prompt, str) or not 10 <= len(prompt.strip()) <= 300:
            raise ValueError("Invalid practice question")
        if (not isinstance(options, list) or len(options) != 3
                or any(not isinstance(option, str) or not 1 <= len(option.strip()) <= 120 for option in options)
                or len({option.strip() for option in options}) != 3):
            raise ValueError("Invalid answer options")
        options = [option.strip() for option in options]
        if not isinstance(answer, str) or answer.strip() not in options:
            raise ValueError("Invalid correct answer")
        return {
            "lesson": lesson.strip(),
            "question": {"prompt": prompt.strip(), "options": options},
            "correctAnswer": answer.strip(),
            "source": "openai",
            "notice": "AI-generated lesson and practice · grounded in the selected graph concept and prerequisite records",
        }
    except Exception as exc:
        logger.warning("AI lesson generation unavailable; using curated content (%s)", type(exc).__name__)
        return _fallback(concept, "Curated practice · AI request failed or returned invalid content")
