"""Excel Export Service for invoice data"""
import logging
from typing import List, Dict
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)

class ExcelExportService:
    """Export invoice data to Excel format"""
    
    COLUMNS = [
        ("File Name", 30),
        ("Supplier Name", 25),
        ("Invoice No", 15),
        ("Invoice Date", 15),
        ("Taxable Amount", 18),
        ("CGST", 15),
        ("SGST", 15),
        ("IGST", 15),
        ("Total Amount", 18),
        ("Transporter", 20),
        ("LR No", 15),
        ("Narration", 80)
    ]
    
    @staticmethod
    def export_to_excel(invoices: List[Dict], output_path: str = None) -> str:
        """Export invoices to Excel file"""
        try:
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"invoices_export_{timestamp}.xlsx"
            
            # Create DataFrame
            df = pd.DataFrame(invoices)
            
            # Reorder columns if they exist
            column_order = [
                "file_name", "supplier_name", "invoice_number", "invoice_date",
                "taxable_value", "cgst_amount", "sgst_amount", "igst_amount",
                "total_amount", "transporter_name", "lr_number", "narration"
            ]
            
            existing_cols = [col for col in column_order if col in df.columns]
            if existing_cols:
                df = df[existing_cols]
            
            # Save to Excel
            df.to_excel(output_path, index=False, sheet_name="Invoices")
            logger.info(f"✅ Excel file exported successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Excel export failed: {str(e)}")
            raise
    
    @staticmethod
    def export_to_csv(invoices: List[Dict], output_path: str = None) -> str:
        """Export invoices to CSV file"""
        try:
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"invoices_export_{timestamp}.csv"
            
            df = pd.DataFrame(invoices)
            
            column_order = [
                "file_name", "supplier_name", "invoice_number", "invoice_date",
                "taxable_value", "cgst_amount", "sgst_amount", "igst_amount",
                "total_amount", "transporter_name", "lr_number", "narration"
            ]
            
            existing_cols = [col for col in column_order if col in df.columns]
            if existing_cols:
                df = df[existing_cols]
            
            df.to_csv(output_path, index=False, encoding="utf-8")
            logger.info(f"✅ CSV file exported successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"CSV export failed: {str(e)}")
            raise

excel_export_service = ExcelExportService()
