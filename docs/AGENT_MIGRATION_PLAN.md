# Agent Layer Migration Plan: Toward a Config-Driven, Agnostic Architecture

## 1. Purpose

The data ingest pipelines were migrated to a generic orchestrator/worker pattern:
code is dataset-agnostic, and per-dataset behavior (fetch logic, sink table,
write mode, checkpointing) lives entirely in config files and small
`extract.ipynb` notebooks that each expose the same `ingest_data`/`update_config`
contract. This document plans the equivalent migration for the agentic layer:
make agents, tools, models, and orchestration topology configurable instead of
hardcoded, so adding a new agent, swapping a model provider, or wiring in a new
tool requires editing config, not Python.

## 2. Current State

- **`config/agent_configs.yaml`** and **`config/mcp_tools.yaml`** already
  describe a 3-level agent hierarchy (orchestrator → supervisors → workers),
  per-agent models, tools, and an MCP server/tool/access-control model. This
  schema is a reasonable starting point.
- **Nothing reads either file.** There is no loader, no agent factory, no code
  path that turns this YAML into running agents.
- **`notebooks/8-multiagent.ipynb`** is the only executable agent code. It is a
  linear, hand-written LangGraph tutorial: every agent, tool binding, prompt,
  and graph edge is hardcoded Python, repeated per example (single supervisor,
  then a 2-team hierarchy). Nothing in it is reusable or driven by config.
- **Provider is hardcoded to OpenAI**: `init_chat_model("openai:gpt-4o-mini")`,
  `OPENAI_API_KEY`, `OpenAIEmbeddings`. `agent_configs.yaml` lists a stray
  Claude model for one worker that the code could never honor.
- **Tools are hardcoded per cell** (`TavilySearch`, a local FAISS retriever,
  `WikipediaQueryRun`, inline `@tool` functions) rather than assembled from
  `mcp_tools.yaml`'s server/tool/access-control definitions.
- **`src/mcp_servers/*`**, which `mcp_tools.yaml` points `command`/`args` at,
  **does not exist**. There is no `src/` directory in the repo at all.
- A live Tavily API key is committed in plaintext in the notebook
  (`os.environ["TAVILY_API_KEY"]="tvly-..."`) — a secret-hygiene issue,
  independent of the agnosticism problem, called out here so it isn't lost.

**Net effect**: the config schema and the runnable code are two disconnected
artifacts. Today, 0% of agent behavior is actually driven by config.

## 3. Target Architecture

Mirror the ingest pipeline's shape:

| Ingest concept | Agent-layer equivalent |
|---|---|
| `orchestrator.ipynb` (generic, dataset-agnostic) | `src/agents/factory.py` — generic, agent-agnostic builder |
| `extract.ipynb` per dataset (`ingest_data`, `update_config`) | one small module per agent role exposing a fixed contract (tools, prompt, model) |
| `config/data_ingest/*.json` (triggers) | `config/agent_configs.yaml` (already exists, needs to become load-bearing) |
| `worker.ipynb`'s `mode`/`sink_table` contract | `mcp_tools.yaml`'s `access_control` contract, actually enforced |

Concretely:

1. **A provider-agnostic model loader.** A single function,
   `get_model(model_name: str, **kwargs)`, that maps a config string
   (`"gpt-4o-mini"`, `"claude-3-haiku-20240307"`, `"claude-sonnet-5"`, ...) to
   the right LangChain chat model class and required env var, so
   `agent_configs.yaml` can mix providers per agent as it already declares it
   wants to. New provider = one entry in a lookup table, not a new notebook.

2. **A tool registry keyed by name**, populated from `mcp_tools.yaml`'s
   `servers.*.tools[].name`. Each tool name maps to a Python callable/`Tool`/
   MCP client binding. Agents never import a tool directly — they ask the
   registry for the names listed in their config entry
   (`workers.<name>.tools`), and the registry enforces
   `access_control.<agent>.allowed_servers` at build time (an agent config
   listing a tool it isn't allowed to use should fail fast, not silently
   grant access).

3. **An agent/graph factory** that reads `agent_configs.yaml` and builds the
   LangGraph `StateGraph` generically: for each `workers:` entry, build a
   `create_react_agent(model, tools, prompt)`; for each supervisor, build a
   supervisor node whose `members` and `coordination_strategy` come from
   config (parallel/sequential/parallel-then-aggregate map to distinct but
   reusable node-wiring functions, not copy-pasted graphs per example). The
   orchestrator level (`human_approval_threshold`, `max_replanning_iterations`)
   becomes the top-level graph entry, also config-built.

4. **Prompts as data, not string literals in Python.** Move the `prompt:`
   text out of Python f-strings into either a `prompts/` directory (one file
   per agent, referenced by name from `agent_configs.yaml`) or a `prompt` key
   directly in the YAML for short ones — consistent with how `extract.ipynb`
   keeps dataset specifics out of the generic orchestrator.

