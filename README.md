# TISON miRNA WebAPI

A FastAPI-based WebAPI for miRNA information, expression analysis, and breast cancer (TCGA-BRCA) data.

## Project Overview

This project provides an API for working with miRNA data and their expression in cancer samples.

The current implementation focuses on:

- Human miRNA information
- TCGA-BRCA breast cancer miRNA expression
- Tumor and normal sample comparison
- Differential miRNA expression analysis
- Statistical testing and FDR correction
- PostgreSQL database storage

## Technology Stack

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Pandas
- SciPy
- Statsmodels
- Uvicorn

## Current WebAPI

The API provides endpoints for:

- miRNA listing and search
- miRNA expression retrieval
- sample-level expression
- tumor vs normal comparison
- differential expression analysis
- significant miRNA results
- CSV export of differential results

## Data

The current analysis uses miRNA expression data from:

**TCGA-BRCA — Breast Invasive Carcinoma**

The database currently contains miRNA expression data for:

- Primary Tumor
- Solid Tissue Normal
- Metastatic samples

## Running the API

Create and activate a Python virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
http://localhost:8000/docs
```
