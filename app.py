import streamlit as st
import pdfplumber
import google.generativeai as genai
import time
from fpdf import FPDF

# 1. Page Configuration (No 'AI' in title)
st.set_page_config(page_title="MIJMR Editorial Board Desk", page_icon="🔖", layout="wide")

st.title("🔖 MIJMR - Editorial Board Evaluation Desk")
st.markdown("Upload the submitted research paper (PDF) for official board evaluation and screening.")

# 2. Fetch API Key from Streamlit Secrets
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("⚠️ Error: Gemini API Key is missing! Please configure it in Streamlit Secrets.")
    st.stop()

# 3. Function to Extract Text from PDF
def extract_text_from_pdf(pdf_file):
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        return text
    except Exception as e:
        return f"Error extracting text: {e}"

# 4. Function to Analyze Text using Gemini 3.5 Flash
def analyze_paper_with_gemini(text, api_key, standard):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-3.5-flash')
    
    if standard == "High Standard (International/Foreign Level)":
        internal_rules = """
        CRITERIA: Evaluate strictly based on top-tier International benchmarks. Be highly rigorous.
        """
        display_title = "MIJMR Editorial Board - International Tier-1 Review Statement"
    else:
        internal_rules = """
        CRITERIA: Evaluate based on local university standard (Arts & Science level). 
        - If the paper is moderately okay (50% to 70% satisfactory), your default decision MUST be APPROVED / PROCEED TO PUBLISH: YES. Do not reject or give heavy revision for average papers.
        - If the paper is extremely poor (below 50% logic/structure), you must provide a strict 'REQUIRED ACTIONABLE CORRECTIONS LIST' point by point, explaining exactly what the author needs to change.
        STRICT RULE: NEVER use any robotic or AI buzzwords. Write exactly like a human Senior Professor or a traditional Editorial Board panel.
        """
        display_title = "MIJMR Editorial Board - Official Review Statement"

    prompt = f"""
    You are a Senior Professor and Chief Screening Editor for MIJMR. 
    Analyze the following research paper text and generate the official board report.
    
    INTERNAL EVALUATION RULES:
    {internal_rules}
    
    Provide the output EXACTLY in the following format. Do NOT include any introductory lines like "Here is the report". Start directly with the title.
    
    **{display_title}**
    
    **1. Core Observations & Evaluation:**
    (Write 1-2 natural paragraphs about the paper's concept and methodology. Keep the tone professional and human-like).
    
    **2. Document & Technical Structure:**
    (Briefly comment on the presence of abstract, keywords, and general grammar in 2-3 sentences).
    
    **3. Quality Rating:** [Provide a score out of 100, e.g., 72/100]
    
    **4. Required Actionable Corrections (Only if paper is very poor or needs changes):**
    (If the paper is poor, list down exactly what parts to change point by point. If the paper is 50-70% ok, just mention 1-2 minor suggestions naturally).
    
    **5. Board's Final Verdict:**
    * **PROCEED TO PUBLISH:** [YES / NO]
    * **BOARD DECISION:** [APPROVED / REVISE SPECIFIC SECTIONS / DECLINED]
    * **Final Remarks:** (A formal 1-2 sentence human-written concluding remark).
    
    Here is the Research Paper Text:
    {text}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"API Error: {e}"

# 5. Function to Create PDF from the Report
def create_pdf(report_text):
    pdf = FPDF()
    pdf.add_page()
    
    # Add Title (No AI mention)
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "MIJMR Editorial Board Evaluation Report", ln=True, align="C")
    pdf.ln(5)
    
    # Clean the text
    clean_text = report_text.replace("**", "").replace("*", "")
    clean_text = clean_text.encode('latin-1', 'replace').decode('latin-1')
    
    # Add Body Text
    pdf.set_font("helvetica", size=11)
    pdf.multi_cell(0, 7, clean_text)
    
    return bytes(pdf.output())

# 6. Streamlit User Interface
st.sidebar.header("🎯 Evaluation Settings")
evaluation_standard = st.sidebar.selectbox(
    "Select Paper Standard Level:",
    ["Normal Standard (Local/Tamil Nadu College Level)", "High Standard (International/Foreign Level)"]
)

uploaded_file = st.file_uploader("📄 Upload Submitted Paper (PDF format only)", type=["pdf"])

if uploaded_file is not None:
    st.success("File uploaded successfully!")
    
    if st.button("🚀 Run Editorial Board Evaluation"):
        with st.spinner("⏳ Reading and processing the document... Please wait..."):
            paper_text = extract_text_from_pdf(uploaded_file)
            
            if "Error extracting text" in paper_text:
                st.error(paper_text)
            elif len(paper_text.strip()) < 50:
                st.warning("⚠️ Text extraction failed or insufficient data. Ensure the PDF is not a scanned image.")
            else:
                st.info("✅ Document verified. Generating board statement...")
                time.sleep(2)
                
                # Step B: Editorial Analysis
                report = analyze_paper_with_gemini(paper_text, api_key, evaluation_standard)
                
                # Show Report on Screen (Directly markdown output without custom AI subheaders)
                st.markdown("---")
                st.markdown(report)
                st.markdown("---")
                st.success("Evaluation Process Completed Successfully.")
                
                # Generate PDF and provide Download Button
                pdf_bytes = create_pdf(report)
                st.download_button(
                    label="📥 Download Official Board Report (PDF)",
                    data=pdf_bytes,
                    file_name="MIJMR_Editorial_Report.pdf",
                    mime="application/pdf"
                )
