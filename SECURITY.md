# Security and responsible use

- Never commit API keys, environment files, contract uploads, or real customer documents.
- Use only a server-side GEMINI_API_KEY environment variable.
- Redact personal and financial information before submitting contract text.
- Uploaded PDFs are parsed in memory for the request; the application does not intentionally save them.
- The API applies input and upload limits and a best-effort per-instance request throttle. That throttle is not a substitute for a shared production rate limiter.
- Do not treat AI-generated risk labels, summaries, or suggested wording as legal advice.
- Report security concerns privately to the repository owner rather than publishing sensitive exploit details in an issue.
