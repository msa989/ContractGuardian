import json
import streamlit as st
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

st.set_page_config(
    page_title="ContractGuardian - AI Legal Audit", page_icon="🛡️", layout="wide"
)

# Custom CSS injection to match modern aesthetic
st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #F8FAFC;
    }
    .top-navbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #FFFFFF;
        padding: 12px 24px;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        margin-bottom: 2rem;
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0F172A;
        text-align: center;
        margin-top: 1rem;
    }
    .hero-subtitle {
        font-size: 1rem;
        color: #64748B;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton>button {
        background-color: #2563EB;
        color: white;
        border-radius: 8px;
        font-weight: 600;
        border: none;
        padding: 0.6rem 1.2rem;
    }
    .stButton>button:hover {
        background-color: #1D4ED8;
        color: white;
    }
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
      description="Clear, non-legalese explanation of what this actually means"
  )
  negotiation_tip: str = Field(description="Actionable advice on how to push back")
  safe_replacement: str = Field(
      description="A fair, balanced alternative clause the user can propose"
  )


# Modern Top Navbar
st.markdown(
    """
    <div class="top-navbar">
        <div style="font-weight: 700; font-size: 1.1rem; color: #0F172A; display: flex; align-items: center; gap: 8px;">
            🛡️ ContractGuardian
        </div>
        <div style="display: flex; gap: 12px; align-items: center;">
            <span style="background: #EFF6FF; color: #1D4ED8; font-size: 0.8rem; font-weight: 600; padding: 4px 10px; border-radius: 20px;">AI Audit v3.8</span>
            <span style="background: #F1F5F9; color: #475569; font-size: 0.8rem; font-weight: 500; padding: 4px 10px; border-radius: 20px; border: 1px solid #CBD5E1;">🟢 Engine Active</span>
        </div>
    </div>
""",
    unsafe_allow_html=True,
)

# Hero Section
st.markdown(
    "<h1 class='hero-title'>Friendly, AI-Powered Contract Guardian</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p class='hero-subtitle'>Upload your legal agreement or lease text. We'll scan for hidden traps, translate complex jargon, and give you safe counter-terms ready to negotiate.</p>",
    unsafe_allow_html=True,
)

# Sidebar Configuration
with st.sidebar:
  st.header("⚙️ Configuration")
  api_key = st.secrets.get("GEMINI_API_KEY", "")
  if not api_key:
    api_key = st.text_input(
        "Enter Gemini API Key", type="password", help="Get a key from Google AI Studio"
    )

  st.divider()
  if st.button("📋 Load Sample Residential Lease"):
    st.session_state["contract_text"] = (
        "8. AUTOMATIC RENEWAL & PENALTIES: Tenant agrees that this Lease"
        " shall automatically renew for successive 12-month terms unless Tenant"
        " provides written notice via certified mail exactly 180 days prior to"
        " lease end. Failure to notify results in a mandatory non-negotiable"
        " liquidated damages fee equal to 4 months of rent.\n\n14. WAIVER OF"
        " LIABILITY & MAINTENANCE: Tenant agrees to hold Landlord harmless for"
        " any property damage, plumbing failures, or structural defects"
        " regardless of fault."
    )
    st.rerun()

# Main Input Interface
tab1, tab2 = st.tabs(["📝 Paste Contract Text", "📄 Upload PDF Document"])

with tab1:
  contract_text = st.text_area(
      "Contract or Lease Clauses",
      value=st.session_state.get("contract_text", ""),
      height=200,
      placeholder="Paste your rental agreement, service contract, or NDA terms here...",
  )

with tab2:
  uploaded_file = st.file_uploader(
      "Upload PDF Lease Agreement", type=["pdf"]
  )

pdf_bytes = uploaded_file.read() if uploaded_file else None

st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
  run_audit = st.button("🚀 Run Security Audit", use_container_width=True)

