# AI-Enhanced Survey Data Processing Application

An AI-augmented web application for automated survey data preprocessing, statistical estimation, and report generation for official statistical agencies.

## Project Structure

```
├── backend/              # Python/Django backend services
│   ├── api/             # REST API endpoints
│   ├── data_processing/ # Statistical algorithms and data cleaning
│   ├── reports/         # Report generation and templates
│   └── requirements.txt # Python dependencies
├── frontend/            # React frontend application
│   ├── src/            # Source code
│   ├── public/         # Static assets
│   └── package.json    # Node.js dependencies
├── database/           # Database schemas and migrations
├── docker/             # Docker configuration
├── docs/               # Documentation
└── tests/              # Test suites
```

## Features

- **Data Input**: CSV/Excel upload with schema mapping
- **Data Cleaning**: Missing value imputation, outlier detection, rule-based validation
- **Weight Application**: Survey weights with statistical estimation
- **Report Generation**: Automated PDF/HTML reports with visualizations
- **User Interface**: Intuitive drag-and-drop configuration interface

## Quick Start

1. Set up backend services:
   ```bash
   cd backend
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py runserver
   ```

2. Set up frontend:
   ```bash
   cd frontend
   npm install
   npm start
   ```

## Technology Stack

- **Backend**: Python, Django REST Framework, PostgreSQL, Celery, Redis
- **Frontend**: React, TypeScript, Material-UI, Chart.js
- **Data Processing**: Pandas, NumPy, SciPy, Scikit-learn, Statsmodels
- **Reports**: ReportLab, Jinja2, Plotly
- **Infrastructure**: Docker, GitHub Actions, Nginx

## Government of India MoSPI Initiative

This project supports MoSPI's objective of improving data quality and efficiency through automation and AI integration in data processing, enhancing reproducibility and reducing delays in producing official statistics.