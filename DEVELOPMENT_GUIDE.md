# Invoice Narration Generator - Development Guide

## Project Overview

The Invoice Narration Generator is a production-ready desktop/web application that automatically processes scanned invoices and generates accounting narrations in Tally-compatible format.

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/gauravjstar/invoice-narration-generator.git
cd invoice-narration-generator

# Create environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### 2. Backend Setup (Python/FastAPI)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --port 8000
```

**API Documentation:** http://localhost:8000/docs

### 3. Frontend Setup (React)

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

**Application:** http://localhost:3000

### 4. Docker Setup (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Core Modules

### Backend Services (backend/app/services/)

#### 1. **OCR Service** (`ocr_service.py`)
- Supports: PaddleOCR, EasyOCR, Tesseract OCR
- Features:
  - Image preprocessing (deskew, denoise, contrast enhancement)
  - Confidence-based text extraction
  - PDF support (page-by-page extraction)
  - Automatic rotation correction

```python
from app.services.ocr_service import ocr_service

result = ocr_service.extract_text_from_image("invoice.jpg")
print(result["text"], result["confidence"])
```

#### 2. **AI Extraction Service** (`ai_extraction_service.py`)
- Uses OpenAI GPT-4o API via LangChain
- Extracts structured data:
  - Supplier information
  - Invoice details (number, date, vehicle, transporter)
  - Line items (name, quantity, unit, rate, amount)
  - Tax details (CGST, SGST, IGST, total)
- Validation and confidence scoring

```python
from app.services.ai_extraction_service import ai_extraction_service

extraction = ai_extraction_service.extract_invoice_data(ocr_text)
validation = ai_extraction_service.validate_extraction(extraction)
```

#### 3. **Narration Generator** (`narration_generator.py`)
- Generates Tally-compatible single-line narrations
- Format: "Being Purchase Bill No. {invoice_number} dated {date} for purchase of {items}. Taxable Amount Rs. {amount}, CGST Rs. {cgst}, SGST Rs. {sgst}, IGST Rs. {igst}, Total Amount Rs. {total}, Through Transporter {transporter}, LR No. {lr_number}."
- Indian number formatting (comma separator)

```python
from app.services.narration_generator import narration_generator

narration = narration_generator.generate_narration(
    invoice_number="4587",
    invoice_date="15-05-2026",
    items=items_list,
    taxable_value=54250.00,
    cgst_amount=4882.50,
    sgst_amount=4882.50,
    igst_amount=0.00,
    total_amount=64015.00,
    transporter_name="ABC Logistics",
    lr_number="LR458965"
)
```

#### 4. **Excel Export Service** (`excel_export_service.py`)
- Export to Excel (.xlsx)
- Export to CSV
- Supports batch processing
- Formatted columns with proper widths and styling

```python
from app.services.excel_export_service import excel_export_service

output_path = excel_export_service.export_to_excel(invoices_list, "output.xlsx")
```

### Database Models (backend/app/models/)

**Invoice Model:**
```python
class Invoice(Base):
    __tablename__ = "invoices"
    
    id: UUID
    file_name: str
    supplier_name: str
    gst_number: Optional[str]
    invoice_number: str
    invoice_date: datetime
    vehicle_number: Optional[str]
    transporter_name: Optional[str]
    lr_number: Optional[str]
    taxable_value: float
    cgst_amount: float
    sgst_amount: float
    igst_amount: float
    total_amount: float
    narration: str
    extraction_confidence: float
    created_at: datetime
    updated_at: datetime
```

### API Endpoints (backend/app/api/)

#### Upload & Process Invoice
```
POST /api/invoices/upload
Content-Type: multipart/form-data

Body: file (PDF/JPG/PNG)

Response:
{
    "invoice_id": "uuid",
    "file_name": "invoice.pdf",
    "supplier_name": "ABC Suppliers",
    "invoice_number": "4587",
    "invoice_date": "15-05-2026",
    "items": [...],
    "taxable_value": 54250.00,
    "cgst_amount": 4882.50,
    "sgst_amount": 4882.50,
    "igst_amount": 0.00,
    "total_amount": 64015.00,
    "transporter_name": "ABC Logistics",
    "lr_number": "LR458965",
    "narration": "Being Purchase Bill No. 4587...",
    "extraction_confidence": 0.95,
    "validation": {
        "is_valid": true,
        "issues": [],
        "warnings": []
    }
}
```

#### Get All Invoices
```
GET /api/invoices?page=1&per_page=20

Response: List of invoices with pagination
```

#### Get Invoice Details
```
GET /api/invoices/{invoice_id}

Response: Complete invoice data
```

#### Update Invoice Data
```
PUT /api/invoices/{invoice_id}

Body: Updated fields

