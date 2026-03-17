import subprocess
import os
import tempfile
from datetime import datetime
from oracle.models.data_models import WindowInfo, ScreenshotResult

class WindowCapturer:
    @staticmethod
    def capture_window(window: WindowInfo) -> ScreenshotResult:
        """
        Captures a screenshot of the specified window using the macOS screencapture utility.
        """
        # Create a temporary file for the screenshot
        # For simplicity, we'll store it in a predictable location or a temp directory
        temp_dir = tempfile.gettempdir()
        filename = f"oracle_capture_{window.window_id}_{int(datetime.now().timestamp())}.png"
        image_path = os.path.join(temp_dir, filename)
        
        # screencapture command:
        # -l <windowid>: capture window with given windowid
        # -o: in window capture mode, do not include the window shadow
        # -x: do not play sounds
        try:
            cmd = ["screencapture", "-l", str(window.window_id), "-o", "-x", image_path]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if not os.path.exists(image_path) or os.path.getsize(image_path) == 0:
                raise RuntimeError(f"Failed to capture screenshot: {image_path} not created or empty.")
                
            return ScreenshotResult(
                image_path=image_path,
                window_info=window,
                timestamp=datetime.now()
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"screencapture failed with error: {e.stderr}") from e
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred during capture: {e}") from e

    @staticmethod
    def cleanup(screenshot_result: ScreenshotResult):
        """
        Removes the screenshot file from disk.
        """
        try:
            if os.path.exists(screenshot_result.image_path):
                os.remove(screenshot_result.image_path)
        except Exception as e:
            # Non-critical, just log it
            print(f"Warning: Failed to cleanup screenshot file {screenshot_result.image_path}: {e}")
