import click
import time
import os
import shutil
import sys
import uuid
from pathlib import Path
from typing import Optional
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
from oracle.models.data_models import InteractionLog, WindowInfo, OCRResult, ScreenshotResult

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

@cli.command(name="list-models")
def list_models_cmd():
    """List available local models and their capabilities."""
    client = OllamaClient()
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("Fetching models...", total=None)
        try:
            models = client.list_models_info()
            progress.update(task, description="Models fetched.")
        except Exception as e:
            console.print(f"[red]Error fetching models: {e}[/red]")
            return

    if not models:
        console.print("[yellow]No local Ollama models found.[/yellow]")
        return

    table = Table(title="Available Local Models")
    table.add_column("Model Name", style="cyan")
    table.add_column("Vision", justify="center")
    table.add_column("Family", style="green")
    table.add_column("Params", justify="right")
    table.add_column("Size", justify="right")

    for m in models:
        vision_mark = "[bold green]✓[/bold green]" if m["is_vision"] else "[red]✗[/red]"
        # Human readable size
        size_mb = m["size"] / (1024 * 1024)
        size_gb = size_mb / 1024
        size_str = f"{size_gb:.1f} GB" if size_gb >= 1 else f"{size_mb:.0f} MB"
        
        table.add_row(
            m["name"],
            vision_mark,
            m["family"],
            m["parameter_size"],
            size_str
        )

    console.print(table)

@cli.command(name="uninstall")
def uninstall_cmd():
    """Uninstall Oracle AI from your system."""
    install_dir = Path.home() / ".oracle-ai"
    
    # Possible symlink locations
    possible_symlinks = [
        Path("/usr/local/bin/oracle"),
        Path.home() / ".local/bin/oracle"
    ]
    
    # Also check where 'oracle' command is currently pointing
    oracle_path = shutil.which("oracle")
    if oracle_path:
        possible_symlinks.append(Path(oracle_path))
    
    # Remove duplicates
    possible_symlinks = list(set(possible_symlinks))
    
    confirm = click.confirm("Are you sure you want to uninstall Oracle AI?", default=False)
    if not confirm:
        return

    try:
        # 1. Remove symlink(s)
        for symlink_path in possible_symlinks:
            if symlink_path.exists():
                if symlink_path.is_symlink():
                    target = os.readlink(symlink_path)
                    if str(install_dir) in str(target):
                        console.print(f"Removing symlink: {symlink_path}")
                        try:
                            os.remove(symlink_path)
                        except PermissionError:
                            console.print(f"[yellow]Permission denied. Attempting to remove {symlink_path} with sudo...[/yellow]")
                            os.system(f"sudo rm {symlink_path}")
                    else:
                        console.print(f"[yellow]Symlink {symlink_path} exists but doesn't point to Oracle AI installation. Skipping.[/yellow]")
                elif symlink_path.is_file() and str(install_dir) in str(symlink_path.resolve()):
                    # It might be the actual binary if it's not a symlink but we are sure it's in our install_dir
                    console.print(f"Removing binary: {symlink_path}")
                    try:
                        os.remove(symlink_path)
                    except PermissionError:
                        os.system(f"sudo rm {symlink_path}")
        
        # 2. Remove installation directory
        if install_dir.exists():
            console.print(f"Removing installation directory: {install_dir}")
            shutil.rmtree(install_dir)
            
        console.print("[green]Oracle AI has been uninstalled successfully.[/green]")
    except Exception as e:
        console.print(f"[red]Error during uninstallation: {e}[/red]")

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

def get_target_source(window_id, window_index, select, image_path, latest_screenshot) -> tuple[Optional[WindowInfo], Optional[ScreenshotResult]]:
    """Identify the target source and return (window_info, screenshot)."""
    screenshot = None
    target_window = None

    if image_path:
        screenshot = ScreenshotResult(
            image_path=image_path,
            window_info=None,
            is_temporary=False
        )
    elif latest_screenshot:
        screenshot = WindowCapturer.get_latest_desktop_screenshot()
    else:
        # Window-based capture
        windows = WindowEnumerator.get_active_windows()
        
        if window_id:
            for w in windows:
                if w.window_id == window_id:
                    target_window = w
                    break
            if not target_window:
                console.print(f"[red]Window ID {window_id} not found.[/red]")
                return None, None
        elif window_index is not None:
            if 0 <= window_index < len(windows):
                target_window = windows[window_index]
            else:
                console.print(f"[red]Window index {window_index} out of range.[/red]")
                return None, None
        elif select or not (window_id or window_index):
            if not windows:
                console.print("[red]No active windows found to select from.[/red]")
                return None, None
            target_window = select_window_interactively(windows)
            
        if not target_window:
            console.print("[red]No window selected.[/red]")
            return None, None
            
        console.print(f"\n[bold blue]Selected Window:[/bold blue] {target_window.app_name} - {target_window.title or 'No Title'}")

    return target_window, screenshot

