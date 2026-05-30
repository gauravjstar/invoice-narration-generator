# Production Deployment Guide

## Table of Contents

1. [Docker Production Build](#docker-production-build)
2. [Database Setup](#database-setup)
3. [Environment Configuration](#environment-configuration)
4. [AWS Deployment](#aws-deployment)
5. [Azure Deployment](#azure-deployment)
6. [Windows Executable](#windows-executable)
7. [Monitoring & Logging](#monitoring--logging)
8. [Backup & Recovery](#backup--recovery)

## Docker Production Build

### Build Images

```bash
# Build backend image
docker build -f backend/Dockerfile -t invoice-narration-generator-backend:latest ./backend

# Build frontend image
docker build -f frontend/Dockerfile -t invoice-narration-generator-frontend:latest ./frontend
```

### Push to Registry

```bash
# Docker Hub
docker tag invoice-narration-generator-backend:latest gauravjstar/invoice-narration-generator-backend:latest
docker push gauravjstar/invoice-narration-generator-backend:latest

# AWS ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker tag invoice-narration-generator-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/invoice-narration-generator-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/invoice-narration-generator-backend:latest
```

## Database Setup

### PostgreSQL Production Configuration

```sql
-- Create database
CREATE DATABASE invoice_db;

-- Create user with privileges
CREATE USER invoice_user WITH PASSWORD 'secure_password';
ALTER ROLE invoice_user SET client_encoding TO 'utf8';
ALTER ROLE invoice_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE invoice_user SET default_transaction_deferrable TO on;
GRANT ALL PRIVILEGES ON DATABASE invoice_db TO invoice_user;

-- Enable required extensions
\c invoice_db
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
```

### Backup Strategy

```bash
# Daily backup
0 2 * * * pg_dump -U invoice_user -h localhost invoice_db > /backups/invoice_db_$(date +\%Y\%m\%d).sql

# Upload to S3
0 3 * * * aws s3 cp /backups/invoice_db_*.sql s3://invoice-backups/ --delete
```

## Environment Configuration

### Production .env

```env
# Backend
DATABASE_URL=postgresql://invoice_user:secure_password@prod-db.example.com:5432/invoice_db
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
OCR_ENGINE=paddleocr
LOG_LEVEL=INFO
SECRET_KEY=your-super-secret-key-min-32-chars
ALLOWED_HOSTS=api.example.com,*.example.com
CORS_ORIGINS=https://app.example.com
MAX_UPLOAD_SIZE=52428800  # 50MB
BATCH_SIZE_LIMIT=1000

# Frontend
REACT_APP_API_URL=https://api.example.com
REACT_APP_MAX_FILE_SIZE=50

# Email (for notifications)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## AWS Deployment

### Using ECS + RDS + S3

```bash
# 1. Create RDS PostgreSQL instance
aws rds create-db-instance \
  --db-instance-identifier invoice-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username invoice_user \
  --master-user-password secure_password \
  --allocated-storage 100 \
  --region us-east-1

# 2. Create S3 bucket for uploads
aws s3 mb s3://invoice-narration-uploads
aws s3api put-bucket-versioning --bucket invoice-narration-uploads --versioning-configuration Status=Enabled

# 3. Create ECS cluster
aws ecs create-cluster --cluster-name invoice-generator

# 4. Register task definitions
aws ecs register-task-definition --cli-input-json file://backend-task-definition.json

# 5. Create services
aws ecs create-service \
  --cluster invoice-generator \
  --service-name invoice-backend \
  --task-definition invoice-backend:1 \
  --desired-count 2 \
  --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:...
```

### CloudFormation Template

Create `infrastructure.yaml`:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Invoice Narration Generator Infrastructure'

Resources:
  InvoiceDBInstance:
    Type: 'AWS::RDS::DBInstance'
    Properties:
      DBInstanceIdentifier: invoice-db
      DBInstanceClass: db.t3.micro
      Engine: postgres
      MasterUsername: invoice_user
      MasterUserPassword: !Ref DBPassword
      AllocatedStorage: '100'
      
  InvoiceUploadBucket:
    Type: 'AWS::S3::Bucket'
    Properties:
      BucketName: invoice-narration-uploads
      VersioningConfiguration:
        Status: Enabled

Parameters:
  DBPassword:
    Type: String
    NoEcho: true
```

## Azure Deployment

### Using App Service + Azure Database for PostgreSQL

```bash
# Create resource group
az group create --name invoice-rg --location eastus

# Create PostgreSQL database
az postgres server create \
  --resource-group invoice-rg \
  --name invoice-db-server \
  --location eastus \
  --admin-user invoice_user \
  --admin-password secure_password \
  --sku-name B_Gen5_1

# Create App Service Plan
az appservice plan create \
  --name invoice-app-plan \
  --resource-group invoice-rg \
  --sku B1 \
  --is-linux

# Create Web App
az webapp create \
  --resource-group invoice-rg \
  --plan invoice-app-plan \
  --name invoice-generator-app \
  --runtime 'PYTHON|3.10'
```

## Windows Executable

### Build .exe with PyInstaller

```bash
# Install PyInstaller
pip install pyinstaller

# Create spec file
pyinstaller --onefile --windowed --icon=icon.ico \
  --add-data "backend/app:app" \
  --add-data "frontend/build:build" \
  backend/app/main.py -n InvoiceNarrationGenerator

# Create installer with NSIS
# (Requires NSIS to be installed)
makensis installer.nsi
```

### NSIS Installer Script

```nsis
; installer.nsi
!include "MUI2.nsh"

; Installer settings
Name "Invoice Narration Generator"
OutFile "InvoiceNarrationGenerator-Setup.exe"
InstallDir "$PROGRAMFILES\InvoiceNarrationGenerator"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

; Installation
Section "Install"
  SetOutPath "$INSTDIR"
  File "dist\InvoiceNarrationGenerator.exe"
  CreateDirectory "$SMPROGRAMS\InvoiceNarrationGenerator"
  CreateShortCut "$SMPROGRAMS\InvoiceNarrationGenerator\Invoice Narration Generator.lnk" "$INSTDIR\InvoiceNarrationGenerator.exe"
SectionEnd
```

## Monitoring & Logging

### ELK Stack Setup

```yaml
# docker-compose-monitoring.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"

  kibana:
    image: docker.elastic.co/kibana/kibana:8.0.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200

  logstash:
    image: docker.elastic.co/logstash/logstash:8.0.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    ports:
      - "5000:5000"
```

### Application Logging

```python
# backend/app/utils/logger.py
import logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger()
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)
```

## Backup & Recovery

### Automated Backup

```python
# backend/app/utils/backup.py
import subprocess
from datetime import datetime
import boto3

def backup_database():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'invoice_db_backup_{timestamp}.sql'
    
    # Create backup
    subprocess.run([
        'pg_dump',
        '-U', 'invoice_user',
        '-h', 'localhost',
        'invoice_db'
    ], stdout=open(filename, 'w'))
    
    # Upload to S3
    s3 = boto3.client('s3')
    s3.upload_file(filename, 'invoice-backups', filename)
    
    return filename

# Schedule with APScheduler
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(backup_database, 'cron', hour=2, minute=0)
scheduler.start()
```

## Health Checks

```python
# backend/app/api/health.py
from fastapi import APIRouter, Depends
from sqlalchemy import text
from app.database.db_config import get_db

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health_check(db = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}, 503
```

## Performance Optimization

### Database Optimization

```sql
-- Create indexes for common queries
CREATE INDEX idx_invoice_number ON invoices(invoice_number);
CREATE INDEX idx_invoice_date ON invoices(invoice_date);
CREATE INDEX idx_supplier_name ON invoices(supplier_name);
CREATE INDEX idx_created_at ON invoices(created_at);

-- For full-text search
CREATE INDEX idx_narration_search ON invoices USING GIN(to_tsvector('english', narration));
```

### API Rate Limiting

```python
# backend/app/middleware/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/invoices")
@limiter.limit("100/minute")
async def get_invoices(request: Request):
    # Implementation
    pass
```

## Disaster Recovery Plan

### RTO & RPO Targets
- **RTO (Recovery Time Objective)**: 1 hour
- **RPO (Recovery Point Objective)**: 15 minutes

### Recovery Procedures

1. **Database Failure**: Restore from latest backup within 15 minutes
2. **Application Failure**: Restart container from image
3. **Complete Failure**: Restore from AWS/Azure backup snapshot

## Rollback Strategy

```bash
# Blue-Green Deployment
# Keep two production environments running

# Deploy to green environment
docker-compose -f docker-compose.green.yml up -d

# Run tests
./run-tests.sh

# If successful, switch traffic to green
aws elbv2 modify-target-group --target-group-arn arn:aws:... --new-targets Id=green-instance-1 Id=green-instance-2

# Old blue environment remains running for quick rollback
```
