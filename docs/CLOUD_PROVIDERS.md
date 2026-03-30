# Cloud Provider Support — Implementation Plan

This document describes the design and implementation of Claude (Anthropic) and OpenAI support added to Oracle alongside the existing Ollama (local) backend.

---

## Overview

Oracle now supports three LLM backends:

| Provider   | Model prefix      | Auth                  |
|------------|-------------------|-----------------------|
| **Ollama** | anything else     | None (local)          |
| **Claude** | `claude-*`        | `ANTHROPIC_API_KEY`   |
| **OpenAI** | `gpt-*`, `o1*`, `o3*`, `o4*` | `OPENAI_API_KEY` |

The backend is selected automatically from the `--model` flag — no extra flags needed.

```bash
# Ollama (existing behaviour, unchanged)
oracle ask "What is this error?" --model qwen3.5:4b

# Claude
oracle ask "Summarise this window" --model claude-sonnet-4-6

# OpenAI
oracle ask "Explain this code" --model gpt-4o
```

---

## Architecture

### New files

```
oracle/llm/
├── base_client.py      Abstract base class shared by all three clients
├── claude_client.py    Anthropic SDK client
├── openai_client.py    OpenAI SDK client
└── llm_factory.py      Factory: picks the right client from the model name
```

### Modified files

| File | Change |
|------|--------|
| `oracle/main.py` | Replace `OllamaClient` import with `create_llm_client` factory; update help text and spinner labels |
| `pyproject.toml` | Add `anthropic>=0.49.0` and `openai>=1.75.0` to dependencies |

---

## Design Decisions

### 1. Model-name-based provider detection

The factory (`llm_factory.py`) inspects the model name string:

```python
claude-*            → ClaudeClient
gpt-*, o1*, o3*, o4* → OpenAIClient
anything else        → OllamaClient
```

This keeps the CLI surface unchanged — users already pass `--model` and just change the value.

### 2. Shared `BaseLLMClient` interface

All three clients inherit from `BaseLLMClient` and implement:

```python
def query(prompt, image_path, messages) -> LLMResponse
def is_vision_model() -> bool
```

`list_models_info()` remains Ollama-only (local model discovery). The base class raises `NotImplementedError` for other clients so the `list-models` command is unaffected.

### 3. Ollama-format message passthrough

`main.py` builds messages in Ollama's dict format:

```python
{'role': 'user', 'content': '...', 'images': ['/tmp/screenshot.png']}
```

Each new client converts this format internally in `_convert_messages()`:

- **Claude** — images become `base64` blocks inside an Anthropic `content` array
- **OpenAI** — images become `image_url` blocks with `data:image/png;base64,...` data URIs

This means `main.py` needed zero message-format changes. The threading loop (which appends `assistant` and `user` turns) works unchanged for all providers.

### 4. Vision detection without API calls

Ollama's `is_vision_model()` makes a network call to `ollama.show()`. The new clients use regex matching instead — instantaneous, no network required:

- **Claude** — `^claude-([3-9]|\d{2,})` (claude-3+, claude-4+, …)
- **OpenAI** — `^(gpt-4o|gpt-4-turbo|gpt-4-vision|o3*|o4*)`

### 5. Lazy imports

`anthropic` and `openai` are imported inside the factory function, not at module load time. Users who only use Ollama are never affected by missing cloud SDK packages.

### 6. API key handling

Keys are read from environment variables and validated at client construction time with clear error messages:

```
ANTHROPIC_API_KEY environment variable is not set.
Export it with: export ANTHROPIC_API_KEY=your_key
```

---

## Setup

Install the new dependencies:

```bash
uv sync
# or
pip install anthropic openai
```

Set your API keys:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...
```

---

## Examples

```bash
# Claude — vision-capable, sends screenshot directly
oracle ask "What does this error mean?" --model claude-sonnet-4-6

# Claude — force OCR instead of vision
oracle ask "Summarise this" --model claude-opus-4-6 --force-ocr

# OpenAI GPT-4o — vision-capable
oracle ask "Explain this diff" --model gpt-4o --latest-screenshot

# OpenAI — text-only model, uses OCR pipeline
oracle ask "What command is shown?" --model gpt-4-turbo

# Threaded conversation with Claude
oracle ask "What is this?" --model claude-haiku-4-5 --thread
```

---

## Not in scope

- `oracle list-models` remains Ollama-only (local model discovery).
- Streaming responses are not implemented; all providers use blocking calls.
- No per-provider configuration file; API keys are environment variables only.
