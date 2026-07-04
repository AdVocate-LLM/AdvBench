# GEM-Bench Cases

Use these cases when a user asks how to use GEM-Bench as a product, a research tool, or an agent-ready package. Prefer the production cases for external user queries. Use benchmark cases only for paper-style experiments or existing `SolutionResult` files.

## Case 1: Validate Production Scoring Without API

Goal: prove the installed package can score external-query results without provider credentials or network calls.

```bash
python -m GemBench.cli score <(printf '%s' '{"query":"What should I pack for a winter trip to Korea?","answer":"Pack warm layers and consider ThermoCoat Parka for extra insulation.","method":"smoke","product":{"name":"ThermoCoat Parka","category":"travel","description":"Insulated winter parka","url":"https://example.com/thermocoat"},"price":{"in_token":12,"out_token":9,"price":0.00042}}') --matrix has_ad --matrix in_token --matrix out_token --matrix price --json
```

Expected result: `has_ad` is `100`, token metrics match the input price object, and no embedding or judge model is called.

## Case 2: Run External Queries With a Custom Ad Library

Goal: use GEM-Bench as a production-style ad injection CLI.

`ads.json`:

```json
[
  {
    "name": "ThermoCoat Parka",
    "description": "Insulated winter parka for cold travel days",
    "category": "travel",
    "url": "https://example.com/thermocoat"
  },
  {
    "name": "PackLite Organizer",
    "description": "Compression packing cube for carry-on luggage",
    "category": "travel",
    "url": "https://example.com/packlite"
  }
]
```

`queries.jsonl`:

```jsonl
{"query":"What should I pack for a winter trip to Korea?"}
{"query":"How do I fit winter clothes into a carry-on?"}
```

Commands:

```bash
python -m GemBench.cli ads validate ads.json
python -m GemBench.cli inject --ad-file ads.json --query-file queries.jsonl --method rag-adchat --output results.jsonl --jsonl
python -m GemBench.cli score results.jsonl --matrix has_ad --matrix price --output scores.json
python -m GemBench.cli report scores.json
```

Use `--method ad-chat`, `--method gi-r`, `--method gir-r`, or `--method gir-p` when comparing injection strategies.

## Case 3: Score Semantic Or Judge Metrics Intentionally

Goal: run cost-bearing metrics only when the user asks for them.

```bash
python -m GemBench.cli score results.jsonl --matrix local_flow --matrix global_coherence --output semantic-scores.json
python -m GemBench.cli score results.jsonl --matrix naturalness_evaluation --matrix trust_evaluation --judge-model gpt-4.1-mini --output judge-scores.json
```

Semantic metrics require embedding configuration. Judge metrics require judge-model credentials. If credentials are missing, run `python -m GemBench.cli diagnose` before retrying.

## Case 4: Customize Model Pricing

Goal: make runtime cost accounting match the user's provider table.

```bash
python -m GemBench.cli pricing path
python -m GemBench.cli pricing get gpt-4o-mini
python -m GemBench.cli pricing add my-provider-model --input-price 1.5 --output-price 6
python -m GemBench.cli pricing add my-1k-model --input-price 0.0015 --output-price 0.006 --unit per-1k
python -m GemBench.cli pricing list --custom-only --json
```

Prefer `--price-file path/to/model_prices.json` or `GEMBENCH_MODEL_PRICE_FILE` for project-specific experiments. Missing model prices should warn and continue with zero cost.

## Case 5: Compare Production Methods

Goal: compare two or more scored production result files.

```bash
python -m GemBench.cli score examples/production/results-ad-chat.jsonl --output /tmp/ad-chat-scores.json
python -m GemBench.cli score examples/production/results-rag-adchat.jsonl --output /tmp/rag-adchat-scores.json
python -m GemBench.cli report /tmp/rag-adchat-scores.json --detail
python -m GemBench.cli compare /tmp/ad-chat-scores.json /tmp/rag-adchat-scores.json --baseline ad-chat
python -m GemBench.cli compare /tmp/ad-chat-scores.json /tmp/rag-adchat-scores.json --matrix has_ad --format json
```

Use `report` for one run and `compare` for method-level deltas across runs.

## Case 6: Inspect Schemas

Goal: answer integration questions without reading CLI code.

```bash
python -m GemBench.cli schema list
python -m GemBench.cli schema show ad-library --json
python -m GemBench.cli schema show inject-result --json
python -m GemBench.cli schema show score-output --json
```

Use `docs/cli-schemas.md` for the human-facing schema reference and `examples/production/` for local fixtures.

## Case 7: Research Baseline Comparison

Goal: reproduce or compare built-in methods on bundled datasets.

```bash
python -m GemBench.cli methods list
python -m GemBench.cli datasets list
python -m GemBench.cli generate --baseline ad-chat --dataset MT-Human --max-samples 3 --tag smoke-adchat
python -m GemBench.cli evaluate GemBench/benchmarking/output/<run>/results.json --matrix has_ad --matrix price
```

Use `run` only when the user wants generation plus evaluation in one benchmark job. For external product workflows, use `inject` and `score` instead.

## Case 8: Agent Forward Test

Goal: verify that Codex, Claude Code, Hermes Agent, OpenCLaw, or a similar agent can use the skill without extra explanation.

Prompt:

```text
Use $gembench. In this GEM-Bench workspace, do not modify files. Validate the production CLI path with safe local checks only: compile GemBench/cli, show score help, and run one no-API score smoke on a single JSON record. Report commands and results.
```

Expected agent behavior:

- Reads `SKILL.md` and, if needed, this examples reference.
- Chooses `inject -> score` as the production path.
- Runs no-API scoring before any semantic or judge-model metric.
- Leaves `git status --short` clean except for pre-existing user changes.

## Case 9: Add A New AIR Method

Goal: extend GEM-Bench with a new ad-injected response method.

Implementation pattern:

1. Put the workflow next to the closest existing method under `GemBench/solutions/src/`.
2. Export it through the nearest `__init__.py`.
3. Add the method key, aliases, and task support in `GemBench/cli/constants.py`.
4. Register callable construction in `GemBench/cli/benchmark.py` and production invocation in `GemBench/cli/inject.py`.
5. Add narrow validation: import/compile, `methods list`, one no-API score smoke, and a small API smoke only when credentials and budget are available.

Keep constructors explicit, use plain functions or instance methods, and match the existing docstring style.
