# LangGraph Orchestrator — orchestrator/

This package contains the LangGraph state machine that orchestrates all analysis agents.

## Responsibilities

- Define the agent graph (nodes = agents, edges = data flow)
- Run MVP agents in parallel branches
- Collect findings from all agents
- Invoke the synthesis LLM pass (gemini-2.5-pro) to write the narrative report
- Assemble and persist the final IntegrityReport

## Graph Overview

```
START
  └─► [parallel fan-out]
        ├── statistical_integrity
        ├── citation_verifier
        └── plain_language_summary
  └─► [fan-in / merge findings]
  └─► synthesis_pass (gemini-2.5-pro)
  └─► persist_report
END
```
