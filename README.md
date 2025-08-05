# Multi-Service Repository

A collection of Django services with shared utilities for microservices architecture.

## Structure
├── arduino_backend/        # Arduino IoT backend service
├── mountjoy_api/           # Main API service with Notion integration
├── requirements/           # Shared Python dependencies
└── shared/                 # Common utilities (middleware, models, utils)

## Quick Start

```bash
# Setup environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements/base.txt

# Copy environment template
cp .env.example .env

# Run services (separate terminals)
cd arduino_backend && python manage.py runserver 8001
cd mountjoy_api && python manage.py runserver 8002
```

## Services

- Arduino Backend (:8001) - IoT device management and data collection
- Mountjoy API (:8002) - Main application API with external integrations

Each service is a standalone Django project that can be deployed independently while sharing common utilities from the shared/ directory.