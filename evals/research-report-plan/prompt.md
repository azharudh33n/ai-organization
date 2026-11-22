---
tags: [ai-organization]
max_turns: 40
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit]
---

Use the ai-organization skill to plan this. Dry run: produce the planning artifacts up to and including the work plan, then stop. Don't browse the web or install anything; mark any skill choice 'to verify'.

PROJECT: decide between Qdrant, pgvector and Weaviate for our customer-support RAG chatbot. About 5 million chunks, 1024-dim embeddings, self-hosted on a single 32 GB VPS, p95 query latency budget 150 ms.
DELIVERABLES: a recommendation report for our CTO, plus a reproducible benchmark script.
AUDIENCE: CTO and two backend engineers.
