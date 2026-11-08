from google import genai
from google.genai import types
import json
import os
import time
from pydantic import BaseModel, Field
import streamlit as st

# Page Config
st.set_page_config(
    page_title="ContractGuardian", page_icon="🛡️", layout="centered"
)

# Load the API key securely from Streamlit Cloud secrets
api_key = st.secrets["GEMINI_API_KEY"]

st.title("🛡️ ContractGuardian")
st.markdown(
    "Analyze contracts or leases to detect hidden traps and red flags before"
    " signing."
)

# Choose Input Method
input_method = st.radio(
    "Choose Input Method:", ["Upload PDF Document", "Paste Contract Text"]
)

pdf_bytes = None
contract_text = ""

if input_method == "Upload PDF Document":
  uploaded_file = st.file_uploader("Choose a PDF contract or lease", type=["pdf"])
  if uploaded_file is not None:
    pdf_bytes = uploaded_file.read()
    st.success(f"PDF Loaded: {uploaded_file.name}")
else:
  contract_text = st.text_area(
      "Paste your contract text here:",
      height=200,
      placeholder="Paste contract clauses, penalty clauses, or lease terms...",
  )


# Pydantic Schema for structured response
class ClauseAnalysis(BaseModel):
  clause_title: str = Field(description="Name or summary of the clause")
  original_text: str = Field(description="Exact quote from the contract")
  risk_level: str = Field(description="MUST be one of: 'HIGH', 'MEDIUM', 'LOW'")
  plain_language_explanation: str = Field(
      description="5th-grade reading level explanation of the trap"
  )
  negotiation_tip: str = Field(
      description="Actionable advice on how to rewrite or fix this"
  )


# Audit Execution Button
if st.button("Run Security Audit", type="primary"):
  if not pdf_bytes and not contract_text:
    st.warning(
        "⚠️ Please either upload a PDF file or paste text before running the"
        " audit."
    )
  else:
    with st.spinner("Analyzing legal terminology and risk clauses..."):
      try:
        response = None
        last_error = None

        # Auto-retry loop to handle server spikes smoothly
        for attempt in range(3):
          try:
            client = genai.Client(api_key=api_key)

            if pdf_bytes:
              contents = [
                  types.Part.from_bytes(
                      data=pdf_bytes, mime_type="application/pdf"
                  ),
                  (
                      "You are ContractGuardian, an expert consumer protection"
                      " lawyer. Analyze this contract/lease for hidden traps,"
                      " unfair penalties, liability waivers, automatic renewals,"
                      " and predatory terms. Return a structured breakdown of"
                      " every risk found."
                  ),
              ]
            else:
              contents = (
                  "You are ContractGuardian, an expert consumer protection"
                  f" lawyer. Analyze this contract text: \n\n{contract_text}\n\n"
                  "Identify hidden traps, unfair penalties, liability waivers,"
                  " and predatory terms. Return a structured breakdown."
              )

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=list[ClauseAnalysis],
                    temperature=0.2,
                ),
            )
            break
          except Exception as e:
            last_error = e
            time.sleep(2)

        if response is None:
          st.error(f"Analysis failed after retries. Error: {last_error}")
        else:
          st.success("Audit Complete!")
          results = json.loads(response.text)

          for clause in results:
            risk = clause.get("risk_level", "MEDIUM").upper()
            if risk == "HIGH":
              badge_color = "🔴"
            elif risk == "MEDIUM":
              badge_color = "🟠"
            else:
              badge_color = "🟢"

            with st.expander(
                f"{badge_color} {clause.get('clause_title')} (Risk: {risk})"
            ):
              st.markdown("**Exact Text:**")
              st.info(f'"{clause.get("original_text")}"')
              st.markdown(
                  "**What it means:**"
                  f" {clause.get('plain_language_explanation')}"
              )
              st.markdown(
                  f"💡 **How to push back:** {clause.get('negotiation_tip')}"
              )

      except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")