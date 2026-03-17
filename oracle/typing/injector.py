import time
from pynput.keyboard import Controller, Key
from typing import Optional

class OutputInjector:
    def __init__(self):
        self.keyboard = Controller()

    def type_text(self, text: str, delay: float = 0.01):
        """
        Simulates typing of the given text into the currently focused window.
        """
        # Small initial delay to ensure the user has switched context if needed
        # although the confirmation should handle this.
        time.sleep(0.5)
        
        for char in text:
            try:
                self.keyboard.type(char)
                # Small delay between characters for reliability
                time.sleep(delay)
            except Exception as e:
                # Log error but continue typing other characters if possible
                print(f"Warning: Failed to type character '{char}': {e}")

    def confirm_and_type(self, text: str, window_name: str, countdown: int = 3):
        """
        Asks for confirmation and counts down before typing.
        """
        print(f"\n⚠️ READY TO INJECT TEXT into window: '{window_name}'")
        print(f"Target text length: {len(text)} characters.")
        print("-" * 20)
        print(text[:100] + ("..." if len(text) > 100 else ""))
        print("-" * 20)
        
        choice = input(f"Proceed with auto-typing? (y/N): ").strip().lower()
        if choice != 'y':
            print("Auto-typing cancelled.")
            return False
            
        print(f"Starting in {countdown} seconds... Please FOCUS the target window.")
        for i in range(countdown, 0, -1):
            print(f"{i}...")
            time.sleep(1)
            
        print("Typing...")
        self.type_text(text)
        print("Finished typing.")
        return True
