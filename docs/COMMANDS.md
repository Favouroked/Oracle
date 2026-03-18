### Commands Guide

Oracle provides a straightforward CLI for interacting with your desktop windows via AI.

#### General Syntax

```bash
oracle [COMMAND] [OPTIONS]
```

---

#### 1. `list-windows`

List all active, visible application windows on your macOS.

-   **Usage:**
    ```bash
    oracle list-windows
    ```
-   **Output:**
    A table containing:
    -   `Index`: Used for selecting windows in other commands.
    -   `Window ID`: Internal macOS ID.
    -   `App Name`: Name of the application.
    -   `Title`: Title of the window (if available).

---

#### 2. `ask`

The primary command for asking questions based on a window's content.

-   **Usage:**
    ```bash
    oracle ask "YOUR QUESTION" [OPTIONS]
    ```
-   **Interactive Mode:**
    If no question is provided, Oracle will prompt you to enter one.
    If no window is specified, it will show an interactive selection list.

-   **Options:**
    -   `"QUESTION"` (argument): Your question for the LLM.
    -   `--model [MODEL_NAME]`: Specify which Ollama model to use. (Default: `llama3`)
    -   `--window-id [ID]`: Select the target window by its ID.
    -   `--window-index [INDEX]`: Select the target window by its index from `list-windows`.
    -   `--select`: Force interactive window selection even if IDs are available.
    -   `--image-path [PATH]`: Manual path to an image file.
    -   `--latest-screenshot` or `--last-screenshot`: Use the most recent screenshot from the Desktop.
    -   `--preview-context`: Display the text extracted from OCR before sending it to the model.
    -   `--type-output`: Ask the model for an answer and then offer to auto-type it back into the selected window.
    -   `--log-path [PATH]`: Customize the location of the history log. (Default: `oracle_history.jsonl`)
    -   `--verbose`: Show additional debug information during execution.

---

#### 3. `list-models`

List all available local Ollama models and indicate if they support vision (image input).

-   **Usage:**
    ```bash
    oracle list-models
    ```

---

#### 4. `preview-context`

Preview the text context extracted from a window, image, or screenshot without asking a question.

-   **Usage:**
    ```bash
    oracle preview-context [OPTIONS]
    ```

-   **Options:**
    -   `--window-id [ID]`: Select the target window by its ID.
    -   `--window-index [INDEX]`: Select the target window by its index.
    -   `--select`: Force interactive window selection.
    -   `--image-path [PATH]`: Manual path to an image file.
    -   `--latest-screenshot` or `--last-screenshot`: Use the most recent screenshot from the Desktop.
    -   `--method [apple-vision | vision-model]`: Choose the OCR method (Default: `apple-vision`).
    -   `--model [MODEL_NAME]`: Specify the vision model to use if method is `vision-model`.

---

#### Typical Workflow

1.  **Find the window index:**
    ```bash
    oracle list-windows
    ```
2.  **Ask a question about a specific window:**
    ```bash
    oracle ask "What is the error message on this screen?" --window-index 0
    ```
3.  **Use auto-typing for code completions or answers:**
    ```bash
    oracle ask "Refactor this code to use async/await." --window-index 2 --type-output
    ```

#### Logging

Oracle keeps a record of every interaction in a JSONL file (default: `oracle_history.jsonl`). Each entry includes:
-   Timestamp
-   Selected window metadata
-   The original question
-   Model used
-   OCR text excerpt
-   Model's response
-   Status (success/error)
