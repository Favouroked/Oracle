import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from oracle.window.enumerator import WindowEnumerator
from oracle.capture.capture_window import WindowCapturer
from oracle.ocr.vision_ocr import VisionOCR
from oracle.llm.ollama_client import OllamaClient
from oracle.llm.prompt_builder import PromptBuilder
from oracle.history.interaction_logger import InteractionLogger
from oracle.typing.injector import OutputInjector
from oracle.models.data_models import InteractionLog, WindowInfo

console = Console()

@click.group()
def cli():
    """Oracle: A local-first AI CLI tool for window context."""
    pass

@cli.command(name="list-windows")
def list_windows_cmd():
    """List active application windows."""
    windows = WindowEnumerator.get_active_windows()
    
    if not windows:
        console.print("[yellow]No active windows found.[/yellow]")
        return

    table = Table(title="Active Windows")
    table.add_column("Index", style="cyan")
    table.add_column("Window ID", style="magenta")
    table.add_column("App Name", style="green")
    table.add_column("Title", style="white")

    for i, w in enumerate(windows):
        table.add_row(str(i), str(w.window_id), w.app_name, w.title or "[italic grey]No Title[/italic grey]")

    console.print(table)

def select_window_interactively(windows: list[WindowInfo]) -> WindowInfo:
    """Interactively select a window from a list."""
    table = Table(title="Select a Window")
    table.add_column("Index", style="cyan")
    table.add_column("App Name", style="green")
    table.add_column("Title", style="white")

    for i, w in enumerate(windows):
        table.add_row(str(i), w.app_name, w.title or "[italic grey]No Title[/italic grey]")

    console.print(table)
    
    idx = -1
    while idx < 0 or idx >= len(windows):
        try:
            val = click.prompt("Enter window index", type=int)
            if 0 <= val < len(windows):
                idx = val
            else:
                console.print(f"[red]Index {val} is out of range.[/red]")
        except click.exceptions.Abort:
            raise
        except Exception:
            console.print("[red]Invalid input. Please enter a number.[/red]")
            
    return windows[idx]

@cli.command(name="ask")
@click.argument("question", required=False)
@click.option("--model", default="llama3", help="Ollama model name.")
@click.option("--window-id", type=int, help="Target window ID.")
@click.option("--window-index", type=int, help="Target window index from 'list-windows'.")
@click.option("--select", is_flag=True, help="Interactively select a window.")
@click.option("--preview-context", is_flag=True, help="Preview OCR text before LLM query.")
@click.option("--type-output", is_flag=True, help="Enable auto-typing the result back into the window.")
@click.option("--log-path", default="oracle_history.jsonl", help="Path to history log.")
@click.option("--verbose", is_flag=True, help="Enable verbose output.")
def ask_cmd(question, model, window_id, window_index, select, preview_context, type_output, log_path, verbose):
    """Ask a question about a window's content."""
    
    # 1. Get the question if not provided as argument
    if not question:
        question = click.prompt("Enter your question")
        
    # 2. Identify the target window
    windows = WindowEnumerator.get_active_windows()
    target_window = None
    
    if window_id:
        for w in windows:
            if w.window_id == window_id:
                target_window = w
                break
        if not target_window:
            console.print(f"[red]Window ID {window_id} not found.[/red]")
            return
    elif window_index is not None:
        if 0 <= window_index < len(windows):
            target_window = windows[window_index]
        else:
            console.print(f"[red]Window index {window_index} out of range.[/red]")
            return
    elif select or not (window_id or window_index):
        if not windows:
            console.print("[red]No active windows found to select from.[/red]")
            return
        target_window = select_window_interactively(windows)
        
    if not target_window:
        console.print("[red]No window selected.[/red]")
        return
        
    console.print(f"\n[bold blue]Selected Window:[/bold blue] {target_window.app_name} - {target_window.title or 'No Title'}")

    try:
        # 3. Capture screenshot
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            task = progress.add_task("Capturing window...", total=None)
            screenshot = WindowCapturer.capture_window(target_window)
            progress.update(task, description="Screenshot captured.")
            
            # 4. OCR
            progress.update(task, description="Running OCR...")
            ocr_result = VisionOCR.extract_text(screenshot.image_path)
            progress.update(task, description=f"OCR finished (Confidence: {ocr_result.confidence:.2f}).")

            if not ocr_result.has_text:
                console.print("[yellow]Warning: Little or no text was extracted from the window.[/yellow]")
            
            if preview_context:
                console.print(Panel(ocr_result.text, title="OCR Context Preview", border_style="dim"))

            # 5. Build prompt and query LLM
            progress.update(task, description=f"Querying Ollama ({model})...")
            prompt = PromptBuilder.build_prompt(question, ocr_result.text, target_window)
            
            client = OllamaClient(model_name=model)
            llm_response = client.query(prompt)
            progress.update(task, description="LLM query finished.")

        # 6. Print answer
        console.print("\n", Panel(llm_response.answer, title=f"Oracle Answer ({model})", border_style="green"))

        # 7. Log interaction
        logger = InteractionLogger(log_path=log_path)
        log_entry = InteractionLog(
            window_info=target_window,
            question=question,
            model=model,
            ocr_text_excerpt=ocr_result.text[:500] + "..." if len(ocr_result.text) > 500 else ocr_result.text,
            response=llm_response.answer,
            auto_typing_requested=type_output,
            status="success"
        )
        logger.log(log_entry)
        
        # 8. Cleanup screenshot
        WindowCapturer.cleanup(screenshot)
        
        # 9. Optional auto-typing
        if type_output:
            injector = OutputInjector()
            injector.confirm_and_type(llm_response.answer, target_window.app_name)

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        # Log failure if we have enough info
        if 'target_window' in locals() and target_window:
            try:
                logger = InteractionLogger(log_path=log_path)
                log_entry = InteractionLog(
                    window_info=target_window,
                    question=question,
                    model=model,
                    ocr_text_excerpt="",
                    response="",
                    auto_typing_requested=type_output,
                    status="error",
                    error_message=str(e)
                )
                logger.log(log_entry)
            except:
                pass

if __name__ == "__main__":
    cli()
