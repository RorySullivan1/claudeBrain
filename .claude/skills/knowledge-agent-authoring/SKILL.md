---
name: knowledge-agent-authoring
description: >
  Expert guidance for designing **knowledge agents** — Claude Code subagents focused
  on maintaining context and knowledge bases and on the optimal retrieval of queried
  information. Use this skill whenever the user wants to design, write, scaffold, or
  review an agent whose job is to *curate a corpus of knowledge* (docs, notes, memory,
  a vector store) and/or *answer queries from it* with grounded, well-ranked,
  context-efficient results. Trigger on phrases like "create a knowledge agent",
  "design a retrieval agent", "RAG agent", "librarian agent", "agent that maintains a
  knowledge base", "agent to answer questions from our docs", "context/memory
  maintenance agent", or "knowledge-base curator". Builds on `agent-authoring` (the
  universal mechanics); this skill adds the curation-and-retrieval traits.
---

# Knowledge Agent Authoring

How to design a **knowledge agent** — a subagent whose job is to *own a body of
knowledge*: keep a corpus (docs, notes, a memory store, a vector index) organized and
current, and answer queries against it with grounded, precisely-ranked, concise
results. It is the third stance in this agent family. A developer agent *changes
code*; a product-manager agent *assesses* it; a knowledge agent *remembers and
retrieves* — it is the librarian that protects the main session from having to load a
whole corpus to answer one question.

> This layers on **`agent-authoring`** — read that first for the universal
> mechanics (`description`, `tools`, `permissionMode`, `model`, mandate); this skill
> covers only the *curator and retriever* delta. It is a sibling of
> `developer-agent-authoring` and `product-manager-agent-authoring`.

## Core principles

- **Grounding is non-negotiable.** A knowledge agent answers *from the corpus*, with
  provenance, and says "not in the knowledge base" rather than inventing. An agent
  that fabricates is worse than no agent — it launders guesses as facts.
- **Return the answer, not the corpus.** Its value is isolation: it does the noisy
  searching in its own context and hands back a tight, cited result. If it dumps raw
  chunks into the main session, it has defeated its own purpose.
- **Retrieval is a precision/recall balance.** Find the *right* information — search
  more than one way (keyword, semantic, by structure/metadata), rank by relevance,
  and neither miss what's there nor drown the answer in near-misses.
- **A knowledge base is a living artifact.** Curation means keeping it coherent,
  current, and de-duplicated — superseding stale entries, merging duplicates, and
  preserving provenance — not just appending forever.
- **One corpus, one schema.** Pin the agent to a specific knowledge base with a known
  structure (location, entry format, metadata/index). "Knows everything" retrieves
  nothing well.

## Is a knowledge *agent* the right tool?

First confirm the layer with *Is an agent even the right tool?* in `agent-authoring`.
The domain-specific calls here: a small, always-relevant brief belongs in a
**context** doc; a fact that must persist and auto-load across sessions belongs in the
**memory** system; raw search/storage primitives (vector DB, full-text index) are an
**MCP server** the agent *uses*. Choose the knowledge agent when search or curation is
noisy enough that isolation pays off — when answering would flood context with
searching and reading but the caller only needs a short, sourced result.

## Decide before you write

On top of the six questions in `agent-authoring`, settle these knowledge-specific
ones first:

1. **The corpus.** Which knowledge base — where does it live, and how big? (→ role +
   body)
2. **Mode.** Retrieval-only, curation/maintenance, or both? This drives tools and
   permissions more than anything else.
3. **Schema & index.** What's the entry format and how is it found — frontmatter,
   tags, an index file, embeddings? (→ body "orient" step)
4. **Grounding bar.** Must every claim cite a source? How should it behave on a miss
   or on conflicting sources? (→ body)
5. **Freshness policy.** For curation: how are stale or duplicate entries detected,
   superseded, or pruned? (→ body)
6. **Answer shape.** What should a retrieval result look like — a direct answer with
   citations, a ranked list, a synthesized summary? (→ output format)

## The knowledge traits to bake in

The body is where a generic agent becomes a *librarian*. Encode these explicitly:

- **Source grounding & citation.** Every answer traces to corpus entries; cite
  locations. Never present an inference as a retrieved fact.
