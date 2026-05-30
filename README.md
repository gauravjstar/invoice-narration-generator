# Invoice Narration Generator

A production-ready desktop/web application that automatically reads scanned invoices (PDF, JPG, JPEG, PNG), extracts invoice data using OCR and AI, generates accounting narrations in a predefined format, and exports results to Excel.

## Features

- **Advanced OCR Processing**: Support for PDF, JPG, JPEG, PNG, scanned invoices, and low-quality documents
- **AI-Powered Data Extraction**: Extract vendor info, invoice details, item details, and tax information
- **Automatic Narration Generation**: Generate accounting narrations in Tally-compatible format
- **Batch Processing**: Process 1000+ invoices in a single batch
- **Duplicate Detection**: Intelligent duplicate invoice detection
- **Excel Export**: Multi-format export (Excel, CSV, PDF)
- **User Correction Interface**: Manual editing and AI learning capabilities
- **Audit Logs**: Complete audit trail for compliance

## Project Structure

```
invoice-narration-generator/
├── frontend/          # React.js Frontend
├── backend/           # Python FastAPI Backend
├── docker-compose.yml # Docker orchestration
└── README.md
```

## Technology Stack

### Frontend
- React.js
- Material-UI
- Axios for API calls

### Backend
- Python 3.10+
- FastAPI
- PostgreSQL
- PaddleOCR / Tesseract OCR / EasyOCR
- GPT-4o API via LangChain
- OpenPyXL / Pandas

### DevOps
- Docker & Docker Compose
- PostgreSQL Container

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.10+
- Node.js 16+
- PostgreSQL (or use Docker)

### Setup with Docker

```bash
# Clone the repository
git clone https://github.com/gauravjstar/invoice-narration-generator.git
cd invoice-narration-generator

# Create .env files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Configure environment variables
# Edit backend/.env and frontend/.env with your settings

# Start all services
docker-compose up -d
```

### Manual Setup

#### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure .env
cp .env.example .env

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```

#### Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env
npm start
```

## API Documentation

Once the backend is running, visit: `http://localhost:8000/docs`

## Configuration

### Backend Environment Variables

```env
DATABASE_URL=postgresql://user:password@localhost:5432/invoice_db
OPENAI_API_KEY=your_openai_api_key
OCR_ENGINE=paddleocr  # paddleocr, tesseract, or easyocr
LOG_LEVEL=INFO
```

### Frontend Environment Variables

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_MAX_FILE_SIZE=50  # MB
```

## Usage

### Web Interface

1. Open `http://localhost:3000`
2. Upload invoice images (drag & drop or browse)
3. Review extracted data in preview section
4. Edit fields as needed
5. Generate narration (automatic or manual)
6. Export to Excel

### Batch Processing

1. Upload multiple files (up to 1000)
2. System processes all invoices automatically
3. Review results
4. Export batch to Excel

## Narration Format

```
Being Purchase Bill No. {Invoice Number} dated {Invoice Date} for purchase of {Item Name 1} Rate {Rate 1}, {Item Name 2} Rate {Rate 2}, {Item Name N} Rate {Rate N}. Taxable Amount Rs. {Taxable Amount}, CGST Rs. {CGST Amount}, SGST Rs. {SGST Amount}, IGST Rs. {IGST Amount}, Total Amount Rs. {Total Amount}, Through Transporter {Transporter Name}, LR No. {LR Number}.
```

### Example

```
Being Purchase Bill No. 4587 dated 15-05-2026 for purchase of MS Pipe Rate 145.50, MS Sheet Rate 78.25, Welding Rod Rate 250.00. Taxable Amount Rs. 54,250.00, CGST Rs. 4,882.50, SGST Rs. 4,882.50, IGST Rs. 0.00, Total Amount Rs. 64,015.00, Through Transporter ABC Logistics, LR No. LR458965.
```

## Excel Export Format

| File Name | Supplier Name | Invoice No | Invoice Date | Taxable Amount | CGST | SGST | IGST | Total Amount | Transporter | LR No | Narration |
|-----------|---------------|-----------|--------------|----------------|------|------|------|--------------|-------------|-------|----------|

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for production deployment guide, including:
- Docker production build
- AWS/Azure deployment
- Windows executable generation
- Database backup strategies

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Accuracy Targets

- Invoice Number: >99%
- Invoice Date: >99%
- Tax Amount: >99%
- Item Extraction: >95%
- Narration Format: 100% consistency

## Audit & Compliance

- Complete audit logs for all operations
- User action tracking
- Data correction history
- Compliance reports

## Performance

- Single invoice processing: <10 seconds
- Batch processing (1000 invoices): <2 minutes
- Duplicate detection: <1 second per invoice

## License

MIT License

## Support

For issues and feature requests, please open an issue on GitHub.
