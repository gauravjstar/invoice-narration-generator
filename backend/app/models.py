"""Database Models for Invoice Management"""
from sqlalchemy import Column, String, Float, DateTime, Integer, Boolean, Text, ForeignKey, Enum, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
import enum

Base = declarative_base()

class User(Base):
    """User account"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    invoices = relationship("Invoice", back_populates="user")

class Invoice(Base):
    """Invoice records"""
    __tablename__ = "invoices"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.id"), index=True)
    
    # File information
    file_name = Column(String, index=True)
    file_path = Column(String)
    file_type = Column(String)  # pdf, jpg, png, etc
    upload_date = Column(DateTime, default=datetime.utcnow)
    
    # Vendor information
    vendor_name = Column(String, index=True)
    vendor_gstin = Column(String, index=True)
    buyer_gstin = Column(String, index=True, nullable=True)
    
    # Invoice details
    invoice_number = Column(String, index=True)
    invoice_date = Column(Date, index=True)
    invoice_date_str = Column(String)
    
    # Tax details
    taxable_amount = Column(Float, default=0.0)
    cgst_amount = Column(Float, default=0.0)
    cgst_percentage = Column(Float, default=0.0)
    sgst_amount = Column(Float, default=0.0)
    sgst_percentage = Column(Float, default=0.0)
    igst_amount = Column(Float, default=0.0)
    igst_percentage = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    
    # Transportation details
    transporter_name = Column(String, nullable=True)
    vehicle_number = Column(String, nullable=True)
    lr_number = Column(String, nullable=True)
    
    # Extraction metadata
    extraction_confidence = Column(Float, default=0.0)
    extraction_mode = Column(String)  # 'offline', 'ai_enhanced'
    ocr_engine_used = Column(String)  # 'paddleocr', 'easyocr', 'tesseract'
    
    # Processing status
    processing_status = Column(String, default='pending')  # pending, processing, completed, failed
    processing_error = Column(Text, nullable=True)
    
    # Narration
    narration = Column(Text)
    is_duplicate = Column(Boolean, default=False)
    duplicate_of_id = Column(String, ForeignKey("invoices.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="invoice")

class InvoiceItem(Base):
    """Line items in invoices"""
    __tablename__ = "invoice_items"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    invoice_id = Column(String, ForeignKey("invoices.id"), index=True)
    
    # Item details
    item_name = Column(String, index=True)
    description = Column(Text, nullable=True)
    hsn_code = Column(String, nullable=True)
    
    # Quantity details
    quantity = Column(Float)
    unit = Column(String)
    
    # Pricing
    rate = Column(Float)
    amount = Column(Float)
    
    # Tax on item
    item_cgst = Column(Float, default=0.0)
    item_sgst = Column(Float, default=0.0)
    item_igst = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="items")

class AuditLog(Base):
    """Audit trail"""
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    invoice_id = Column(String, ForeignKey("invoices.id"), index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True, nullable=True)
    
    # Action details
    action = Column(String, index=True)  # upload, extract, correct, export, delete
    details = Column(Text)
    status = Column(String)  # success, failed
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    invoice = relationship("Invoice", back_populates="audit_logs")

class ExportHistory(Base):
    """Export history tracking"""
    __tablename__ = "export_history"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.id"), index=True)
    
    # Export details
    export_format = Column(String)  # xlsx, csv
    file_name = Column(String)
    file_path = Column(String)
    invoice_count = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User")
