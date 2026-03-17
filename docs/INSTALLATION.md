### Installation Guide

Oracle is a local-first Python CLI tool designed for macOS. It uses native macOS APIs for window management, screenshot capture, and OCR.

#### Prerequisites

1.  **macOS:** Oracle requires macOS due to its dependence on Quartz and Vision frameworks.
2.  **Ollama:** Ensure you have [Ollama](https://ollama.com/) installed and running locally.
    -   Download and install from [ollama.com](https://ollama.com/download).
    -   Start the Ollama application or run `ollama serve`.
    -   Pull a model to use (e.g., `ollama pull llama3`).
3.  **Python 3.13:** Oracle is built for Python 3.13.
4.  **uv:** We recommend using `uv` for dependency management. Install it via:
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

#### Setup Instructions

1.  **Clone the Repository:**
    ```bash
    git clone <repository-url>
    cd Oracle
    ```

2.  **Install & Setup:**
    Using `uv`:
    ```bash
    uv sync
    # To use the 'oracle' command directly, you can install the package in editable mode:
    uv pip install -e .
    ```
    Alternatively, you can run via `uv run oracle`.

3.  **Permissions:**
    On first run, macOS may prompt for permissions:
    -   **Screen Recording:** Required for capturing screenshots of selected windows.
    -   **Accessibility:** Required if you use the auto-typing feature (`--type-output`).
    Go to `System Settings > Privacy & Security` and ensure your terminal/IDE has the necessary permissions.

#### Verifying Installation

Run the following command to see if Oracle can list your windows:
```bash
oracle list-windows
```
If you see a table of active windows, the installation was successful! (Note: You may need to have your virtual environment activated or use `uv run oracle list-windows` if not installed in your global path).
