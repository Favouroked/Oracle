from pydantic import BaseModel, Field

class RuntimeConfig(BaseModel):
    model: str = Field("llama3", description="Default Ollama model")
    log_path: str = Field("oracle_history.jsonl", description="Path to interaction history log")
    verbose: bool = Field(False, description="Enable verbose output")
    preview_context: bool = Field(False, description="Show OCR context before LLM query")
    type_output: bool = Field(False, description="Enable optional auto-typing")
