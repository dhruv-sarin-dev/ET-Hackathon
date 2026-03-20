# NexusGraph Architecture

NexusGraph shifts away from unstructured "chatting" agents toward an enterprise-grade deterministic Multi-Agent workflow, utilizing a central state ledger.

## Multi-Agent Roles

### 1. The Signal Agent (`main.py`)
- **Role:** The "Eyes and Ears" of the supply chain.
- **Function:** Ingests live news, IoT alerts, and supply chain updates as natural language or unstructured text. Uses Google Gemini 1.5 Flash (via LangChain) to syntactically map these natural events to explicit, pre-defined spatial nodes in the network (e.g., "Supplier Alpha", "Factory Prime").
- **Output:** A strict Pydantic `DisruptionReport` array.

### 2. The Graph Engine (`graph_engine.py`)
- **Role:** The "Deterministic Brain".
- **Function:** Holds the mathematically sound topology of the 3-tier supply chain. When an event fires, it removes nodes, models "blast radius" cascading failures (e.g., a Retailer starved of deliveries), and instantly computes the globally optimal `new_path` via Dijkstra's shortest-path algorithm.

## Zero-Hallucination Ledger (`nexus_state.json`)
To satisfy strict industrial reliability:
- Agents **MUST NOT** pass data via natural language buffers.
- The Signal Agent writes to `nexus_state.json`. The Graph Engine reads from `nexus_state.json`. 
- This ledger functions as the undeniable single source of truth across the pipeline. If a node fails, its absence is verified in the JSON structural tree, eliminating conversational context loss.

## Enterprise Hardening & Fallbacks (Phase 6)
- **Hallucination Absorption:** If the LLM generates an invalid Node ID (not present in `VALID_NODES`), `main.py` explicitly catches and discards the mapping, preventing fatal runtime crashes and logging a standard `WARNING`.
- **Absolute Isolation Handling:** If a disruption completely severs a downstream node (e.g., loss of all Distribution Centers to a given Retailer), `graph_engine.py` deterministically traps the `nx.NetworkXNoPath` violation, classifies it as a critical `NO_ROUTE_AVAILABLE`, and gracefully moves to the next node.
- **Telemetry:** Comprehensive native python `logging` maps all inter-agent operations systematically.
