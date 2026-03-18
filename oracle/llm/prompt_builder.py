from typing import Optional
from oracle.models.data_models import WindowInfo

class PromptBuilder:
    @staticmethod
    def build_prompt(
        question: str, 
        ocr_text: str, 
        window_info: Optional[WindowInfo] = None,
        has_image: bool = False
    ) -> str:
        """
        Constructs a prompt for the local LLM using the user's question and OCR text.
        """
        system_instruction = (
            "You are Oracle, a helpful AI assistant that answers questions based on the content of a user's window.\n"
        )
        
        if has_image:
            system_instruction += "Use the provided image (and any OCR-extracted text) as context to answer the question.\n"
        else:
            system_instruction += "Use the provided OCR-extracted text as context to answer the question.\n"

        system_instruction += (
            "If the context is partial, noisy, or ambiguous, acknowledge this uncertainty.\n"
            "Keep your answer concise and relevant."
        )
        
        window_context = ""
        if window_info:
            window_context = f"Window Context (App: {window_info.app_name}, Title: {window_info.title}):\n"
        
        prompt = f"{system_instruction}\n\n"
        prompt += f"USER QUESTION: {question}\n\n"
        prompt += f"{window_context}OCR EXTRACTED TEXT:\n"
        if ocr_text:
            prompt += "--- START ---\n"
            prompt += f"{ocr_text}\n"
            prompt += "--- END ---\n\n"
        else:
            prompt += "[No text provided, please refer to the image directly if available.]\n\n"
        
        prompt += "Based on the " + ("image and " if has_image else "") + "text above, what is the answer to the user's question?"
        
        return prompt