5. **The actual `src/mcp_servers/*` implementations.** `mcp_tools.yaml`
   already specifies the tool surface (`get_stock_price`, `search_filings`,
   `query_graph`, `calculate_ratios`, `search_documents`, ...); these need to
   exist as real MCP servers (or, as an intermediate step, as plain Python
   functions registered directly in the tool registry, deferring true MCP
   process-per-server until it's needed).

## 4. Migration Phases

Phased so each step is independently shippable and testable, same spirit as
the ingest migration (stub first, wire incrementally, confirm behavior at
each step before moving on).

**Phase 0 — Hygiene (do first, low risk)**
- Rotate and remove the hardcoded Tavily key from `8-multiagent.ipynb`; move
  all API keys to `dbutils.secrets`/`.env`, consistent with how the ingest
  notebooks pull the FRED key from `dbutils.secrets`.

**Phase 1 — Model loader**
- Add `src/agents/models.py` with `get_model(model_name, **kwargs)` covering
  at least OpenAI and Anthropic (the two providers already implied by
  `agent_configs.yaml`).
- No behavior change yet — just makes provider selection a function of a
  string instead of a hardcoded import.

**Phase 2 — Tool registry**
- Add `src/agents/tools.py`: a registry populated by reading
  `mcp_tools.yaml`, initially backed by direct Python implementations for
  each tool (Tavily search, FAISS retriever, the `add`/`multiply`/`divide`
  math tools, etc. — largely lifted from the existing notebook), not yet
  real MCP subprocess servers.
- Enforce `access_control` here: `get_tools_for_agent(agent_name)` raises if
  a config-listed tool isn't in `allowed_servers`.

**Phase 3 — Single-agent factory**
- Add `src/agents/factory.py::build_worker(name)` that reads one
  `workers.<name>` entry from `agent_configs.yaml` and returns a
  `create_react_agent` built from `get_model` + `get_tools_for_agent`. Port
  one existing notebook agent (e.g. `research_agent`) to this factory as a
  proof of concept, verify identical behavior.

**Phase 4 — Supervisor factory**
- Add `build_supervisor(name)` handling the three `coordination_strategy`
  values already in the config (`parallel_with_timeout`,
  `sequential_with_dependencies`, `parallel_then_aggregate`) as distinct,
  reusable graph-wiring strategies. Port one supervisor (e.g.
  `news_supervisor` with its 4 workers) end-to-end.

**Phase 5 — Full graph + orchestrator**
- Add `build_graph()` that assembles the whole 3-level hierarchy from
  `agent_configs.yaml` in one call, including the orchestrator's
  `human_approval_threshold`/`max_replanning_iterations` behavior.
- Retire `8-multiagent.ipynb`'s hardcoded graphs in favor of a thin notebook
  that just calls `build_graph()` and invokes it — same shape as the ingest
  `orchestrator.ipynb` being a thin, generic caller.

**Phase 6 — Real MCP servers (optional/later)**
- Once the tool registry's direct-Python tools are stable, migrate each to
  an actual MCP server process under `src/mcp_servers/`, matching
  `mcp_tools.yaml`'s `command`/`args`/`env`/`cache` fields. This phase is
  separable and not required for "config-driven," only for the literal MCP
  protocol `mcp_tools.yaml` already assumes.

## 5. Config Changes Needed Along the Way

- `agent_configs.yaml`: add a `prompt` (or `prompt_file`) key per agent —
  currently prompts exist only as Python strings in the notebook and have no
  config representation at all.
- `agent_configs.yaml`: normalize `model` values against whatever key
  `get_model` expects (decide once: raw provider-prefixed strings like
  `"openai:gpt-4o-mini"` vs. the current bare `"gpt-4o"` plus an inferred
  provider — recommend keeping explicit `provider`/`model` as two fields to
  avoid inference bugs).
- `mcp_tools.yaml`: no structural change needed for Phases 1-5; it already
  has the right shape (`servers`, `tools`, `access_control`). Phase 6 is
  where its `command`/`args`/`env` fields become load-bearing.

## 6. Non-Goals (For Now)

- Not migrating away from LangGraph — the goal is removing hardcoding, not
  changing frameworks.
- Not standing up real MCP server processes before Phase 6 — an in-process
  tool registry gets the "configurable" goal met sooner with less
  infrastructure risk.
- Not designing a UI/API for editing configs — this plan only covers making
  the YAML load-bearing, not building tooling around it.

## 7. Open Questions

- Should `human_approval_threshold` gating be implemented as a LangGraph
  interrupt, or handled outside the graph (e.g. a Databricks job approval
  gate)? Affects Phase 5 design.
- Where should prompt files live relative to `notebooks/` vs. a new `src/`
  tree — needs a decision before Phase 4 to avoid churn.
- Confirm whether `sentiment_worker`'s existing Claude model entry in
  `agent_configs.yaml` is intentional (mixed-provider by design) or a
  leftover — affects whether Phase 1 needs to support provider mixing from
  day one or can start OpenAI-only.