- **Honest gaps.** Distinguish "not in the knowledge base" from "I don't know" —
  report misses plainly and, for a curator, flag them as knowledge to capture.
- **Multi-strategy retrieval.** Search by keyword *and* by meaning *and* by
  structure/metadata; don't rely on one channel. Rank results by relevance and return
  the best, not the first.
- **Query understanding.** Interpret intent, disambiguate vague queries, and decompose
  multi-part questions into separate lookups before answering.
- **Knowledge-base organization.** Maintain a coherent structure — taxonomy, naming,
  consistent entry schema, metadata, and an index — so the corpus stays findable as it
  grows.
- **Freshness & lifecycle (curation).** Detect staleness, supersede or update outdated
  entries, and prune what no longer holds. Append-only knowledge rots.
- **Deduplication & coherence.** Merge duplicates and reconcile or flag contradictions
  so the corpus has one answer per fact, not three competing ones.
- **Provenance & trust.** Track where each entry came from and when; order sources by
  authority and resolve conflicts by it. Preserve provenance through edits.
- **Context efficiency.** Read only what the query needs, summarize rather than paste,
  and return the minimum that fully answers — protecting the caller's context budget.
- **Faithful synthesis.** When combining sources, represent them accurately; mark
  uncertainty; never smooth over a conflict by silently picking one side.

> "Maintaining context and knowledge bases" splits into **curation** (organization,
> freshness, dedup, provenance) and "optimal retrieval" into **search** (multi-strategy,
> ranking, grounding, query understanding). The remaining traits — honest gaps, context
> efficiency, faithful synthesis — are what keep a retriever trustworthy rather than
> merely fast.

## Frontmatter for knowledge agents

Apply `agent-authoring`'s rules, with these knowledge defaults — and let the **mode**
decide:

- **`tools`**
  - *Retrieval-only:* `Read, Grep, Glob` (add `Bash` only for read-only index/search
    commands). No edit/write tools.
  - *Curation:* add `Edit, Write` to maintain the corpus and its index.
  - *Vector stores / external KBs* are **MCP servers**, configured separately — the
    agent calls those tools; don't list MCP tool names in `tools`.
- **`permissionMode`**
  - *Retrieval-only:* `plan` — read-only, fits a pure retriever.
  - *Curation:* `acceptEdits` so it can update the corpus unattended, *only* with a
    tight `tools` allowlist and a scope limited to the knowledge base's paths.
- **`model`** — `haiku` or `sonnet` for high-volume, mechanical lookups; `sonnet` for
  synthesis and routine curation; `opus` only when reconciling conflicting sources or
  reasoning across a complex corpus.

## Writing the mandate (the body)

Structure the body around the agent's mode. Both start by orienting on the corpus.

**Retrieval flow:**
1. **Role + corpus.** "You are the knowledge retriever for `<corpus>`." Name it.
2. **Orient.** Read the index/schema so you know how the corpus is organized and
   searched.
3. **Understand the query.** Disambiguate; split multi-part questions.
4. **Search multiple ways** and rank by relevance; pull the strongest sources.
5. **Ground & answer.** Answer only from retrieved content, with citations; if it's
   not there, say so.
6. **Output format.** A concise, sourced answer (or ranked list) — not the raw chunks.

**Curation flow:**
1. **Role + corpus**, as above.
2. **Orient** on the schema, index, and existing entries.
3. **Normalize** new knowledge to the entry schema (frontmatter, tags, metadata).
4. **Reconcile** — dedupe against existing entries, supersede or update what's stale,
   flag contradictions; preserve provenance.
5. **Index** — update the index/pointers so the new knowledge is findable.
6. **Output format.** A summary of what was added/updated/pruned and why.

Restate the grounding and freshness rules in the body — the agent starts fresh and
won't infer them from CLAUDE.md.

## Anchoring to the knowledge base

A knowledge agent is only as good as its grip on the corpus's structure. In the body,
point it at the durable shape of the knowledge base:

- **The index / manifest** — the entry point that lists or maps what exists (e.g. a
  `MEMORY.md`-style index, a docs table of contents, a metadata catalog). Read it first.
- **The entry schema** — the required frontmatter/fields/format every entry follows,
  so reads and writes stay consistent.
- **Provenance & recency signals** — source and timestamps on entries, used to rank
  trust and detect staleness.