Response: Updated invoice
```

#### Batch Upload
```
POST /api/invoices/batch-upload
Content-Type: multipart/form-data

Body: files (multiple files)

Response: Array of processed invoices with status
```

#### Export to Excel
```
POST /api/invoices/export/excel

Body: {
    "invoice_ids": ["uuid1", "uuid2"],
    "format": "xlsx"
}

Response: File download
```

#### Search & Filter
```
GET /api/invoices/search?supplier=ABC&date_from=2026-01-01&date_to=2026-12-31

Response: Filtered invoices
```

#### Duplicate Detection
```
POST /api/invoices/check-duplicates

Body: {
    "invoice_number": "4587",
    "gst_number": "27AABCT1234H1Z0",
    "total_amount": 64015.00
}

Response: {
    "is_duplicate": false,
    "similar_invoices": []
}
```

## Configuration

### Environment Variables (backend/.env)

```env
# Database
DATABASE_URL=postgresql://invoice_user:invoice_password@localhost:5432/invoice_db
DATABASE_ECHO=False

# OpenAI
OPENAI_API_KEY=sk-your-api-key
OPENAI_MODEL=gpt-4o

# OCR
OCR_ENGINE=paddleocr  # paddleocr, tesseract, easyocr
OCR_LANGUAGE=en
OCR_CONFIDENCE_THRESHOLD=0.7

# Application
SECRET_KEY=your-super-secret-key-min-32-chars
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ORIGINS=http://localhost:3000

# File Upload
MAX_UPLOAD_SIZE=52428800  # 50MB
UPLOAD_FOLDER=./uploads

# Batch Processing
BATCH_SIZE_LIMIT=1000
MAX_WORKERS=4
PROCESS_TIMEOUT=300

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Environment
ENVIRONMENT=development
DEBUG=True
```

## Testing

### Backend Tests
```bash
cd backend
pytest -v
pytest --cov=app  # Coverage report
```

### Frontend Tests
```bash
cd frontend
npm test
npm test -- --coverage
```

## Docker Commands

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop services
docker-compose down

# Remove volumes (cleanup)
docker-compose down -v
```

## File Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI entry point
│   ├── config.py              # Configuration settings
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py          # API routes
│   │   └── endpoints/
│   │       ├── invoices.py
│   │       ├── upload.py
│   │       └── export.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ocr_service.py
│   │   ├── ai_extraction_service.py
│   │   ├── narration_generator.py
│   │   ├── excel_export_service.py
│   │   └── duplicate_detection_service.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── invoice_model.py
│   │   └── schemas.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db_config.py
│   │   └── operations.py
│   └── utils/
│       ├── __init__.py
│       ├── file_handler.py
│       ├── validators.py
│       └── audit_logger.py
├── tests/
├── requirements.txt
├── .env.example
└── Dockerfile

frontend/
├── src/
│   ├── components/
│   │   ├── Dashboard.jsx
│   │   ├── UploadSection.jsx
│   │   ├── PreviewSection.jsx
│   │   ├── EditSection.jsx
│   │   ├── BatchProcessing.jsx
│   │   └── SearchFilter.jsx
│   ├── pages/
│   ├── services/
│   │   └── api.js
│   ├── styles/
│   ├── App.jsx
│   └── index.js
├── public/
├── package.json
├── .env.example
└── Dockerfile
```

## Performance Metrics

- **Single Invoice Processing:** < 10 seconds
- **Batch Processing (1000 invoices):** < 2 minutes
- **Duplicate Detection:** < 1 second per invoice
- **Extraction Accuracy:**
  - Invoice Number: > 99%
  - Invoice Date: > 99%
  - Tax Amount: > 99%
  - Item Extraction: > 95%
  - Narration Format: 100% consistency

## Troubleshooting

### OCR Issues
- Check image quality (minimum 300 DPI recommended)
- Ensure document is properly scanned/rotated
- Try different OCR engines (switch in .env)

### AI Extraction Problems
- Verify OpenAI API key is valid
- Check OCR confidence score (should be > 0.7)
- Review logs for extraction warnings

### Database Connection
```bash
# Test PostgreSQL connection
psql postgresql://invoice_user:invoice_password@localhost:5432/invoice_db

# Check container logs
docker-compose logs db
```

### Port Conflicts
- Backend: 8000 (change in docker-compose.yml)
- Frontend: 3000 (change in frontend/.env)
- Database: 5432 (change in docker-compose.yml)

## Contributing

1. Create feature branch: `git checkout -b feature/your-feature`
2. Commit changes: `git commit -am 'Add feature'`
3. Push to branch: `git push origin feature/your-feature`
4. Create Pull Request

## License

MIT License

## Support

For issues and feature requests, open an issue on GitHub.
