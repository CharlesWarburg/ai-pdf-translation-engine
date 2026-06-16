# AI PDF Translator

For setup and first-run instructions, see [SETUP_GUIDE.md](SETUP_GUIDE.md).

## Overview

The AI PDF Translator is a web application that allows users to upload a PDF, select a target language, and receive a translated PDF.

The project was built to explore how AI can be integrated into document processing workflows while solving a practical problem for users.

---

## Problem

Translating PDF documents can be time-consuming and often requires copying content between multiple tools.

The goal of this project was to create a simple workflow that:

- Accepts PDF uploads
- Extracts text automatically
- Translates content using AI
- Generates a downloadable translated PDF

---

## Tech Stack

| Technology | Purpose |
|------------|----------|
| Python | Core application |
| FastAPI | Backend API |
| OpenAI Agents SDK | AI translation |
| pypdf | PDF text extraction |
| ReportLab | PDF generation |
| Docker | Containerisation |
| HTML/CSS/JavaScript | Frontend |
| Pydantic | Configuration & validation |

---

## System Architecture

```text
User Uploads PDF
        ↓
Text Extraction
        ↓
Document Chunking
        ↓
AI Translation
        ↓
Validation
        ↓
PDF Generation
        ↓
Download Result
```

---

## Key Challenges

### 1. Large Documents

Some PDFs exceed what can realistically be sent to an AI model in a single request.

**Solution**

The document is split into smaller chunks which are processed concurrently.

This allows larger files to be handled more efficiently while staying within model limitations.

---

### 2. Translation Quality

AI translations may occasionally miss content or produce inconsistent results.

**Solution**

A second validation agent reviews the translated document and reports confidence metrics and untranslated segments.

This helps identify potential quality issues without impacting the user experience.

---

### 3. Unicode Support

Different languages require support for special characters and non-English alphabets.

**Solution**

DejaVu Sans was embedded into generated PDFs to ensure translated text renders correctly across multiple languages.

---

## Why I Chose The OpenAI Agents SDK

I wanted a structured way to work with AI rather than calling raw model endpoints directly.

The SDK provided:

- Consistent agent configuration
- Clear separation of responsibilities
- Easier extensibility
- Cleaner architecture for future improvements

This also allowed me to introduce a validation agent alongside the translation agent using the same architecture.

---

## Business Value

This type of solution could be used for:

- International business documentation
- Customer support material
- Internal knowledge bases
- Legal and compliance documents
- Localisation workflows

The project demonstrates:

- API integration
- Data processing
- AI workflows
- Error handling
- Application architecture
- Containerisation

---

## Future Improvements

Given more time I would:

- Add OCR support for scanned PDFs
- Preserve original document formatting
- Support additional file types
- Deploy the application to AWS
- Add user accounts and document history
- Implement token-based chunking

---

## Live Demonstration

### Workflow

1. Upload a PDF document
2. Select a target language
3. Submit the translation request
4. Review the translated output
5. Download the translated PDF

---

## What I Learned

This project taught me how to:

- Integrate AI into a production workflow
- Design around model limitations
- Process large documents efficiently
- Structure a backend service
- Build a complete end-to-end application
- Balance usability with technical constraints

---

## Repository Structure

```text
app/
│
├── main.py
│      ↓
│  Starts FastAPI
│  Loads middleware
│  Mounts routes
│
├── routers/
│      ↓
│  translate.py
│      ↓
│  Receives upload request
│  Validates inputs
│  Calls translation service
│
├── services/
│
│  translation.py
│      ↓
│  Main orchestrator
│
│  extract PDF
│      ↓
│  chunk document
│      ↓
│  call AI
│      ↓
│  validate
│      ↓
│  create PDF
│
│  agents.py
│      ↓
│  TranslationAgent
│  ValidationAgent
│
│  chunking.py
│      ↓
│  Splits document into manageable chunks
│
│  pdf_io.py
│      ↓
│  Reads PDF
│  Creates output PDF
│
├── utils/
│      ↓
│  Error handling
│
├── static/
│      ↓
│  Frontend interface
│
└── config.py
       ↓
   Environment variables

docker-compose.yml
requirements.txt
README.md
SETUP_GUIDE.md
```

---

## Conclusion

The AI PDF Translator demonstrates how AI can be combined with modern backend technologies to solve a real-world document processing problem.

It showcases skills in software engineering, API integration, data processing, AI workflows, application architecture, and problem solving while delivering a practical and user-focused solution.
