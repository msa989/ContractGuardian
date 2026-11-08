import json
import streamlit as st
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

st.set_page_config(
    page_title="ContractGuardian", page_icon="🛡️", layout="wide"
)

# Custom Styling
st.markdown(
    """
    <style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1E293B; margin-bottom: 0px; }
    .sub-header { font-size: 1rem; color: #64748B; margin-bottom: 25px; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; }
    </style>
""",
    unsafe_allow_html=True,
)


class ClauseAnalysis(BaseModel):
  clause_title: str = Field(description="Short descriptive name of the clause")
  original_text: str = Field(description="Exact text snippet from the contract")
  risk_level: str = Field(
      description="Risk rating: HIGH, MEDIUM, or LOW", enum=["HIGH", "MEDIUM", "LOW"]
  )
  plain_language_explanation: str = Field(
      description="Clear, non-legalese explanation of what this actually means for the user"
  )
  negotiation_tip: str = Field(
      description="Actionable advice on how to push back or negotiate"
  )
  safe_replacement: str = Field(
      description="A fair, balanced alternative clause the user can propose instead"
  )


st.markdown(
    "<h1 class='main-header'>🛡️ ContractGuardian</h1>", unsafe_allow_html=True
)
st.markdown(
    "<p class='sub-header'>AI-Powered Legal Audit & Negotiation Assistant</p>",
    unsafe_allow_html=True,
)

# Sidebar Configuration
with st.sidebar:
  st.header("⚙️ Configuration")
  api_key = st.secrets.get("GEMINI_API_KEY", "")

  if not api_key:
    api_key = st.text_input("Enter Gemini API Key", type="password")

  st.divider()
  st.markdown("### 💡 Demo Utilities")
  if st.button("📋 Load Sample Trap Lease"):
    st.session_state["contract_text"] = """8. AUTOMATIC RENEWAL & PENALTIES: Tenant agrees that this Lease shall automatically renew for successive 12-month terms unless Tenant provides written notice via certified mail exactly 180 days prior to lease end. Failure to notify results in a mandatory non-negotiable liquidated damages fee equal to 4 months of rent.

14. WAIVER OF LIABILITY & MAINTENANCE: Tenant agrees to hold Landlord harmless for any property damage, plumbing failures, or structural defects regardless of fault. Tenant is responsible for all structural repairs under $2,500."""

# Input Tabs
tab1, tab2 = st.tabs(["📝 Text Input", "📄 Upload Document"])

with tab1:
  contract_text = st.text_area(
      "Paste Contract / Lease Agreement Text:",
      value=st.session_state.get("contract_text", ""),
      height=220,
      placeholder="Paste legal text here...",
  )

with tab2:
  uploaded_file = st.file_uploader("Upload PDF Contract", type=["pdf"])

pdf_bytes = uploaded_file.read() if uploaded_file else None

st.divider()

if st.button("🚀 Run Security Audit", type="primary"):
  if not api_key:
    st.error("🔑 API Key is missing. Please add it to Streamlit Secrets.")
  elif not pdf_bytes and not contract_text.strip():
    st.warning(
        "⚠️ Please upload a PDF file or paste text before running the audit."
    )
  else:
    with st.spinner("Analyzing contract for hidden traps and risks..."):
      try:
        client = genai.Client(api_key=api_key)

        if pdf_bytes:
          contents = [
              types.Part.from_bytes(
                  data=pdf_bytes, mime_type="application/pdf"
              ),
              "Analyze this contract/lease for hidden traps, unfair penalties, liability waivers, and predatory terms.",
          ]
        else:
          contents = f"Analyze this contract text:\n\n{contract_text}\n\nIdentify hidden traps, unfair penalties, and predatory terms."

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=list[ClauseAnalysis],
                temperature=0.1,
            ),
        )

        if response and response.text:
          results = json.loads(response.text)
          st.session_state["audit_results"] = results
          st.success("Audit Complete!")
        else:
          st.error("Received an empty response from Gemini.")
      except Exception as e:
        st.error(f"Audit execution failed: {str(e)}")

# Display Results & Negotiation Features
if "audit_results" in st.session_state:
  results = st.session_state["audit_results"]

  # Risk Summary Calculations
  high_risk_count = sum(
      1 for c in results if c.get("risk_level", "").upper() == "HIGH"
  )
  med_risk_count = sum(
      1 for c in results if c.get("risk_level", "").upper() == "MEDIUM"
  )
  low_risk_count = sum(
      1 for c in results if c.get("risk_level", "").upper() == "LOW"
  )

  st.markdown("## 📊 Executive Audit Summary")
  col1, col2, col3 = st.columns(3)
  col1.metric("🔴 High Risk Flags", high_risk_count)
  col2.metric("🟠 Medium Risk Flags", med_risk_count)
  col3.metric("🟢 Low Risk / Standard", low_risk_count)

  st.divider()
  st.markdown("## 🔍 Detailed Clause Breakdown")

  high_risk_clauses = []

  for idx, clause in enumerate(results):
    risk = clause.get("risk_level", "MEDIUM").upper()
    badge = (
        "🔴 HIGH RISK"
        if risk == "HIGH"
        else "🟠 MEDIUM RISK" if risk == "MEDIUM" else "🟢 LOW RISK"
    )

    if risk == "HIGH":
      high_risk_clauses.append(clause)

    with st.expander(
        f"{badge} | {clause.get('clause_title', f'Clause #{idx+1}')}"
    ):
      st.markdown("**Original Text:**")
      st.info(f'"{clause.get("original_text")}"')

      st.markdown(
          f"**What it means:** {clause.get('plain_language_explanation')}"
      )
      st.markdown(f"💡 **Negotiation Tip:** {clause.get('negotiation_tip')}")

      st.markdown("**🛡️ Recommended Safe Replacement:**")
      st.success(f'"{clause.get("safe_replacement")}"')

  # Negotiation Email Generator Section
  st.divider()
  st.markdown("## ✉️ Automated Negotiation Assistant")

  if st.button("Generate Pushback Email for Landlord/Counterparty"):
    email_body = "Dear Property Manager / Landlord,\n\nI have reviewed the proposed agreement and would like to request revisions to the following clauses before signing:\n\n"
    for item in high_risk_clauses:
      email_body += (
          f"• {item.get('clause_title')}:\n  Proposed Revision: "
          f'"{item.get("safe_replacement")}"\n\n'
      )
    email_body += "Please let me know if we can adjust these terms. Thank you!"

    st.text_area(
        "Copy and send this email draft:", value=email_body, height=220
    )