if run_audit:
  if not api_key:
    st.error(
        "🔑 API Key is missing. Please add a valid Gemini API key to Streamlit"
        " Secrets or the sidebar input."
    )
  elif not pdf_bytes and not contract_text.strip():
    st.warning("⚠️ Please provide contract text or upload a PDF first.")
  else:
    status_box = st.status(
        "Initializing secure audit pipeline...", expanded=True
    )
    try:
      client = genai.Client(api_key=api_key)

      status_box.update(
          label="Analyzing clauses with Gemini-3.8-Flash...", state="running"
      )
      if pdf_bytes:
        contents = [
            types.Part.from_bytes(
                data=pdf_bytes, mime_type="application/pdf"
            ),
            "Analyze this contract/lease for hidden traps, unfair penalties,"
            " liability waivers, and predatory terms.",
        ]
      else:
        contents = (
            f"Analyze this contract text:\n\n{contract_text}\n\nIdentify"
            " hidden traps, unfair penalties, and predatory terms."
        )

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
        status_box.update(
            label="Audit completed successfully!", state="complete", expanded=False
        )
        st.rerun()
      else:
        status_box.update(label="Received empty response.", state="error")
        st.error("Model returned an empty response. Please try again.")
    except Exception as e:
      status_box.update(label="Audit failed.", state="error")
      st.error(f"Error during execution: {str(e)}")

# Display Results & Safe Counter-Terms
if "audit_results" in st.session_state:
  results = st.session_state["audit_results"]

  high_risk = sum(1 for c in results if c.get("risk_level", "").upper() == "HIGH")
  med_risk = sum(1 for c in results if c.get("risk_level", "").upper() == "MEDIUM")
  low_risk = sum(1 for c in results if c.get("risk_level", "").upper() == "LOW")

  st.divider()
  st.markdown("## 📊 Executive Risk Assessment")
  m1, m2, m3 = st.columns(3)
  m1.metric("🔴 High Risk Traps", high_risk)
  m2.metric("🟠 Medium Risk Warnings", med_risk)
  m3.metric("🟢 Low Risk / Fair", low_risk)

  st.markdown("## 🔍 Analyzed Clauses & Safe Counter-Terms")

  high_risk_items = []
  for idx, clause in enumerate(results):
    risk = clause.get("risk_level", "MEDIUM").upper()
    badge = (
        "🔴 HIGH RISK"
        if risk == "HIGH"
        else "🟠 MEDIUM RISK" if risk == "MEDIUM" else "🟢 LOW RISK"
    )

    if risk == "HIGH":
      high_risk_items.append(clause)

    with st.expander(
        f"{badge} — {clause.get('clause_title', f'Clause {idx+1}')}"
    ):
      st.markdown("**Original Clause Text:**")
      st.info(f'"{clause.get("original_text")}"')

      st.markdown(
          f"**What it means for you:**"
          f" {clause.get('plain_language_explanation')}"
      )
      st.markdown(f"💡 **Negotiation Strategy:** {clause.get('negotiation_tip')}")

      st.markdown("**🛡️ Recommended Safe Replacement Clause:**")
      st.success(f'"{clause.get("safe_replacement")}"')

  # Negotiation Email Generator
  st.divider()
  st.markdown("## ✉️ Automated Landlord Pushback Email")
  if st.button("Generate Professional Counter-Offer Email"):
    email_draft = (
        "Dear Property Manager / Landlord,\n\nI have reviewed the proposed"
        " lease agreement and would like to request the following amendments"
        " before signing:\n\n"
    )
    for item in high_risk_items:
      email_draft += (
          f"• Clause: {item.get('clause_title')}\n  Proposed Revision:"
          f' "{item.get("safe_replacement")}"\n\n'
      )
    email_draft += (
        "Please let me know if these adjustments are acceptable so we can move"
        " forward. Thank you!"
    )
    st.text_area(
        "Ready-to-copy email template:", value=email_draft, height=220
    )