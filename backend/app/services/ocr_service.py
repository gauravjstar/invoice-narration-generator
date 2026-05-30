"""OCR Service for Invoice Processing"""
import logging
from typing import Dict, List, Optional
from PIL import Image
import io
import numpy as np
from app.config import settings

logger = logging.getLogger(__name__)

class OCRService:
    """Advanced OCR Processing Service"""
    
    def __init__(self):
        """Initialize OCR engine based on configuration"""
        self.engine = settings.OCR_ENGINE
        self.confidence_threshold = settings.OCR_CONFIDENCE_THRESHOLD
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize the appropriate OCR engine"""
        try:
            if self.engine == "paddleocr":
                from paddleocr import PaddleOCR
                self.ocr = PaddleOCR(use_angle_cls=True, lang="en")
                logger.info("✅ PaddleOCR initialized")
            elif self.engine == "easyocr":
                import easyocr
                self.ocr = easyocr.Reader(["en"])
                logger.info("✅ EasyOCR initialized")
            elif self.engine == "tesseract":
                import pytesseract
                self.ocr = pytesseract
                logger.info("✅ Tesseract OCR initialized")
            else:
                raise ValueError(f"Unsupported OCR engine: {self.engine}")
        except Exception as e:
            logger.error(f"Failed to initialize OCR engine: {str(e)}")
            raise
    
    def extract_text_from_image(self, image_path: str) -> Dict:
        """Extract text from image using configured OCR engine"""
        try:
            image = Image.open(image_path).convert('RGB')
            image = self._preprocess_image(image)
            
            if self.engine == "paddleocr":
                result = self.ocr.ocr(np.array(image), cls=True)
                return self._parse_paddle_result(result)
            elif self.engine == "easyocr":
                result = self.ocr.readtext(np.array(image))
                return self._parse_easyocr_result(result)
            elif self.engine == "tesseract":
                text = self.ocr.image_to_string(image)
                return {"text": text, "confidence": 0.85}
        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            return {"text": "", "confidence": 0, "error": str(e)}
    
    def _preprocess_image(self, image: Image) -> Image:
        """Preprocess image for better OCR results"""
        try:
            from PIL import ImageFilter, ImageOps, ImageEnhance
            
            image = ImageOps.grayscale(image)
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            image = image.filter(ImageFilter.MedianFilter(size=3))
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)
            
            return image
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {str(e)}")
            return image
    
    def _parse_paddle_result(self, result: List) -> Dict:
        """Parse PaddleOCR result"""
        all_text = []
        all_confidence = []
        
        if result and result[0]:
            for line in result[0]:
                text = line[1][0]
                confidence = float(line[1][1])
                if confidence >= self.confidence_threshold:
                    all_text.append(text)
                    all_confidence.append(confidence)
        
        return {
            "text": " ".join(all_text),
            "confidence": np.mean(all_confidence) if all_confidence else 0,
            "lines": all_text,
            "line_confidences": all_confidence
        }
    
    def _parse_easyocr_result(self, result: List) -> Dict:
        """Parse EasyOCR result"""
        all_text = []
        all_confidence = []
        
        for detection in result:
            text = detection[1]
            confidence = float(detection[2])
            if confidence >= self.confidence_threshold:
                all_text.append(text)
                all_confidence.append(confidence)
        
        return {
            "text": " ".join(all_text),
            "confidence": np.mean(all_confidence) if all_confidence else 0,
            "lines": all_text,
            "line_confidences": all_confidence
        }
    
    def extract_text_from_pdf(self, pdf_path: str) -> Dict:
        """Extract text from PDF file"""
        try:
            import fitz
            
            all_text = []
            doc = fitz.open(pdf_path)
            
            for page_num, page in enumerate(doc):
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_data = pix.tobytes("ppm")
                img = Image.open(io.BytesIO(img_data))
                
                page_result = self.extract_text_from_image(str(img))
                all_text.append(page_result.get("text", ""))
            
            return {
                "text": " ".join(all_text),
                "page_count": len(doc),
                "pages": all_text
            }
        except Exception as e:
            logger.error(f"PDF extraction failed: {str(e)}")
            return {"text": "", "error": str(e)}

ocr_service = OCRService()
