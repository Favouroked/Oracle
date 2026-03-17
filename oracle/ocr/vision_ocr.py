import Vision
import Foundation
import AppKit
import Quartz
from oracle.models.data_models import OCRResult

class VisionOCR:
    @staticmethod
    def extract_text(image_path: str) -> OCRResult:
        """
        Extracts text from an image using Apple's Vision framework via pyobjc.
        """
        try:
            # Create a URL for the image file
            image_url = Foundation.NSURL.fileURLWithPath_(image_path)
            
            # Create a VNImageRequestHandler for the image
            handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(image_url, None)
            
            # Create a VNRecognizeTextRequest
            # This is a block-less approach, where we retrieve results after performing the request
            request = Vision.VNRecognizeTextRequest.alloc().init()
            
            # Configure the request: use 'Accurate' level for better OCR quality
            request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
            
            # Perform the request
            success, error = handler.performRequests_error_([request], None)
            
            if not success:
                error_msg = error.localizedDescription() if error else "Unknown Vision error"
                raise RuntimeError(f"Vision OCR request failed: {error_msg}")
            
            # Process results
            observations = request.results()
            if not observations:
                return OCRResult(text="", confidence=0.0, has_text=False)
            
            extracted_text_parts = []
            total_confidence = 0.0
            
            for observation in observations:
                # Get the top candidate (the one with highest confidence)
                top_candidates = observation.topCandidates_(1)
                if top_candidates:
                    candidate = top_candidates[0]
                    extracted_text_parts.append(candidate.string())
                    total_confidence += candidate.confidence()
            
            full_text = "\n".join(extracted_text_parts)
            avg_confidence = total_confidence / len(observations) if observations else 0.0
            
            # Basic cleanup: remove noise and leading/trailing whitespace
            cleaned_text = full_text.strip()
            
            return OCRResult(
                text=cleaned_text,
                confidence=avg_confidence,
                has_text=len(cleaned_text) > 0
            )
            
        except Exception as e:
            # Re-raise as RuntimeError for consistency
            raise RuntimeError(f"An error occurred during OCR: {e}") from e
