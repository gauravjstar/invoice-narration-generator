"""AI Data Extraction Service using OpenAI and LangChain"""
import logging
import json
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from app.config import settings

logger = logging.getLogger(__name__)

class InvoiceItem(BaseModel):
    """Invoice line item"""
    item_name: str = Field(..., description="Name of the item")
    quantity: float = Field(..., description="Quantity of items")
    unit: str = Field(..., description="Unit of measurement")
    rate: float = Field(..., description="Rate per unit")
    amount: float = Field(..., description="Total amount for item")

class InvoiceExtraction(BaseModel):
    """Extracted invoice data"""
    supplier_name: str = Field(..., description="Name of the supplier")
    gst_number: Optional[str] = Field(None, description="GST registration number")
    invoice_number: str = Field(..., description="Invoice number")
    invoice_date: str = Field(..., description="Invoice date in DD-MM-YYYY format")
    vehicle_number: Optional[str] = Field(None, description="Vehicle number")
    transporter_name: Optional[str] = Field(None, description="Transporter name")
    lr_number: Optional[str] = Field(None, description="LR (Lorry Receipt) number")
    items: List[InvoiceItem] = Field(..., description="List of line items")
    taxable_value: float = Field(..., description="Taxable value")
    cgst_amount: float = Field(..., description="CGST amount")
    sgst_amount: float = Field(..., description="SGST amount")
    igst_amount: float = Field(..., description="IGST amount")
    total_amount: float = Field(..., description="Total invoice amount")
    extraction_confidence: float = Field(default=0.0, description="Confidence score")

class AIExtractionService:
    """AI-powered data extraction service"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = settings.OPENAI_MODEL
            logger.info(f"✅ AI Extraction Service initialized with {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            self.client = None
    
    def extract_invoice_data(self, ocr_text: str) -> InvoiceExtraction:
        """Extract structured invoice data from OCR text"""
        try:
            if not self.client:
                return self._create_default_extraction()
            
            prompt = f"""Extract invoice information from the following OCR text.
            
OCR Text:
{ocr_text[:4000]}

Extract and return ONLY valid JSON with these exact fields:
- supplier_name (string)
- gst_number (string or null)
- invoice_number (string)
- invoice_date (string in DD-MM-YYYY format)
- vehicle_number (string or null)
- transporter_name (string or null)
- lr_number (string or null)
- items (array of objects with: item_name, quantity, unit, rate, amount)
- taxable_value (number)
- cgst_amount (number)
- sgst_amount (number)
- igst_amount (number)
- total_amount (number)
- extraction_confidence (number between 0 and 1)

Return ONLY the JSON object, no other text."""
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            response_text = response.content[0].text
            
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    data = json.loads(json_str)
                    extraction = InvoiceExtraction(**data)
                else:
                    extraction = self._create_default_extraction()
                    extraction.extraction_confidence = 0.3
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON response")
                extraction = self._create_default_extraction()
                extraction.extraction_confidence = 0.2
            
            logger.info(f"✅ Extraction successful with confidence: {extraction.extraction_confidence}")
            return extraction
            
        except Exception as e:
            logger.error(f"AI extraction failed: {str(e)}")
            extraction = self._create_default_extraction()
            extraction.extraction_confidence = 0.0
            return extraction
    
    def validate_extraction(self, extraction: InvoiceExtraction) -> Dict:
        """Validate extracted data for completeness and consistency"""
        issues = []
        warnings = []
        
        if not extraction.supplier_name:
            issues.append("Supplier name is missing")
        if not extraction.invoice_number:
            issues.append("Invoice number is missing")
        if not extraction.invoice_date:
            issues.append("Invoice date is missing")
        if not extraction.items or len(extraction.items) == 0:
            issues.append("No items found in invoice")
        
        total_tax = extraction.cgst_amount + extraction.sgst_amount + extraction.igst_amount
        expected_total = extraction.taxable_value + total_tax
        
        if abs(expected_total - extraction.total_amount) > 1.0:
            warnings.append(f"Total amount mismatch. Expected: {expected_total}, Got: {extraction.total_amount}")
        
        item_total = sum(item.amount for item in extraction.items)
        if abs(item_total - extraction.taxable_value) > 1.0:
            warnings.append(f"Item total mismatch. Expected: {extraction.taxable_value}, Got: {item_total}")
        
        if extraction.extraction_confidence < 0.7:
            warnings.append(f"Low extraction confidence: {extraction.extraction_confidence}")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "confidence": extraction.extraction_confidence
        }
    
    def _create_default_extraction(self) -> InvoiceExtraction:
        """Create default extraction object"""
        return InvoiceExtraction(
            supplier_name="",
            invoice_number="",
            invoice_date="",
            items=[],
            taxable_value=0.0,
            cgst_amount=0.0,
            sgst_amount=0.0,
            igst_amount=0.0,
            total_amount=0.0
        )

ai_extraction_service = AIExtractionService()
