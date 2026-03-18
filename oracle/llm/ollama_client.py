import ollama
from typing import Optional
from oracle.models.data_models import LLMResponse

class OllamaClient:
    def __init__(self, model_name: str = "qwen3.5:9b"):
        self.model_name = model_name

    def query(self, prompt: str = None, image_path: Optional[str] = None, messages: Optional[list[dict]] = None) -> LLMResponse:
        """
        Sends a query to the local Ollama instance and returns the result.
        """
        try:
            # Prepare messages
            if messages is None:
                if prompt is None:
                    raise ValueError("Either 'prompt' or 'messages' must be provided.")
                message = {'role': 'user', 'content': prompt}
                if image_path:
                    message['images'] = [image_path]
                messages = [message]

            response = ollama.chat(
                model=self.model_name,
                messages=messages,
                options={'temperature': 0.1} # Lower temperature for more factual answers
            )
            
            answer = response.get('message', {}).get('content', '')
            if not answer:
                raise RuntimeError("Empty response from Ollama.")
            
            # Ollama provides duration in nanoseconds
            total_duration_ns = response.get('total_duration', 0)
            total_duration_seconds = total_duration_ns / 1_000_000_000.0 if total_duration_ns else 0.0
                
            return LLMResponse(
                answer=answer,
                model=self.model_name,
                total_duration_seconds=total_duration_seconds
            )
        except Exception as e:
            # Re-raise as RuntimeError for consistency
            error_msg = str(e)
            if "not found" in error_msg.lower():
                raise RuntimeError(f"Ollama model '{self.model_name}' not found. Please pull it first using 'ollama pull {self.model_name}'.") from e
            if "connection" in error_msg.lower() or "connect" in error_msg.lower():
                raise RuntimeError("Ollama server is not available. Please make sure Ollama is running.") from e
            raise RuntimeError(f"An error occurred while querying Ollama: {e}") from e

    def list_models_info(self) -> list[dict]:
        """
        Lists available models with detailed info (e.g., vision capability).
        """
        try:
            models_info = ollama.list()
            detailed_models = []
            for m in models_info.models:
                # To check if vision capable, we need to show the model
                # This can be slow if there are many models, but it's necessary
                try:
                    show_info = ollama.show(m.model)
                    is_vision = "vision" in show_info.get("capabilities", [])
                except Exception:
                    is_vision = False
                
                detailed_models.append({
                    "name": m.model,
                    "is_vision": is_vision,
                    "size": m.size,
                    "family": m.details.family,
                    "parameter_size": m.details.parameter_size,
                    "quantization_level": m.details.quantization_level
                })
            return detailed_models
        except Exception as e:
            raise RuntimeError(f"Failed to list detailed Ollama models: {e}") from e

    def is_vision_model(self) -> bool:
        """
        Check if the current model is a vision-capable model.
        """
        try:
            model_details = ollama.show(self.model_name)
            return "vision" in model_details.get("capabilities", [])
        except Exception:
            return False