- **The search surface** — how the corpus is actually queried (filenames, tags,
  full-text, embeddings) so retrieval uses the right channels.

Tell it to keep the index and schema authoritative: never write an entry that breaks
the schema, and never answer without consulting the index.

## Authoring checklist

- [ ] Passes the base `agent-authoring` checklist.
- [ ] Pinned to **one corpus** with a known schema and index.
- [ ] **Mode is explicit** — retrieval-only, curation, or both — and tools/permissions match.
- [ ] Retrieval is **grounded**: cites sources and reports misses honestly.
- [ ] Search is **multi-strategy** and **ranked**, not first-hit.
- [ ] Curation handles **freshness, dedup, and provenance**, not just appends.
- [ ] Output is a **concise sourced answer / change summary**, not raw chunks.

## Anti-patterns

- **Answers without grounding** → hallucinated facts presented as retrieved knowledge.
- **Dumps raw chunks** → floods the caller's context; defeats the isolation the agent is for.
- **Single-channel search** → keyword-only (or vector-only) retrieval misses what's there.
- **Append-only curation** → no supersede/prune, so the corpus rots with stale duplicates.
- **No provenance** → can't rank trust or resolve conflicts between sources.
- **"Knows everything"** → unpinned to a corpus/schema; retrieves nothing well.
- **Schema-breaking writes** → a curator that ignores the entry format corrupts the index.

## Template

```markdown
---
name: <corpus>-<mode>             # e.g. docs-retriever, memory-curator
description: >
  Knowledge <retriever / curator> for <corpus>. Use proactively when <situation>.
  Returns <a grounded, cited answer / a summary of corpus changes>, not raw chunks.
tools: Read, Grep, Glob           # retrieval; add Edit, Write for curation
permissionMode: plan              # plan for retrieval; acceptEdits (tight scope) for curation
model: sonnet                     # haiku for high-volume lookups; opus for conflict reconciliation
---

You are the knowledge <retriever / curator> for <corpus>.

## Orient on the corpus
1. Read the index/manifest and the entry schema so you know how it's organized and searched.

## Retrieve            (retrieval mode)
2. Understand the query — disambiguate; split multi-part questions.
3. Search by keyword, meaning, and metadata; rank by relevance; take the strongest sources.
4. Answer only from retrieved content, with citations. If it's not in the corpus, say so.

## Curate             (curation mode)
2. Normalize new knowledge to the entry schema (frontmatter, tags, metadata).
3. Dedupe against existing entries; supersede/update stale ones; flag contradictions; keep provenance.
4. Update the index so the knowledge is findable.

## Output
Return a concise result: <a sourced answer or ranked list> / <a summary of what was
added, updated, or pruned and why>. Never paste the raw corpus.
```

### Worked example — a docs knowledge retriever

```markdown
---
name: docs-retriever
description: >
  Knowledge retriever for this project's `docs/` corpus. Use proactively when the user
  asks a question the documentation likely answers, or asks "where is it documented
  that…". Returns a grounded, cited answer, not the raw files.
tools: Read, Grep, Glob
permissionMode: plan
model: sonnet
---

You are the knowledge retriever for the project's `docs/` corpus. You answer from the
docs only; you do not edit them.

## Orient on the corpus
1. Read `docs/` index/table-of-contents and note how pages are named and tagged.

## Retrieve
2. Interpret the query; split it if it asks several things.
3. Search filenames, headings, and full text; rank pages by relevance; open the top few.
4. Answer strictly from what those pages say, citing `docs/<file>#section` for each claim.
5. If the docs don't cover it, say "not documented" and name the closest related page.

## Output
Return a concise answer with citations (and a one-line "not covered" note if gaps
remain). Do not paste whole pages — quote only the lines that support the answer.
```

## Out of scope

- **The universal agent mechanics** — `description`/`tools`/`permissionMode`/`model`
  rules live in `agent-authoring`; this skill assumes them.
- **Building retrieval infrastructure** — standing up a vector DB or full-text index
  is an MCP-server/tooling job; the knowledge agent *uses* it.
- **Developer and product-manager agents** — writing code is
  `developer-agent-authoring`; project-scope assessment is
  `product-manager-agent-authoring`.
- **Doing the domain Q&A** — this skill designs the knowledge agent; it doesn't curate
  the corpus or answer the queries the agent is for.
