import os
import re
import time
import base64
from pathlib import Path
from typing import Optional

from oracle.llm.base_client import BaseLLMClient
from oracle.models.data_models import LLMResponse

_VISION_PATTERN = re.compile(r"^claude-([3-9]|\d{2,})")


def _media_type(img_path: str) -> str:
    suffix = Path(img_path).suffix.lower()
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(suffix, "image/png")


class ClaudeClient(BaseLLMClient):
    def __init__(self, model_name: str):
        super().__init__(model_name)
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY environment variable is not set. "
                "Export it with: export ANTHROPIC_API_KEY=your_key"
            )
        import anthropic
        self._client = anthropic.Anthropic(api_key=api_key)
        self._anthropic = anthropic

    def is_vision_model(self) -> bool:
        return bool(_VISION_PATTERN.match(self.model_name))

    def _convert_messages(self, messages: list[dict]) -> list[dict]:
        converted = []
        for msg in messages:
            role = msg["role"]
            content = msg.get("content", "")
            images = msg.get("images", [])

            if images:
                blocks = []
                for img_path in images:
                    data = base64.standard_b64encode(Path(img_path).read_bytes()).decode()
                    blocks.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": _media_type(img_path),
                            "data": data,
                        },
                    })
                blocks.append({"type": "text", "text": content})
                converted.append({"role": role, "content": blocks})
            else:
                converted.append({"role": role, "content": content})
        return converted

    def query(
        self,
        prompt: Optional[str] = None,
        image_path: Optional[str] = None,
        messages: Optional[list[dict]] = None,
    ) -> LLMResponse:
        if messages is None:
            if prompt is None:
                raise ValueError("Either 'prompt' or 'messages' must be provided.")
            msg: dict = {"role": "user", "content": prompt}
            if image_path:
                msg["images"] = [image_path]
            messages = [msg]

        converted = self._convert_messages(messages)
        start = time.time()
        try:
            response = self._client.messages.create(
                model=self.model_name,
                max_tokens=4096,
                messages=converted,
            )
            answer = response.content[0].text
            duration = time.time() - start
            return LLMResponse(answer=answer, model=self.model_name, total_duration_seconds=duration)
        except self._anthropic.AuthenticationError as e:
            raise RuntimeError("Invalid ANTHROPIC_API_KEY. Check your API key and try again.") from e
        except self._anthropic.NotFoundError as e:
            raise RuntimeError(
                f"Claude model '{self.model_name}' not found. Check the model name and try again."
            ) from e
        except self._anthropic.APIConnectionError as e:
            raise RuntimeError("Could not connect to the Anthropic API. Check your internet connection.") from e
        except Exception as e:
            raise RuntimeError(f"An error occurred while querying Claude: {e}") from e
