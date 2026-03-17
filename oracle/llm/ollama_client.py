import ollama
from typing import Optional
from oracle.models.data_models import LLMResponse

class OllamaClient:
    def __init__(self, model_name: str = "llama3"):
        self.model_name = model_name

    def query(self, prompt: str) -> LLMResponse:
        """
        Sends a query to the local Ollama instance and returns the result.
        """
        try:
            # Check if model exists (implicitly or explicitly)
            # For simplicity, we'll try to chat directly
            response = ollama.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': 0.1} # Lower temperature for more factual answers
            )
            
            answer = response.get('message', {}).get('content', '')
            if not answer:
                raise RuntimeError("Empty response from Ollama.")
                
            return LLMResponse(
                answer=answer,
                model=self.model_name
            )
        except Exception as e:
            # Re-raise as RuntimeError for consistency
            error_msg = str(e)
            if "not found" in error_msg.lower():
                raise RuntimeError(f"Ollama model '{self.model_name}' not found. Please pull it first using 'ollama pull {self.model_name}'.") from e
            if "connection" in error_msg.lower() or "connect" in error_msg.lower():
                raise RuntimeError("Ollama server is not available. Please make sure Ollama is running.") from e
            raise RuntimeError(f"An error occurred while querying Ollama: {e}") from e

    def list_models(self) -> list[str]:
        """
        Lists available models in the local Ollama instance.
        """
        try:
            models_info = ollama.list()
            return [m.model for m in models_info.models]
        except Exception as e:
            raise RuntimeError(f"Failed to list Ollama models: {e}") from e
