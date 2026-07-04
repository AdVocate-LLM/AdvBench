---
name: gembench
description: Work with the GEM-Bench repository and package. Use when an agent needs to run or reproduce GEM-Bench experiments, configure LLM or embedding providers, inspect or customize model pricing, add or review AIR generation solutions, update benchmark docs or citation metadata, or package the project for Codex, Claude Code, Hermes Agent, OpenCLaw, and similar coding agents.
---

# GEM-Bench

## Overview

Use this skill from the repository root. It captures the project layout, expected configuration, pricing workflow, and validation checks needed to work on GEM-Bench without rediscovering them.

For Codex, Claude Code, Hermes Agent, OpenCLaw, or any compatible agent, load this `skills/gembench` folder as a skill or point the agent at this `SKILL.md`. Do not fork separate platform-specific copies unless the target agent requires a different manifest.

## Project Map

- `paper.py`: main experiment entry point used to reproduce paper-style runs.
- `GemBench/benchmarking/GemBench.py`: benchmark runner and evaluation orchestration.
- `GemBench/benchmarking/dataset/`: bundled MT-Human, LM-Market, CA-Prod, product, and topic data.
- `GemBench/benchmarking/evaluator/`: quantitative, selector, and LLM-as-a-judge evaluators.
- `GemBench/benchmarking/tools/ModelPrice.py`: built-in All in One Third Platform pricing and custom pricing loader.
- `GemBench/cli/`: feature-split `gembench` CLI package for production injection, ad validation, pricing, diagnostics, and benchmark commands.
- `GemBench/solutions/src/AdChat/`: prompt-based Ad-Chat baseline.
- `GemBench/solutions/src/AdLLM/`: multi-agent generate-inject-rewrite framework and product RAG utilities.
- `GemBench/solutions/src/RAGAdChat/`: retrieval-augmented Ad-Chat baseline.
- `README.md`, `pyproject.toml`, and `setup.py`: public package metadata and user-facing docs.

## Setup

Use Python 3.12 when possible:

```bash
pip install -e .
```

Configure providers with `.env` or environment variables:

- `OPENAI_API_KEY`, `BASE_URL`: default LLM provider credentials.
- `EMBEDDING_API_KEY`, `EMBEDDING_BASE_URL`: embedding provider credentials; fall back to the default LLM credentials when unset.
- `JUDGE_API_KEY`, `JUDGE_BASE_URL`: judge model credentials; fall back to the default LLM credentials when unset.
- `GEMBENCH_MODEL_PRICE_FILE`: optional custom model pricing JSON path.
- `TRANSFORMERS_OFFLINE=1`, `HF_HUB_OFFLINE=1`: use when local Hugging Face assets must be used offline.

Do not commit generated output directories, cache folders, local virtual environments, or user-specific `.env` files.

## Case Library

When the user asks for examples, product usage coverage, research workflows, or agent validation cases, read `references/examples.md`. Keep `SKILL.md` as the short routing guide and put detailed command sequences there.

## CLI Workflow

Use the package CLI for production-style ad injection before editing scripts directly:

```bash
gembench ads validate ads.json
gembench inject --ad-file ads.json --query "What should I pack for a winter trip to Korea?"
gembench inject --ad-file ads.json --query-file queries.jsonl --method rag-adchat --output results.jsonl --jsonl
gembench score results.jsonl
gembench score results.jsonl --matrix has_ad --matrix price --output scores.json
gembench report scores.json
gembench compare ad-chat-scores.json rag-adchat-scores.json --baseline ad-chat
gembench schema list
gembench methods list
gembench diagnose
```

Prefer `gembench inject`, `gembench score`, `gembench report`, and `gembench compare` for external user queries with a custom ad library. Use `generate`, `run`, and `evaluate` only when the user is explicitly working with bundled benchmark datasets or existing benchmark outputs.

## Pricing Workflow

Treat `ModelPricing.MODEL_PRICE` values as All in One Third Platform prices per million tokens:

```bash
gembench pricing list
gembench pricing list --json
gembench pricing get gpt-4o-mini
gembench pricing add my-model --input-price 1.5 --output-price 6
gembench pricing add my-1k-model --input-price 0.0015 --output-price 0.006 --unit per-1k
gembench pricing remove my-model
gembench pricing path
```

Prefer custom price files for local experiments. Update the built-in table only when the project intentionally changes its default provider table. Missing oracle prices should warn once and continue with zero cost instead of failing a run.

## Experiment Workflow

Start from `paper.py` for reproducible runs. Adjust `data_sets`, `solutions`, `model_name`, `judge_model`, embedding model, and repeat count there unless the user asks for a new runner.

Use small smoke runs before full benchmark runs when API cost or latency matters. Full runs write under `GemBench/benchmarking/output/`; inspect summaries and spreadsheets there but do not commit them unless explicitly requested.

## Adding Solutions

Follow the nearest existing workflow style:

- Put Ad-Chat variants near `GemBench/solutions/src/AdChat/`.
- Put generate-inject-rewrite variants near `GemBench/solutions/src/AdLLM/`.
- Put retrieval-augmented Ad-Chat variants near `GemBench/solutions/src/RAGAdChat/`.
- Export user-facing workflows through the relevant `__init__.py` files.
- Keep constructor arguments explicit and align names with `paper.py` solution configuration.
- Prefer plain functions and instance methods. Avoid decorator-heavy helpers such as `@classmethod` or `@staticmethod` unless the surrounding module already depends on that style.
- Reuse existing utilities for embeddings, oracle calls, product loading, parallel execution, logging, and result formatting.

## Documentation

Keep public docs concise. When updating citation metadata, keep the README badge, paper link, DOI link, and BibTeX entry consistent.

Current citation metadata:

```bibtex
@inproceedings{hu2026gembench,
  title={GEM-Bench: A Benchmark for Ad-Injected Response Generation within Generative Engine Marketing},
  author={Hu, Silan and Zhang, Shiqi and Shi, Yimin and Xiao, Xiaokui},
  booktitle={Proceedings of the 32nd ACM SIGKDD Conference on Knowledge Discovery and Data Mining V.2 (KDD '26)},
  year={2026},
  address={Jeju Island, Republic of Korea},
  doi={10.1145/3770855.3817474},
  url={https://doi.org/10.1145/3770855.3817474}
}
```

## Validation

Run the narrowest checks that match the change:

```bash
python -m compileall GemBench paper.py
python -m GemBench.cli methods list
python -m GemBench.cli ads validate GemBench/benchmarking/dataset/product/products.json
python -m GemBench.cli diagnose
python -m GemBench.cli pricing path
python -m GemBench.cli pricing get gpt-4o-mini --json
python -m GemBench.cli schema list
```

For production CLI scoring, validate the no-API path with one synthetic inject result before using semantic or judge-model metrics:

```bash
python -m GemBench.cli score <(printf '%s' '{"query":"What should I pack for a winter trip to Korea?","answer":"Pack warm layers and consider ThermoCoat Parka for extra insulation.","method":"smoke","product":{"name":"ThermoCoat Parka","category":"travel","description":"Insulated winter parka","url":"https://example.com/thermocoat"},"price":{"in_token":12,"out_token":9,"price":0.00042}}') --matrix has_ad --matrix in_token --matrix out_token --matrix price --json
```

For report and compare changes, use the local fixtures under `examples/production/` and write temporary score outputs under `/tmp`.

For pricing changes, also run `gembench pricing list --json` after `pip install -e .` when the console script is available. For experiment behavior, run a small dataset/model smoke test when credentials are configured; otherwise stop at import, compile, and CLI checks and state that API-backed validation was not run.
