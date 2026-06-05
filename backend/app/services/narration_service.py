"""Narration generation service for Tally-compatible accounting entries"""
import logging
from typing import List, Dict, Optional
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class NarrationService:
    """Generate professional accounting narrations"""
    
    @staticmethod
    def generate_narration(
        invoice_number: str,
        invoice_date: str,
        items: List[Dict],
        taxable_amount: float,
        cgst_amount: float = 0.0,
        sgst_amount: float = 0.0,
        igst_amount: float = 0.0,
        total_amount: float = 0.0,
        transporter_name: Optional[str] = None,
        vehicle_number: Optional[str] = None,
        lr_number: Optional[str] = None,
        vendor_name: Optional[str] = None
    ) -> str:
        """
        Generate Tally-compatible narration.
        
        Format:
        Being Purchase Bill No. {invoice_number} dated {date} for purchase of 
        {normalized_items}. Taxable Amount Rs. {taxable}, CGST Rs. {cgst}, 
        SGST Rs. {sgst}, IGST Rs. {igst}, Total Amount Rs. {total}
        Through Transporter {transporter}, Vehicle {vehicle}, LR No. {lr}.
        """
        try:
            # Format amounts with Indian number system
            taxable_formatted = NarrationService._format_amount(taxable_amount)
            cgst_formatted = NarrationService._format_amount(cgst_amount)
            sgst_formatted = NarrationService._format_amount(sgst_amount)
            igst_formatted = NarrationService._format_amount(igst_amount)
            total_formatted = NarrationService._format_amount(total_amount)
            
            # Build items description
            items_text = NarrationService._build_items_text(items)
            
            # Parse date
            parsed_date = NarrationService._parse_date(invoice_date)
            if not parsed_date:
                parsed_date = invoice_date
            
            # Start building narration
            narration = f"Being Purchase Bill No. {invoice_number} dated {parsed_date}"
            
            # Add vendor if available
            if vendor_name and len(vendor_name) > 2:
                narration += f" from {vendor_name}"
            
            # Add items
            if items_text:
                narration += f" for purchase of {items_text}"
            
            # Add amounts
            narration += f". Taxable Amount Rs. {taxable_formatted}"
            
            if cgst_amount > 0:
                narration += f", CGST Rs. {cgst_formatted}"
            if sgst_amount > 0:
                narration += f", SGST Rs. {sgst_formatted}"
            if igst_amount > 0:
                narration += f", IGST Rs. {igst_formatted}"
            
            narration += f", Total Amount Rs. {total_formatted}"
            
            # Add transportation details
            transport_parts = []
            if transporter_name and len(transporter_name) > 2:
                transport_parts.append(f"Transporter {transporter_name}")
            if vehicle_number and len(vehicle_number) > 2:
                transport_parts.append(f"Vehicle {vehicle_number}")
            if lr_number and len(lr_number) > 2:
                transport_parts.append(f"LR No. {lr_number}")
            
            if transport_parts:
                narration += ", Through " + ", ".join(transport_parts)
            
            narration += "."
            
            logger.info(f"✅ Narration generated: {len(narration)} characters")
            return narration
            
        except Exception as e:
            logger.error(f"Narration generation failed: {str(e)}")
            return ""
    
    @staticmethod
    def _build_items_text(items: List[Dict]) -> str:
        """Build normalized item descriptions"""
        if not items:
            return ""
        
        item_descriptions = []
        
        for item in items[:5]:  # Limit to first 5 items in narration
            name = item.get('name', '').strip()
            rate = item.get('rate', 0)
            
            if name:
                # Normalize item name
                normalized_name = NarrationService._normalize_item_name(name)
                formatted_rate = NarrationService._format_amount(rate)
                item_descriptions.append(f"{normalized_name} @ Rs. {formatted_rate}")
        
        # Join with commas
        if len(item_descriptions) == 1:
            return item_descriptions[0]
        elif len(item_descriptions) <= 3:
            return ", ".join(item_descriptions)
        else:
            return ", ".join(item_descriptions[:3]) + " etc."
    
    @staticmethod
    def _normalize_item_name(name: str) -> str:
        """Normalize item name for narration"""
        # Remove extra spaces
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Common normalizations
        normalizations = {
            r'\bM\.S\b|\bMS\b|\bmild\s*steel\b': 'MS',
            r'\bHR\b|\bhigh\s*rise\b': 'HR',
            r'\bCR\b|\bcold\s*rolled\b': 'CR',
            r'\bP\.P\b|\bPP\b': 'PP',
            r'\bP\.V\.C\b|\bPVC\b': 'PVC',
            r'\bG\.I\b|\bGI\b': 'GI',
            r'\bFRP\b': 'FRP',
        }
        
        for pattern, replacement in normalizations.items():
            name = re.sub(pattern, replacement, name, flags=re.IGNORECASE)
        
        # Capitalize first letter of each significant word
        words = name.split()
        words = [w.capitalize() if len(w) > 2 else w.upper() for w in words]
        
        return ' '.join(words)
    
    @staticmethod
    def _format_amount(amount: float) -> str:
        """Format amount with Indian number system (comma separators)"""
        try:
            if amount is None or amount == 0:
                return "0.00"
            
            # Convert to string with 2 decimals
            amount_str = f"{float(amount):.2f}"
            integer_part, decimal_part = amount_str.split('.')
            
            # Handle negative numbers
            is_negative = integer_part.startswith('-')
            integer_part = integer_part.lstrip('-')
            
            # Apply Indian numbering (10,00,000 format)
            if len(integer_part) <= 2:
                formatted_integer = integer_part
            else:
                # Reverse for easier processing
                reversed_int = integer_part[::-1]
                parts = []
                
                # First part (rightmost 3 digits)
                parts.append(reversed_int[:3][::-1])
                remaining = reversed_int[3:]
                
                # Remaining parts (2 digits each)
                while remaining:
                    if len(remaining) >= 2:
                        parts.append(remaining[:2][::-1])
                        remaining = remaining[2:]
                    else:
                        parts.append(remaining[::-1])
                        remaining = ""
                
                # Join parts with commas
                formatted_integer = ",".join(reversed(parts))
            
            formatted = f"{formatted_integer}.{decimal_part}"
            if is_negative:
                formatted = f"-{formatted}"
            
            return formatted
        except Exception as e:
            logger.warning(f"Amount formatting failed: {str(e)}")
            return f"{amount:.2f}"
    
    @staticmethod
    def _parse_date(date_str: str) -> str:
        """Parse and standardize date format"""
        try:
            from datetime import datetime
            
            date_formats = [
                '%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d', '%Y/%m/%d',
                '%d %b %Y', '%d %B %Y', '%d.%m.%Y'
            ]
            
            for fmt in date_formats:
                try:
                    parsed = datetime.strptime(date_str, fmt)
                    return parsed.strftime('%d-%m-%Y')
                except ValueError:
                    continue
            
            # Return as-is if no format matches
            return date_str
        except Exception as e:
            logger.warning(f"Date parsing failed: {str(e)}")
            return date_str
