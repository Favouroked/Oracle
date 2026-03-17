# Oracle AI

Oracle is a local-first, privacy-conscious Python CLI tool for macOS that allows you to interact with your application windows using an LLM.

Oracle takes a screenshot of a specific window you select, extracts text using macOS's high-performance native Vision OCR, and sends that text along with your question to a local Ollama instance. This ensures all your data stays on your machine.

## Key Features

-   **Native macOS Integration:** Precise window selection and capture using Quartz APIs.
-   **Local-First OCR:** Uses Apple's Vision framework (zero-dependency, extremely fast).
-   **Private Inference:** Queries local LLMs via Ollama.
-   **Safety-First Auto-Typing:** Can optionally type its answers back into your windows after confirmation.
-   **Audit Log:** Persistently logs all interactions to a local JSONL file.

## Getting Started

1.  **Prerequisites:** macOS, Python 3.13, [Ollama](https://ollama.com/), and `uv`.
2.  **Installation:** `uv sync`
3.  **Detailed Instructions:** See [docs/INSTALLATION.md](docs/INSTALLATION.md).

## Usage Examples

### List active windows
```bash
oracle list-windows
```

### Ask about a window (interactive)
```bash
oracle ask "What is going on here?" --select
```

### Ask about a window by index and type the answer
```bash
oracle ask "Explain this code." --window-index 0 --type-output
```

For a complete list of commands and options, see [docs/COMMANDS.md](docs/COMMANDS.md).

## Privacy & Safety

-   **Zero Cloud Dependence:** All OCR and LLM inference is performed locally.
-   **Transparent Actions:** Oracle tells you what it's capturing and can preview the OCR text before sending it to the LLM.
-   **Safe Injection:** Auto-typing requires explicit user confirmation and provides a countdown before starting.

## License

MIT