@cli.command(name="ask")
@click.argument("question", required=False)
@click.option("--model", default="qwen3.5:9b", help="Ollama model name.")
@click.option("--window-id", type=int, help="Target window ID.")
@click.option("--window-index", type=int, help="Target window index from 'list-windows'.")
@click.option("--select", is_flag=True, help="Interactively select a window.")
@click.option("--preview-context", is_flag=True, help="Preview OCR text before LLM query.")
@click.option("--type-output", is_flag=True, help="Enable auto-typing the result back into the window.")
@click.option("--force-ocr", is_flag=True, help="Force OCR even if the model supports vision.")
@click.option("--log-path", default="oracle_history.jsonl", help="Path to history log.")
@click.option("--image-path", type=click.Path(exists=True), help="Manual path to an image file.")
@click.option("--latest-screenshot", "--last-screenshot", is_flag=True, help="Use the latest screenshot from the Desktop folder.")
@click.option("--thread", is_flag=True, help="Continue the chat based on the LLM's reply.")
@click.option("--verbose", is_flag=True, help="Enable verbose output.")
def ask_cmd(question, model, window_id, window_index, select, preview_context, type_output, force_ocr, log_path, image_path, latest_screenshot, thread, verbose):
    """Ask a question about a window's content or an image."""
    
    # 1. Get the question if not provided as argument
    if not question:
        question = click.prompt("Enter your question")
        
    # 2. Identify the target source
    target_window, screenshot = get_target_source(window_id, window_index, select, image_path, latest_screenshot)
    if not target_window and not screenshot:
        return

    try:
        # 3. Get the screenshot (either existing or capture it)
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            if not screenshot:
                task = progress.add_task("Capturing window...", total=None)
                screenshot = WindowCapturer.capture_window(target_window)
                progress.update(task, description="Window captured.")
            else:
                task = progress.add_task("Loading image context...", total=None)
                progress.update(task, description=f"Using image: {screenshot.image_path}")

            # 4. Determine if we should use vision or OCR
            client = OllamaClient(model_name=model)
            use_vision = client.is_vision_model() and not force_ocr
            
            ocr_result = None
            if not use_vision:
                # 4a. OCR
                start_ocr = time.time()
                progress.update(task, description="Running OCR...")
                ocr_result = VisionOCR.extract_text(screenshot.image_path)
                ocr_duration = time.time() - start_ocr
                progress.update(task, description=f"OCR finished in {ocr_duration:.2f}s (Confidence: {ocr_result.confidence:.2f}).")
            else:
                progress.update(task, description=f"Using vision ({model}), skipping OCR.")
                ocr_result = OCRResult(text="", confidence=1.0, has_text=False)

            if not ocr_result.has_text and not use_vision:
                console.print("[yellow]Warning: Little or no text was extracted from the source image.[/yellow]")
            
            if preview_context and ocr_result.text:
                console.print(Panel(ocr_result.text, title="OCR Context Preview", border_style="dim"))

            # 5. Build prompt and query LLM
            progress.update(task, description=f"Querying Ollama ({model})...")
            prompt = PromptBuilder.build_prompt(
                question, 
                ocr_result.text, 
                target_window or screenshot.window_info, 
                has_image=use_vision
            )
            
            messages = [{'role': 'user', 'content': prompt}]
            if use_vision:
                messages[0]['images'] = [screenshot.image_path]
            
            llm_response = client.query(messages=messages)
            progress.update(task, description=f"LLM query finished in {llm_response.total_duration_seconds:.2f}s.")

        # 6. Handle response, logging, and potential thread loop
        thread_id = str(uuid.uuid4()) if thread else None
        current_question = question
        
        while True:
            # Print answer
            console.print("\n", Panel(llm_response.answer, title=f"Oracle Answer ({model})", subtitle=f"Time: {llm_response.total_duration_seconds:.2f}s", border_style="green"))

            # 7. Log interaction
            logger = InteractionLogger(log_path=log_path)
            log_entry = InteractionLog(
                window_info=target_window or screenshot.window_info,
                question=current_question,
                model=model,
                ocr_text_excerpt=ocr_result.text[:500] + "..." if len(ocr_result.text) > 500 else ocr_result.text,
                response=llm_response.answer,
                auto_typing_requested=type_output,
                status="success",
                total_duration_seconds=llm_response.total_duration_seconds,
                thread_id=thread_id
            )
            logger.log(log_entry)
            
            # 8. Optional auto-typing (only if we have a target window)
            if type_output and (target_window or screenshot.window_info):
                win = target_window or screenshot.window_info
                injector = OutputInjector()
                injector.confirm_and_type(llm_response.answer, win.app_name)
            elif type_output:
                console.print("[yellow]Warning: Auto-typing requested but no target window is available.[/yellow]")

            if not thread:
                break
            
            # 9. Thread loop follow-up
            next_question = click.prompt("\n[bold cyan]Follow-up[/bold cyan] (or /q to quit)", default="/q")
            if next_question.strip().lower() == "/q":
                break
            
            # Update messages with history
            messages.append({'role': 'assistant', 'content': llm_response.answer})
            messages.append({'role': 'user', 'content': next_question})
            current_question = next_question
            
            # Query again for follow-up
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
                task = progress.add_task(f"Querying Ollama ({model})...", total=None)
                llm_response = client.query(messages=messages)
                progress.update(task, description=f"LLM query finished in {llm_response.total_duration_seconds:.2f}s.")

        # 10. Cleanup screenshot if temporary
        WindowCapturer.cleanup(screenshot)

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        # Log failure if we have enough info
        try:
            logger = InteractionLogger(log_path=log_path)
            # Use locals() to safely get variables that might not have been initialized
            current_vars = locals()
            log_entry = InteractionLog(
                window_info=target_window or (screenshot.window_info if screenshot else None),
                question=current_vars.get('current_question', question),
                model=model,
                ocr_text_excerpt="",
                response="",
                auto_typing_requested=type_output,
                status="error",
                error_message=str(e),
                thread_id=current_vars.get('thread_id')
            )
            logger.log(log_entry)
        except:
            pass

