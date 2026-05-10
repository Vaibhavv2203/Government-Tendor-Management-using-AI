# Tender Analysis System

An AI-powered tender matching and analysis platform built using Streamlit and Google Gemini AI.

The application automatically scans tender PDF documents, extracts content, and analyzes their relevance for different companies based on services, keywords, industry type, and geographical focus. It helps organizations identify suitable tenders and make informed bidding decisions using AI-generated insights and relevance scoring.

---

## Features

- Automated tender PDF analysis
- AI-powered relevance scoring
- Company profile management
- Tender-to-company matching
- Industry and keyword analysis
- Geographic relevance detection
- AI-generated tender summaries
- Recommendation system for bidding decisions
- JSON and CSV export support
- Local company storage using JSON
- Batch analysis of multiple tender files

---

## Tech Stack

- Python
- Streamlit
- Google Gemini AI
- Pandas
- PyPDF2
- JSON
- Glob
- Pathlib

---

## Project Workflow

1. Add company profiles with:
   - Services
   - Keywords
   - Industry
   - Geographical focus

2. Upload or place tender PDF files into the tenders folder.

3. The system:
   - Extracts text from PDFs
   - Processes tender content
   - Sends data to Gemini AI

4. Gemini AI analyzes:
   - Service alignment
   - Keyword matching
   - Industry relevance
   - Geographic relevance

5. The system generates:
   - Relevance scores
   - Tender summaries
   - Key requirements
   - Recommendation to bid or not

6. Results can be downloaded as:
   - JSON
   - CSV

---

## Folder Structure

```text
project-folder/
│
├── Main.py
├── companies.json
├── requirements.txt
├── TENDERS_FOLDER/
│   ├── tender1.pdf
│   ├── tender2.pdf
│   └── ...
