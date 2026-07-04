# GEM-Bench CLI Schemas

This document covers the production CLI data shapes. Use benchmark `results.json` only with `gembench evaluate`; use the shapes below with `gembench inject`, `gembench score`, `gembench report`, and `gembench compare`.

## Ad Library

`gembench inject --ad-file ads.json` accepts a list of product objects:

```json
[
  {
    "name": "ThermoCoat Parka",
    "description": "Insulated winter parka for cold travel days",
    "category": "travel",
    "url": "https://example.com/thermocoat"
  }
]
```

Required field: `name`.

Optional fields: `description`, `desc`, `category`, `url`, `link`.

The loader also accepts the existing benchmark product-table shapes: a flat object with `names`, `descriptions` or `descs`, and `urls`, or a category-keyed object containing those arrays.

## Query File

`gembench inject --query-file queries.jsonl` accepts one object per line:

```jsonl
{"query":"What should I pack for a winter trip to Korea?"}
{"prompt":"How do I fit winter clothes into a carry-on?"}
```

Use one of `query`, `prompt`, or `question`.

## Inject Result

`gembench inject --jsonl` emits records shaped like:

```json
{
  "method": "rag-adchat",
  "query": "What should I pack for a winter trip to Korea?",
  "answer": "Pack thermal layers and a windproof outer layer.",
  "product": {
    "name": "ThermoCoat Parka",
    "description": "Insulated winter parka for cold travel days",
    "category": "travel",
    "url": "https://example.com/thermocoat"
  },
  "price": {
    "in_token": 124,
    "out_token": 42,
    "price": 0.0014
  }
}
```

`gembench score` also accepts compatible external records with `prompt`, `question`, `response`, or `content` aliases.

## Score Output

`gembench score --json` and `gembench score --output scores.json` write:

```json
{
  "summary": [
    {
      "method": "rag-adchat",
      "matrix": "has_ad",
      "count": 2,
      "average": 100.0,
      "min": 100.0,
      "max": 100.0
    }
  ],
  "scores": [
    {
      "method": "rag-adchat",
      "dataset": "External",
      "repeat_id": "0",
      "matrix": "has_ad",
      "category": "travel",
      "query": "What should I pack for a winter trip to Korea?",
      "answer": "Pack thermal layers and a windproof outer layer.",
      "product": {
        "name": "ThermoCoat Parka",
        "description": "Insulated winter parka for cold travel days",
        "category": "travel",
        "url": "https://example.com/thermocoat"
      },
      "score": 100.0
    }
  ]
}
```

Use `gembench report scores.json` for a compact table, `gembench report scores.json --detail` for per-query rows, and `gembench compare scores-a.json scores-b.json --baseline ad-chat` for method-level deltas.

## Local Example

```bash
python -m GemBench.cli ads validate examples/production/ads.json
python -m GemBench.cli score examples/production/results-rag-adchat.jsonl --output /tmp/rag-score.json
python -m GemBench.cli score examples/production/results-ad-chat.jsonl --output /tmp/ad-score.json
python -m GemBench.cli report /tmp/rag-score.json
python -m GemBench.cli compare /tmp/ad-score.json /tmp/rag-score.json --baseline ad-chat
```
