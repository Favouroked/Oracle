from abc import ABC, abstractmethod
from typing import Optional
from oracle.models.data_models import LLMResponse


class BaseLLMClient(ABC):
    def __init__(self, model_name: str):
        self.model_name = model_name

    @abstractmethod
    def query(
        self,
        prompt: Optional[str] = None,
        image_path: Optional[str] = None,
        messages: Optional[list[dict]] = None,
    ) -> LLMResponse: ...

    @abstractmethod
    def is_vision_model(self) -> bool: ...

    def list_models_info(self) -> list[dict]:
        raise NotImplementedError("list_models_info is only supported by OllamaClient.")
