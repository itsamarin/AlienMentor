# Neo4j Mini Agentic Hack

## Workshop Content

[Complete the workshop to receive a Neo4j Certificate of Completion](https://github.com/neo4j-graphacademy/workshop-hackathon).

### Goal

Build and experiment.

Create a small AI application using Neo4j and try one or both of these products:

- [Neo4j Aura Free](https://neo4j.com/product/auradb/) — start building with a free managed Neo4j database
- [Neo4j Document Intelligence](https://neo4j.com/blog/graph-database/introducing-document-intelligence-from-documents-to-a-knowledge-graph-right-inside-aura/) — turn documents into a knowledge graph
- [Neo4j Aura MCP](https://neo4j.com/docs/mcp/current/mcp-for-aura/) — connect AI agents with graph data
- [Neo4j Agent Memory Service](https://memory.neo4jlabs.com/) — give your agents persistent memory

You are free to choose your own idea, documents, stack, and approach.

### Suggested Flow

1. Choose a simple use case.
2. Add documents or data.
3. Build or generate a knowledge graph.
4. Ask connected questions about the graph.
5. Add agent memory if useful.
6. Prepare a short demo.
7. Note what worked, what was confusing, and what blocked you.

A finished production application is not required. A working experiment and useful feedback are enough.

## Feedback

_Add your feedback here._

## Hackathon Tools

### GitHub Codespace

[Open the hackathon repository in a GitHub Codespace](https://codespaces.new/neo4j-graphacademy/workshop-hackathon).

### Neo4j Aura MCP

[Neo4j Aura MCP](https://neo4j.com/docs/mcp/current/mcp-for-aura/) is a hosted MCP server for your Aura instance.

1. In the [Aura console](https://console.neo4j.io/), find your instance ID under **Instances**, or select **...** > **Inspect** and copy its MCP server URL.
2. Replace `<instance-id>` in `.vscode/mcp.json` with your Aura instance ID.
3. Start the `neo4j-mcp` server from your editor's MCP server controls.
4. Authorize access when prompted, then open a new coding-agent chat so the tools are detected.

The resulting server URL uses this format:

```text
https://<instance-id>.mcp-instances.neo4j.io
```

### Neo4j GraphAcademy MCP

The GraphAcademy MCP server gives you access to Neo4j learning content.

1. Start the `neo4j-graphacademy` server from your editor's MCP server controls.
2. Authorize access when prompted.


### VS Code MCP Configuration

```json
{
	"servers": {
		"neo4j-mcp": {
			"type": "http",
			"url": "https://<instance-id>.mcp-instances.neo4j.io"
		},
		"neo4j-graphacademy": {
			"type": "http",
			"url": "https://mcp.graphacademy.neo4j.com/mcp"
		}
	},
	"inputs": []
}
```

### Neo4j Skills

Install [Neo4j Skills](https://github.com/neo4j-contrib/neo4j-skills):

```shell
npx skills add https://github.com/neo4j-contrib/neo4j-skills
```

### Neo4j Aura MCP Starter Prompt

> Use Neo4j Aura MCP to inspect my database schema and suggest three connected questions I can explore.

### Reset the Graph Model

```text
/clear-data-model
```

### Claude Code?

Install Claude Code on your workspace and ask your instructor for a key.

```
curl -fsSL https://claude.ai/install.sh | bash
```

Then add your MCP servers:

```
claude mcp add --transport http neo4j-graphacademy https://mcp.graphacademy.neo4j.com/mcp
claude mcp add --transport http neo4j-instance https://<instance-id>.mcp-instances.neo4j.io
```

## Need Data for Your Hack?

### Explore Neo4j Example Datasets

Not sure which data to use for your project? Neo4j provides a collection of ready-to-use example datasets that can help you start building and experimenting quickly.

The examples cover a range of graph use cases, including:

- Movies and recommendations
- Retail and product relationships
- Social networks
- Transportation and routing
- Fraud and financial investigations
- Knowledge graphs and connected data

You can use these datasets to explore graph data models, practice writing Cypher queries, test GraphRAG or agentic workflows, and prototype your hack without spending time preparing data from scratch.

Each example includes information about the data model and instructions for accessing or loading the dataset. Depending on the example, you may be able to use it through Neo4j Browser, GitHub, Neo4j Aura, or a public demo server.

Start with the [Neo4j example datasets](https://neo4j.com/docs/getting-started/appendix/example-data/).

You can also explore additional examples and prebuilt projects:

- [Neo4j Sandbox](https://sandbox.neo4j.com/)
- [Neo4j Graph Examples on GitHub](https://github.com/neo4j-graph-examples)
- [Neo4j GraphGists](https://neo4j.com/graphgists)

Some datasets and use cases may appear in more than one resource. Choose the format that best fits your workflow, explore the available nodes and relationships, and adapt the example to support your hackathon idea.

## Learn to Build with Neo4j

Continue learning and start building with these free Neo4j resources.

### [Neo4j GraphAcademy](https://graphacademy.neo4j.com/)

Neo4j GraphAcademy is your one-stop destination for free, hands-on courses. Learn everything from graph database fundamentals to advanced techniques for building applications with Neo4j.

### [Neo4j Aura](https://neo4j.com/product/auradb/)

Neo4j Aura is Neo4j's fully managed cloud service. With the free tier, you can start building immediately without worrying about installation, infrastructure, or database administration.

### [Neo4j Developer Center](https://neo4j.com/developer/)

Explore guides, examples, drivers, and resources for building Neo4j applications with your preferred programming language and technology stack.

### [Neo4j Documentation](https://neo4j.com/docs/)

Find detailed documentation for Neo4j products, tools, query languages, deployment options, and integrations.

### [Neo4j Community](https://community.neo4j.com/)

Have a question or want to connect with other developers? Join the Neo4j Community to exchange ideas, troubleshoot challenges, and learn from other graph practitioners.

### [Neo4j on YouTube](https://www.youtube.com/@neo4j)

Watch developer interviews, technical demonstrations, tutorials, event sessions, and recordings from Neo4j developer conferences.

## AlienMentor — Graph-Powered Daily Learning Coach

AlienMentor helps learners decide what to study next by combining their progress with prerequisite relationships in a knowledge graph, then using optional AI to explain, practise, and adapt. The app includes a 265-concept curriculum across nine tracks. Tracks progress through three tiers with a smaller set of prerequisite links; Thai dance and Muay Thai also offer separate foundations, intermediate, and advanced course goals.

### Architecture

- **Flask** serves the responsive browser interface and JSON API.
- **`curriculum.py`** contains the demo curriculum, graph-path selection rules, prerequisite status, and measured progress calculations.
- **`graph_store.py`** provides a deterministic in-memory demo store and a parameterized Neo4j store. Neo4j is used only when credentials are present and writes are explicitly enabled.
- **`coach_ai.py`** optionally calls OpenAI Chat Completions with a strict JSON schema. It passes only the selected concept, retrieved prerequisite records, linked resource, and learner level. The app validates the returned lesson and question before using them. Without a configured key or when generation fails, a labeled curated question and concept explanation are used.
- **`app.py`** validates requests, orchestrates the graph/coach flow, and serves health status. **`templates/`** and **`static/`** hold the interface.

The graph uses the existing app namespace `learnpath-ai` so existing AlienMentor graph records remain compatible. Labels include `Learner`, `LearningGoal`, `Concept`, `Resource`, `LearningActivity`, and `AssessmentResult`. Assessment results record the question, answer, score, correctness, and timestamp. Recommendations are rule-based over graph prerequisites and observed assessment results; AI-generated lesson text does not choose or invent graph edges.

### Run locally

1. Use Python 3.11 or newer.
2. Install dependencies: `python3 -m pip install -r requirements.txt`.
3. Start the app: `python3 app.py`.
4. Open <http://127.0.0.1:5000>.

No credentials are needed for the complete interactive demo flow. The UI labels the process-local mode as **Offline demo**; its progress resets when the process stops. For the automated test suite, run `python3 -m unittest discover -s tests -v`.

### Optional Neo4j connection

Copy `.env.example` to `.env`, then set `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, and `NEO4J_DATABASE` to your own database settings. `NEO4J_READ_ONLY` defaults to `true`; set it to `false` only when you intend to seed AlienMentor nodes and store learner results. The app uses idempotent `MERGE` operations and app-scoped uniqueness constraints. It refreshes only its own prerequisite and goal requirement links while preserving learner assessment history and unrelated graph data. If Neo4j is unavailable during startup or a request, the app switches to a clearly labeled demo fallback.

#### Seed directly from Aura Query

To load the curriculum without connecting the Flask app first, open `neo4j/seed_265.cypher`, copy its full contents into the Aura Console **Query** editor, and click **Run**. The script uses `MERGE` and only writes AlienMentor records tagged `app = 'learnpath-ai'`; it can be run again safely. It replaces only the app-owned prerequisite and goal requirement links to match the three-tier curriculum. It creates 265 concepts, the course goals, and their prerequisite/resource/requirement relationships, including three-tier Thai dance and Muay Thai pathways. This updated seed extends an existing 23-concept AlienMentor graph without duplicating its records. Start the app with your Aura environment variables and submit **Build my plan** to create the demo learner and selected goal. Shell commands such as `export NEO4J_URI=...` must be run in a terminal, never in Aura's Cypher Query editor.

The existing `.vscode/mcp.json` configures workshop MCP clients for editor use. The Flask application does not depend on MCP; it talks to Neo4j through the official Python driver.

### Optional AI generation

Set `OPENAI_API_KEY` in `.env` or your deployment environment to enable generated lesson explanations and practice questions. `OPENAI_MODEL` is optional and defaults to `gpt-4o-mini`. API requests are made only when a key is set; provider use may incur charges. The app never returns the model's expected answer to the browser, and falls back to curated practice if the request fails or its output does not validate. Answer checking uses the validated correct option and records the result; it does not use an AI judge.

### Deploy with Render

`render.yaml` describes an offline-demo web service. Push the project to a GitHub repository you control, create a Render Blueprint from it, and deploy. Check `/health` on the generated URL. To enable Neo4j or AI in deployment, add the relevant variables in Render's private environment settings; do not commit `.env`. The public demo uses one shared learner. Offline progress is process-local and can reset after restart; do not use real learner data without adding authentication and per-learner storage.

### Three-minute demo

1. **0:00–0:35 — Choose a mission.** Select “Become a Python data analyst,” Beginner, and 30 minutes. Show that the app is in Offline demo mode unless a live Neo4j connection is verified.
2. **0:35–1:10 — Follow the graph.** Point out the recommended Python foundation concept, linked resource, prerequisite state, and why it is selected.
3. **1:10–1:45 — Try a wrong answer.** Submit an incorrect option. The result is recorded and the coach recommends review of the same concept.
4. **1:45–2:20 — Show adaptation.** Submit the correct option. The latest correct result clears the immediate review and opens the next eligible graph concept. The observed average still shows both attempts, separately from the estimated mastery.
5. **2:20–3:00 — Show evidence and AI mode.** Open the progress and graph sections. Explain observed accuracy and goal-path mastery, estimated mastery, and whether the lesson is AI generated or curated fallback.

### Evidence and limitations

- Goal-path progress counts concepts with a recorded average of at least 70%; overall accuracy is calculated from saved answers. The latest incorrect answer triggers review, while a later correct answer permits progression. Mastery estimates use a labeled 50% prior and are not test results.
- The demo store and the configured sample learner are shared and are not multi-user authentication or private learner accounts.
- No Neo4j MCP tools, usable database connection, or OpenAI API key were available in this workspace, so live Neo4j and live model behavior have not been claimed. Demo routes and provider validation/fallback are covered by local tests.
