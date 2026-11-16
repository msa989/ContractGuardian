# ContractGuardian

Understand before you sign. ContractGuardian is an AI-assisted contract review tool that highlights wording worth a closer look, explains it in plain language, and suggests questions or balanced alternative wording.

> Important: ContractGuardian is an educational information tool, not a law firm or legal-advice service. AI can be wrong, miss context, or misunderstand a clause. It does not determine whether a term is legal or enforceable. Consult a qualified lawyer in the relevant jurisdiction before relying on a contract review.

## Features

- Paste contract text or upload a text-based PDF (8 MB / 60 pages maximum).
- Review up to 12 prioritized clauses.
- See source excerpts, plain-language explanations, practical impact, suggested next steps, alternative wording, and AI confidence.
- Provide a country or jurisdiction as context without treating output as a legal conclusion.
- Responsive browser interface; no account required.
- FastAPI API with request validation, safe error messages, basic per-instance request throttling, and security headers.

## Stack

Frontend: HTML, CSS and vanilla JavaScript. Backend: Python, FastAPI and Pydantic. AI: Google Gemini API via google-genai. PDF extraction: pypdf. Hosting target: Vercel.

## Run locally

Requires Python 3.12 or later.

1. Create and activate a virtual environment.
2. Install dependencies with pip install -r requirements.txt.
3. Copy .env.example to .env and add your own Gemini API key. Load those environment variables into your shell; never expose the key in browser JavaScript or commit it.
4. Run uvicorn index:app --reload.
5. Serve the public folder locally, or install the Vercel CLI and run vercel dev from the project root to test Vercel routing.

## Deploy to Vercel

1. Import this GitHub repository into Vercel and keep the project root at the repository root.
2. Add GEMINI_API_KEY in Project Settings → Environment Variables for Preview and Production.
3. Optionally set GEMINI_MODEL. The default is gemini-3.8-flash.
4. Deploy a Preview first. Test the homepage, /api/health, text analysis, PDF analysis, and invalid-input behavior.
5. Promote to Production only after the Preview passes.

The FastAPI application is exported from the root index.py and app.py entrypoints. Static assets are in public/.

## API

- GET /api/health — health and version check.
- POST /api/analyze — JSON body with contract_text, jurisdiction, and contract_type.
- POST /api/analyze-pdf — multipart form with file, optional jurisdiction, and contract_type.
- GET /api/docs — interactive API documentation.

## Privacy and security

- Contract text is sent to the configured Gemini API for analysis. Redact names, addresses, account numbers, signatures, and other personal data before submitting.
- The app does not intentionally persist submitted contract content. Hosting and AI-provider infrastructure may process request data under their respective terms and retention policies; review those policies before using real agreements.
- The in-memory rate limiter is best-effort per serverless instance, not global abuse prevention. Add a shared rate limiter before high-traffic production use.
- Do not commit API keys. Rotate any key that has been exposed.
- Scanned/image-only PDFs are not OCR-processed in this version.

## Current limitations

This is a contest prototype, not a bulletproof legal product. It has not undergone a professional security audit, independent legal validation, or load testing. It should not be marketed as a replacement for legal counsel.
