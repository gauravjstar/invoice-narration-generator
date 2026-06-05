"""Pydantic schemas for request/response validation"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date

class InvoiceItemSchema(BaseModel):
    """Invoice item schema"""
    item_name: str
    description: Optional[str] = None
    hsn_code: Optional[str] = None
    quantity: float
    unit: str
    rate: float
    amount: float
    item_cgst: float = 0.0
    item_sgst: float = 0.0
    item_igst: float = 0.0
    
    class Config:
        from_attributes = True

class InvoiceExtractedSchema(BaseModel):
    """Extracted invoice data"""
    vendor_name: str
    vendor_gstin: str
    buyer_gstin: Optional[str] = None
    invoice_number: str
    invoice_date: str
    invoice_date_str: str
    taxable_amount: float
    cgst_amount: float
    cgst_percentage: float
    sgst_amount: float
    sgst_percentage: float
    igst_amount: float
    igst_percentage: float
    total_amount: float
    transporter_name: Optional[str] = None
    vehicle_number: Optional[str] = None
    lr_number: Optional[str] = None
    items: List[InvoiceItemSchema]
    extraction_confidence: float
    extraction_mode: str
    ocr_engine_used: str
    narration: str

class InvoiceResponseSchema(BaseModel):
    """Invoice response schema"""
    id: str
    file_name: str
    vendor_name: str
    vendor_gstin: str
    invoice_number: str
    invoice_date: date
    taxable_amount: float
    cgst_amount: float
    sgst_amount: float
    igst_amount: float
    total_amount: float
    narration: str
    extraction_confidence: float
    processing_status: str
    is_duplicate: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class InvoiceDetailSchema(InvoiceResponseSchema):
    """Invoice detail response"""
    items: List[InvoiceItemSchema]
    transporter_name: Optional[str]
    vehicle_number: Optional[str]
    lr_number: Optional[str]
    ocr_engine_used: str
    extraction_mode: str

class BatchUploadResponseSchema(BaseModel):
    """Batch upload response"""
    total_files: int
    successful: int
    failed: int
    invoices: List[InvoiceResponseSchema]
    errors: List[dict] = []

class ExportSchema(BaseModel):
    """Export request schema"""
    invoice_ids: List[str]
    format: str = Field(default="xlsx", regex="^(xlsx|csv)$")

class DuplicateCheckSchema(BaseModel):
    """Duplicate check schema"""
    vendor_gstin: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    total_amount: Optional[float] = None
    invoice_id: Optional[str] = None
