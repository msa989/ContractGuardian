import streamlit as st
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
import json
import time

# Page Config
st.set_page_config(page_title="ContractGuardian", page_icon="🛡️", layout="centered")

st.title("🛡️ ContractGuardian")
st.markdown("Analyze contracts or leases to detect hidden traps and red flags before signing.")

# API Key input in the sidebar
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("Enter your Gemini API Key", type="password")

# Pydantic Schema for structured response
class ClauseAnalysis(BaseModel):
    clause_title: str = Field(description="Name or summary of the clause")
    original_text: str = Field(description="Exact quote from the contract")
    risk_level: str = Field(description="MUST be one of: 'HIGH', 'MEDIUM', 'LOW'")
    plain_language_explanation: str = Field(description="5th-grade reading level explanation of what this means for the user")
    recommended_pushback: str = Field(description="Specific wording or request the user can send to negotiate this out")

class ContractAuditResult(BaseModel):
    contract_type: str = Field(description="e.g., Residential Lease, NDA, Freelance Service Agreement")
    overall_risk_score: str = Field(description="Overall rating: 'HIGH RISK', 'MODERATE RISK', or 'SAFE'")
    executive_summary: str = Field(description="2-3 sentence high-level overview of the document")
    flagged_clauses: list[ClauseAnalysis]

# Input Method Selection
input_option = st.radio("Choose Input Method:", ["Upload PDF Document", "Paste Contract Text"])

pdf_bytes = None
contract_text = None

if input_option == "Upload PDF Document":
    uploaded_file = st.file_uploader("Choose a PDF contract or lease", type="pdf")
    if uploaded_file is not None:
        pdf_bytes = uploaded_file.read()
        st.success(f"PDF Loaded: {uploaded_file.name}")
else:
    contract_text = st.text_area("Paste your contract text here:", height=200, placeholder="Paste clauses or full agreement text...")

# Audit Execution Button
if st.button("Run Security Audit", type="primary"):
    if not api_key:
        st.warning("⚠️ Please enter your Gemini API Key in the sidebar to proceed.")
    elif not pdf_bytes and not contract_text:
        st.warning("⚠️ Please either upload a PDF file or paste text before running the audit.")
    else:
        with st.spinner("Analyzing legal terminology and risk clauses..."):
            try:
                response = None
                last_error = None
                
                # Auto-retry loop to handle 503 server spikes smoothly
                for attempt in range(3):
                    try:
                        client = genai.Client(api_key=api_key)
                        
                        if pdf_bytes:
                            contents = [
                                types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                                "You are ContractGuardian, an expert consumer protection attorney. Analyze this contract for high, medium, and low risks."
                            ]
                        else:
                            contents = f"You are ContractGuardian, an expert consumer protection attorney. Analyze this contract text for high, medium, and low risks:\n\n{contract_text}"

                        response = client.models.generate_content(
                            model="gemini-3.8-flash",
                            contents=contents,
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json",
                                response_schema=ContractAuditResult,
                                temperature=0.1
                            )
                        )
                        break
                    except Exception as e:
                        last_error = e
                        if "503" in str(e) and attempt < 2:
                            time.sleep(2)
                            continue
                        else:
                            raise e

                if not response:
                    raise last_error

                result = json.loads(response.text)

                # Display Results
                st.success("Audit Complete!")
                st.subheader(f"Audit Overview: {result['contract_type']}")
                
                risk_color = "red" if "HIGH" in result['overall_risk_score'] else "green"
                st.markdown(f"**Overall Risk:** :{risk_color}[{result['overall_risk_score']}]")
                st.write(result['executive_summary'])
                
                st.divider()
                st.subheader(f"Flagged Clauses ({len(result['flagged_clauses'])})")

                for clause in result['flagged_clauses']:
                    badge_color = "🔴" if clause['risk_level'] == "HIGH" else ("🟡" if clause['risk_level'] == "MEDIUM" else "🟢")
                    
                    with st.expander(f"{badge_color} {clause['clause_title']} ({clause['risk_level']} RISK)"):
                        st.markdown(f"**Exact Text:**")
                        st.info(f"\"{clause['original_text']}\"")
                        st.markdown(f"**What it means:** {clause['plain_language_explanation']}")
                        st.markdown(f"**💡 How to push back:** {clause['recommended_pushback']}")

            except Exception as e:
                st.error(f"An error occurred during analysis: {e}")