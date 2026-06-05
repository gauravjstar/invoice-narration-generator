"""Advanced OCR Engine with multiple OCR backends"""
import logging
import cv2
import numpy as np
from typing import Dict, Tuple, List
from pathlib import Path
from pdf2image import convert_from_path
from PIL import Image
import io

logger = logging.getLogger(__name__)

class OCREngine:
    """Multi-engine OCR processor with automatic fallback"""
    
    def __init__(self):
        """Initialize OCR engines"""
        self.engines = {}
        self._init_paddle_ocr()
        self._init_easy_ocr()
        self._init_tesseract()
        
    def _init_paddle_ocr(self):
        """Initialize PaddleOCR"""
        try:
            from paddleocr import PaddleOCR
            self.engines['paddleocr'] = PaddleOCR(
                use_angle_cls=True,
                lang='en',
                use_gpu=False
            )
            logger.info("✅ PaddleOCR initialized")
        except Exception as e:
            logger.warning(f"PaddleOCR initialization failed: {str(e)}")
    
    def _init_easy_ocr(self):
        """Initialize EasyOCR"""
        try:
            import easyocr
            self.engines['easyocr'] = easyocr.Reader(['en'], gpu=False)
            logger.info("✅ EasyOCR initialized")
        except Exception as e:
            logger.warning(f"EasyOCR initialization failed: {str(e)}")
    
    def _init_tesseract(self):
        """Initialize Tesseract"""
        try:
            import pytesseract
            self.engines['tesseract'] = pytesseract
            logger.info("✅ Tesseract initialized")
        except Exception as e:
            logger.warning(f"Tesseract initialization failed: {str(e)}")
    
    def extract_from_image(self, image_path: str) -> Dict:
        """Extract text from image with automatic fallback"""
        try:
            image = cv2.imread(str(image_path))
            if image is None:
                image = Image.open(image_path)
                image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Preprocess image
            preprocessed = self._preprocess_image(image)
            
            # Try PaddleOCR first (best for invoices)
            if 'paddleocr' in self.engines:
                result = self._extract_paddleocr(preprocessed)
                if result['confidence'] > 0.6:
                    result['engine'] = 'paddleocr'
                    return result
            
            # Fallback to EasyOCR
            if 'easyocr' in self.engines:
                result = self._extract_easyocr(preprocessed)
                if result['confidence'] > 0.6:
                    result['engine'] = 'easyocr'
                    return result
            
            # Fallback to Tesseract
            if 'tesseract' in self.engines:
                result = self._extract_tesseract(preprocessed)
                result['engine'] = 'tesseract'
                return result
            
            logger.error("No OCR engine available")
            return {'text': '', 'confidence': 0, 'engine': 'none', 'error': 'No OCR engine available'}
            
        except Exception as e:
            logger.error(f"Image extraction failed: {str(e)}")
            return {'text': '', 'confidence': 0, 'engine': 'error', 'error': str(e)}
    
    def extract_from_pdf(self, pdf_path: str) -> Dict:
        """Extract text from PDF (both image and text PDFs)"""
        try:
            all_text = []
            all_confidence = []
            engines_used = set()
            
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=300)
            
            for page_num, image in enumerate(images):
                # Save image temporarily
                temp_path = f"/tmp/page_{page_num}.jpg"
                image.save(temp_path)
                
                # Extract from image
                result = self.extract_from_image(temp_path)
                all_text.append(result.get('text', ''))
                if result.get('confidence', 0) > 0:
                    all_confidence.append(result.get('confidence', 0))
                engines_used.add(result.get('engine', 'unknown'))
                
                # Clean up
                Path(temp_path).unlink(missing_ok=True)
            
            avg_confidence = np.mean(all_confidence) if all_confidence else 0
            
            return {
                'text': ' '.join(all_text),
                'pages': len(images),
                'confidence': avg_confidence,
                'engine': ','.join(engines_used),
                'page_texts': all_text
            }
            
        except Exception as e:
            logger.error(f"PDF extraction failed: {str(e)}")
            return {'text': '', 'pages': 0, 'confidence': 0, 'engine': 'error', 'error': str(e)}
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Denoise
            denoised = cv2.fastNlMeansDenoising(gray, h=10)
            
            # Increase contrast
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            contrast = clahe.apply(denoised)
            
            # Sharpen
            kernel = np.array([[-1, -1, -1],
                              [-1,  9, -1],
                              [-1, -1, -1]])
            sharpened = cv2.filter2D(contrast, -1, kernel)
            
            # Deskew
            deskewed = self._deskew_image(sharpened)
            
            return deskewed
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {str(e)}")
            return image
    
    def _deskew_image(self, image: np.ndarray) -> np.ndarray:
        """Deskew image for better text alignment"""
        try:
            coords = np.column_stack(np.where(image > 0))
            if len(coords) == 0:
                return image
            
            angle = cv2.minAreaRect(coords)[2]
            if angle < -45:
                angle = 90 + angle
            
            if abs(angle) > 0.1:
                h, w = image.shape
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                image = cv2.warpAffine(image, M, (w, h),
                                     borderMode=cv2.BORDER_REPLICATE)
            
            return image
        except Exception as e:
            logger.warning(f"Deskewing failed: {str(e)}")
            return image
    
    def _extract_paddleocr(self, image: np.ndarray) -> Dict:
        """Extract using PaddleOCR"""
        try:
            result = self.engines['paddleocr'].ocr(image, cls=True)
            
            texts = []
            confidences = []
            
            if result and result[0]:
                for line in result[0]:
                    text = line[1][0]
                    confidence = float(line[1][1])
                    texts.append(text)
                    confidences.append(confidence)
            
            avg_confidence = np.mean(confidences) if confidences else 0
            
            return {
                'text': ' '.join(texts),
                'confidence': float(avg_confidence),
                'lines': texts,
                'line_confidences': confidences
            }
        except Exception as e:
            logger.error(f"PaddleOCR extraction failed: {str(e)}")
            return {'text': '', 'confidence': 0, 'error': str(e)}
    
    def _extract_easyocr(self, image: np.ndarray) -> Dict:
        """Extract using EasyOCR"""
        try:
            result = self.engines['easyocr'].readtext(image)
            
            texts = []
            confidences = []
            
            for detection in result:
                text = detection[1]
                confidence = float(detection[2])
                texts.append(text)
                confidences.append(confidence)
            
            avg_confidence = np.mean(confidences) if confidences else 0
            
            return {
                'text': ' '.join(texts),
                'confidence': float(avg_confidence),
                'lines': texts,
                'line_confidences': confidences
            }
        except Exception as e:
            logger.error(f"EasyOCR extraction failed: {str(e)}")
            return {'text': '', 'confidence': 0, 'error': str(e)}
    
    def _extract_tesseract(self, image: np.ndarray) -> Dict:
        """Extract using Tesseract"""
        try:
            # Convert back to PIL Image for Tesseract
            pil_image = Image.fromarray(image)
            text = self.engines['tesseract'].image_to_string(pil_image)
            
            return {
                'text': text,
                'confidence': 0.7,  # Tesseract doesn't provide confidence
                'lines': text.split('\n')
            }
        except Exception as e:
            logger.error(f"Tesseract extraction failed: {str(e)}")
            return {'text': '', 'confidence': 0, 'error': str(e)}
