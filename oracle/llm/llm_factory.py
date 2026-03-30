from oracle.llm.base_client import BaseLLMClient
from oracle.llm.ollama_client import OllamaClient

_OPENAI_PREFIXES = ("gpt-", "o1", "o3", "o4")


def _is_openai_model(name: str) -> bool:
    return any(name.startswith(p) for p in _OPENAI_PREFIXES)


def create_llm_client(model_name: str) -> BaseLLMClient:
    """Return the appropriate LLM client based on the model name prefix.

    - claude-*        → ClaudeClient (Anthropic, requires ANTHROPIC_API_KEY)
    - gpt-*, o1*, o3*, o4* → OpenAIClient (requires OPENAI_API_KEY)
    - anything else   → OllamaClient (local Ollama instance)
    """
    if model_name.startswith("claude-"):
        from oracle.llm.claude_client import ClaudeClient
        return ClaudeClient(model_name)
    if _is_openai_model(model_name):
        from oracle.llm.openai_client import OpenAIClient
        return OpenAIClient(model_name)
    return OllamaClient(model_name=model_name)
