"""Narration Generator Service"""
import logging
from typing import List
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class InvoiceItem(BaseModel):
    item_name: str
    quantity: float
    unit: str
    rate: float
    amount: float

class NarrationGenerator:
    """Generate accounting narrations for invoices"""
    
    @staticmethod
    def generate_narration(
        invoice_number: str,
        invoice_date: str,
        items: List[InvoiceItem],
        taxable_value: float,
        cgst_amount: float,
        sgst_amount: float,
        igst_amount: float,
        total_amount: float,
        transporter_name: str = "",
        lr_number: str = ""
    ) -> str:
        """
        Generate accounting narration in Tally-compatible format
        """
        try:
            # Build items part
            items_text = NarrationGenerator._build_items_text(items)
            
            # Format amounts
            taxable_amount = NarrationGenerator._format_amount(taxable_value)
            cgst_amt = NarrationGenerator._format_amount(cgst_amount)
            sgst_amt = NarrationGenerator._format_amount(sgst_amount)
            igst_amt = NarrationGenerator._format_amount(igst_amount)
            total_amt = NarrationGenerator._format_amount(total_amount)
            
            # Build narration
            narration = f"Being Purchase Bill No. {invoice_number} dated {invoice_date} for purchase of {items_text}. "
            narration += f"Taxable Amount Rs. {taxable_amount}, CGST Rs. {cgst_amt}, SGST Rs. {sgst_amt}, IGST Rs. {igst_amt}, "
            narration += f"Total Amount Rs. {total_amt}"
            
            # Add transporter and LR if available
            if transporter_name:
                narration += f", Through Transporter {transporter_name}"
            if lr_number:
                narration += f", LR No. {lr_number}"
            
            narration += "."
            
            logger.info("✅ Narration generated successfully")
            return narration
            
        except Exception as e:
            logger.error(f"Narration generation failed: {str(e)}")
            return ""
    
    @staticmethod
    def _build_items_text(items: List[InvoiceItem]) -> str:
        """Build items text for narration"""
        if not items:
            return ""
        
        item_parts = []
        for item in items:
            rate = NarrationGenerator._format_amount(item.rate)
            item_parts.append(f"{item.item_name} Rate {rate}")
        
        return ", ".join(item_parts)
    
    @staticmethod
    def _format_amount(amount: float) -> str:
        """Format amount with Indian comma separator"""
        try:
            amount_str = f"{amount:.2f}"
            integer_part, decimal_part = amount_str.split('.')
            
            if len(integer_part) <= 2:
                formatted = integer_part
            else:
                reversed_int = integer_part[::-1]
                parts = []
                
                if len(reversed_int) >= 3:
                    parts.append(reversed_int[:3][::-1])
                    remaining = reversed_int[3:]
                else:
                    parts.append(reversed_int[::-1])
                    remaining = ""
                
                while remaining:
                    if len(remaining) >= 2:
                        parts.append(remaining[:2][::-1])
                        remaining = remaining[2:]
                    else:
                        parts.append(remaining[::-1])
                        remaining = ""
                
                formatted = ",".join(reversed(parts))
            
            return f"{formatted}.{decimal_part}"
        except Exception as e:
            logger.warning(f"Amount formatting failed: {str(e)}")
            return f"{amount:.2f}"

narration_generator = NarrationGenerator()