@cli.command(name="preview-context")
@click.option("--window-id", type=int, help="Target window ID.")
@click.option("--window-index", type=int, help="Target window index from 'list-windows'.")
@click.option("--select", is_flag=True, help="Interactively select a window.")
@click.option("--image-path", type=click.Path(exists=True), help="Manual path to an image file.")
@click.option("--latest-screenshot", "--last-screenshot", is_flag=True, help="Use the latest screenshot from the Desktop folder.")
@click.option("--method", type=click.Choice(["apple-vision", "vision-model"]), default="apple-vision", help="OCR method to use.")
@click.option("--model", default="llava:7b", help="Vision model to use if method is 'vision-model'.")
def preview_context_cmd(window_id, window_index, select, image_path, latest_screenshot, method, model):
    """Preview the text context extracted from a window or image."""
    target_window, screenshot = get_target_source(window_id, window_index, select, image_path, latest_screenshot)
    if not target_window and not screenshot:
        return

    try:
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            if not screenshot:
                task = progress.add_task("Capturing window...", total=None)
                screenshot = WindowCapturer.capture_window(target_window)
                progress.update(task, description="Window captured.")
            else:
                task = progress.add_task("Loading image context...", total=None)
                progress.update(task, description=f"Using image: {screenshot.image_path}")

            extracted_text = ""
            start_time = time.time()
            if method == "apple-vision":
                progress.update(task, description="Running Apple Vision OCR...")
                ocr_result = VisionOCR.extract_text(screenshot.image_path)
                extracted_text = ocr_result.text
                duration = time.time() - start_time
                progress.update(task, description=f"OCR finished in {duration:.2f}s (Confidence: {ocr_result.confidence:.2f}).")
            else:
                progress.update(task, description=f"Querying vision model ({model}) for OCR...")
                client = OllamaClient(model_name=model)
                if not client.is_vision_model():
                    raise ValueError(f"Model '{model}' is not vision-capable.")
                
                prompt = "Transcribe all the text visible in this image. Output only the transcribed text, nothing else. If there is no text, output an empty string."
                llm_response = client.query(prompt, image_path=screenshot.image_path)
                extracted_text = llm_response.answer
                progress.update(task, description=f"Vision model OCR finished in {llm_response.total_duration_seconds:.2f}s.")

        if extracted_text:
            title = f"Extracted Context ({method})"
            if method == "vision-model":
                title += f" - {llm_response.total_duration_seconds:.2f}s"
            else:
                title += f" - {duration:.2f}s"
            console.print("\n", Panel(extracted_text, title=title, border_style="dim"))
        else:
            console.print("\n[yellow]No text could be extracted.[/yellow]")

        # Cleanup if temporary
        WindowCapturer.cleanup(screenshot)

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")

if __name__ == "__main__":
    cli()
