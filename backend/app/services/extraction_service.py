"""Complete invoice data extraction service"""
import logging
import re
from typing import Dict, List, Tuple, Optional
from fuzzywuzzy import fuzz
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class ExtractionService:
    """Extract structured data from OCR text"""
    
    # Invoice number field variations
    INVOICE_KEYWORDS = [
        r'invoice\s*(?:no|number|#)?',
        r'bill\s*(?:no|number|#)?',
        r'tax\s*invoice\s*(?:no|number)',
        r'memo\s*(?:no|number)',
        r'document\s*(?:no|number)',
        r'voucher\s*(?:no|number)',
        r'ref(?:erence)?\s*(?:no|number)',
        r'challan\s*(?:no|number)',
        r'dc\s*(?:no|number)'
    ]
    
    # GST patterns
    GSTIN_PATTERN = r'\d{2}[A-Z]{5}\d{4}[A-Z]{1}\d{1}Z\d{1}'
    
    # Date patterns
    DATE_PATTERNS = [
        r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',  # DD-MM-YYYY or DD/MM/YYYY
        r'\d{2,4}[-/]\d{1,2}[-/]\d{1,2}',  # YYYY-MM-DD
        r'\d{1,2}\s(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s\d{2,4}',  # DD Mon YYYY
    ]
    
    # Tax patterns
    TAX_PATTERNS = {
        'cgst': r'cgst|central\s*tax',
        'sgst': r'sgst|state\s*tax',
        'igst': r'igst|integrated\s*tax'
    }
    
    def __init__(self):
        """Initialize extraction service"""
        self.confidence_scores = {}
    
    def extract_all(self, ocr_text: str, use_ai: bool = False) -> Dict:
        """Extract all invoice fields"""
        try:
            logger.info("Starting invoice data extraction")
            
            extraction = {
                'vendor_name': self._extract_vendor_name(ocr_text),
                'vendor_gstin': self._extract_gstin(ocr_text, 'vendor'),
                'buyer_gstin': self._extract_gstin(ocr_text, 'buyer'),
                'invoice_number': self._extract_invoice_number(ocr_text),
                'invoice_date': self._extract_invoice_date(ocr_text),
                'items': self._extract_items(ocr_text),
                'taxes': self._extract_taxes(ocr_text),
                'transporter_name': self._extract_transporter(ocr_text),
                'vehicle_number': self._extract_vehicle_number(ocr_text),
                'lr_number': self._extract_lr_number(ocr_text),
                'confidence_scores': self.confidence_scores
            }
            
            # Calculate totals
            extraction['totals'] = self._calculate_totals(
                extraction['items'],
                extraction['taxes']
            )
            
            logger.info(f"✅ Extraction complete with confidence: {extraction['confidence_scores'].get('overall', 0):.2f}")
            return extraction
            
        except Exception as e:
            logger.error(f"Extraction failed: {str(e)}")
            return {'error': str(e), 'confidence_scores': {}}
    
    def _extract_vendor_name(self, text: str) -> str:
        """Extract vendor/supplier name"""
        try:
            # Look for "From" or "Supplier" sections
            patterns = [
                r'(?:from|supplier|sold\s*by|vendor)[:\s]+([A-Za-z\s,\.\-]+?)(?=\n|to|bill|invoice)',
                r'^([A-Za-z\s,\.\-]+?)(?=\n.*?(?:gstin|tax|invoice|bill))',
            ]
            
            text_lower = text.lower()
            
            for pattern in patterns:
                match = re.search(pattern, text_lower, re.IGNORECASE | re.MULTILINE)
                if match:
                    vendor = match.group(1).strip()
                    if vendor and len(vendor) > 2:
                        self.confidence_scores['vendor_name'] = 0.9
                        return vendor
            
            self.confidence_scores['vendor_name'] = 0.3
            return ""
        except Exception as e:
            logger.warning(f"Vendor name extraction failed: {str(e)}")
            return ""
    
    def _extract_gstin(self, text: str, gstin_type: str = 'vendor') -> str:
        """Extract GSTIN"""
        try:
            matches = re.findall(self.GSTIN_PATTERN, text)
            
            if matches:
                gstin = matches[0]
                self.confidence_scores[f'{gstin_type}_gstin'] = 0.95
                return gstin
            
            self.confidence_scores[f'{gstin_type}_gstin'] = 0.0
            return ""
        except Exception as e:
            logger.warning(f"GSTIN extraction failed: {str(e)}")
            return ""
    
    def _extract_invoice_number(self, text: str) -> Tuple[str, float]:
        """Extract invoice number with confidence scoring"""
        try:
            candidates = []
            text_lines = text.split('\n')
            
            for keyword_pattern in self.INVOICE_KEYWORDS:
                for i, line in enumerate(text_lines):
                    if re.search(keyword_pattern, line, re.IGNORECASE):
                        # Get the value after the keyword
                        match = re.search(
                            keyword_pattern + r'[:\s]*([A-Za-z0-9\-/]+)',
                            line,
                            re.IGNORECASE
                        )
                        if match:
                            number = match.group(1).strip()
                            if number and len(number) < 30:
                                candidates.append({
                                    'number': number,
                                    'confidence': self._score_invoice_number(number, keyword_pattern),
                                    'context': line
                                })
            
            if candidates:
                best = max(candidates, key=lambda x: x['confidence'])
                self.confidence_scores['invoice_number'] = best['confidence']
                return best['number'], best['confidence']
            
            self.confidence_scores['invoice_number'] = 0.0
            return "", 0.0
        except Exception as e:
            logger.warning(f"Invoice number extraction failed: {str(e)}")
            return "", 0.0
    
    def _score_invoice_number(self, number: str, keyword: str) -> float:
        """Score invoice number quality"""
        score = 0.5
        
        # Prefer numbers with dashes or slashes
        if '-' in number or '/' in number:
            score += 0.2
        
        # Prefer alphanumeric
        if any(c.isalpha() for c in number):
            score += 0.15
        
        # Prefer reasonable length (4-20 chars)
        if 4 <= len(number) <= 20:
            score += 0.15
        
        return min(score, 1.0)
    
    def _extract_invoice_date(self, text: str) -> Tuple[str, float]:
        """Extract invoice date"""
        try:
            candidates = []
            
            for pattern in self.DATE_PATTERNS:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    date_str = match.group(0)
                    try:
                        # Try to parse and validate
                        parsed = self._parse_date(date_str)
                        if parsed:
                            candidates.append({
                                'date': date_str,
                                'parsed': parsed,
                                'confidence': 0.85
                            })
                    except:
                        pass
            
            if candidates:
                # Prefer more recent dates
                best = max(candidates, key=lambda x: x['parsed'])
                self.confidence_scores['invoice_date'] = best['confidence']
                return best['date'], best['confidence']
            
            self.confidence_scores['invoice_date'] = 0.0
            return "", 0.0
        except Exception as e:
            logger.warning(f"Date extraction failed: {str(e)}")
            return "", 0.0
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string"""
        date_formats = [
            '%d-%m-%Y', '%d/%m/%Y',
            '%Y-%m-%d', '%Y/%m/%d',
            '%d %b %Y', '%d %B %Y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
        return None
    
    def _extract_items(self, text: str) -> List[Dict]:
        """Extract line items"""
        try:
            items = []
            
            # Pattern for item lines (description, qty, unit, rate, amount)
            item_pattern = r'([A-Za-z\s\.\-0-9]+?)\s+(\d+\.?\d*)\s+([A-Za-z]{1,10})\s+([0-9]+\.?\d*)\s+([0-9]+\.?\d*)'
            
            matches = re.finditer(item_pattern, text, re.IGNORECASE)
            
            for match in matches:
                item = {
                    'name': match.group(1).strip(),
                    'quantity': float(match.group(2)),
                    'unit': match.group(3).strip(),
                    'rate': float(match.group(4)),
                    'amount': float(match.group(5))
                }
                items.append(item)
            
            self.confidence_scores['items'] = min(0.8, 0.5 + len(items) * 0.1)
            return items
        except Exception as e:
            logger.warning(f"Item extraction failed: {str(e)}")
            return []
    
    def _extract_taxes(self, text: str) -> Dict[str, float]:
        """Extract tax amounts"""
        try:
            taxes = {'cgst': 0.0, 'sgst': 0.0, 'igst': 0.0}
            
            for tax_name, tax_pattern in self.TAX_PATTERNS.items():
                pattern = tax_pattern + r'[:\s]*[Rs.]*\s*([0-9]+\.?\d*)'
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    taxes[tax_name] = float(match.group(1))
            
            self.confidence_scores['taxes'] = 0.85 if any(taxes.values()) else 0.3
            return taxes
        except Exception as e:
            logger.warning(f"Tax extraction failed: {str(e)}")
            return {'cgst': 0.0, 'sgst': 0.0, 'igst': 0.0}
    
    def _extract_transporter(self, text: str) -> str:
        """Extract transporter name"""
        try:
            pattern = r'(?:transporter|carrier)[:\s]+([A-Za-z\s,\.\-]+?)(?=\n|vehicle|lr)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                self.confidence_scores['transporter'] = 0.8
                return match.group(1).strip()
            self.confidence_scores['transporter'] = 0.0
            return ""
        except Exception as e:
            logger.warning(f"Transporter extraction failed: {str(e)}")
            return ""
    
    def _extract_vehicle_number(self, text: str) -> str:
        """Extract vehicle number"""
        try:
            # Indian vehicle number pattern: 2 letters + 2 digits + 2 letters + 4 digits
            pattern = r'(?:vehicle|lorry|truck|reg)[:\s]*([A-Z]{2}\s?\d{2}\s?[A-Z]{2}\s?\d{4})'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                self.confidence_scores['vehicle_number'] = 0.9
                return match.group(1).replace(' ', '')
            self.confidence_scores['vehicle_number'] = 0.0
            return ""
        except Exception as e:
            logger.warning(f"Vehicle number extraction failed: {str(e)}")
            return ""
    
    def _extract_lr_number(self, text: str) -> str:
        """Extract LR (Lorry Receipt) number"""
        try:
            pattern = r'(?:lr|lorry\s*receipt)[:\s]*([A-Za-z0-9\-/]+?)(?=\n|\s{2,}|date|total)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                self.confidence_scores['lr_number'] = 0.85
                return match.group(1).strip()
            self.confidence_scores['lr_number'] = 0.0
            return ""
        except Exception as e:
            logger.warning(f"LR number extraction failed: {str(e)}")
            return ""
    
    def _calculate_totals(self, items: List[Dict], taxes: Dict) -> Dict:
        """Calculate invoice totals"""
        taxable = sum(item.get('amount', 0) for item in items)
        cgst = taxes.get('cgst', 0)
        sgst = taxes.get('sgst', 0)
        igst = taxes.get('igst', 0)
        total = taxable + cgst + sgst + igst
        
        return {
            'taxable_amount': taxable,
            'cgst_amount': cgst,
            'sgst_amount': sgst,
            'igst_amount': igst,
            'total_amount': total
        }
