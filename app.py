import streamlit as st
import pdfplumber
import google.generativeai as genai
import time
from fpdf import FPDF
import re

# 1. Page Configuration
st.set_page_config(page_title="MIJMR AI Editorial Agent", page_icon="🤖", layout="wide")

st.title("🤖 MIJMR - AI Editorial Board Agent")
st.markdown("Upload a Research Paper (PDF) for automated screening and evaluation.")

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

# 4. Function to Analyze Text using Gemini
def analyze_paper_with_gemini(text, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-3.5-flash')
    
    prompt = f"""
    You are the highly strict and professional Chief Screening Editor for MIJMR (MIN E KAVI International Journal of Multidisciplinary Research).
    Analyze the following research paper and provide a structured 'Peer Review Report'. 
    IMPORTANT: Focus heavily on the CORE LOGIC, METHODOLOGY, and RESEARCH QUALITY rather than just formatting.
    
    Provide the output in the following format:
    
    1. Core Logic & Research Methodology (Crucial)
    (Deeply evaluate the core logic of the paper. Is the research problem clear? Is the methodology scientifically sound? Are the conclusions derived logically from the data? Point out any fundamental flaws in the core concept).
    
    2. Format & Language Verification
    (Briefly check if standard sections like Abstract, Keywords, Conclusion are present, and evaluate the academic tone/grammar).
    
    3. Relevancy & Domain
    (Identify the field of study. Is it suitable for a multidisciplinary journal?).
    
    4. Overall Scoring (Out of 100)
    (Provide a score focusing mainly on research quality, logic, and originality).
    
    5. Final Verdict & Actionable Recommendation
    (You MUST give one of the following exact verdicts based heavily on the core logic, followed by a strict, direct suggestion to the author):
    * [APPROVED]
    * [DECLINED - STRICTLY NO]
    * [REVISE SPECIFIC SECTION] - Clearly state EXACTLY WHICH PART needs to be changed.
    
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
    
    # Add Title
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "MIJMR - AI Editorial Review Report", ln=True, align="C")
    pdf.ln(5)
    
    # Clean the text (Remove basic markdown like ** and handle emojis/unsupported chars)
    clean_text = report_text.replace("**", "").replace("*", "")
    clean_text = clean_text.encode('latin-1', 'replace').decode('latin-1')
    
    # Add Body Text
    pdf.set_font("helvetica", size=12)
    pdf.multi_cell(0, 8, clean_text)
    
    # Return PDF as bytes
    return pdf.output()

# 6. Streamlit User Interface
uploaded_file = st.file_uploader("📄 Upload Research Paper (PDF format only)", type=["pdf"])

if uploaded_file is not None:
    st.success("File uploaded successfully!")
    
    if st.button("🚀 Run AI Editorial Analysis"):
        with st.spinner("⏳ AI is reading the paper... Please wait..."):
            paper_text = extract_text_from_pdf(uploaded_file)
            
            if "Error extracting text" in paper_text:
                st.error(paper_text)
            elif len(paper_text.strip()) < 50:
                st.warning("⚠️ Could not extract enough text. This PDF might be an image/scanned document.")
            else:
                st.info("✅ Text extracted successfully. AI is evaluating the content...")
                time.sleep(2)
                
                # Step B: AI Analysis
                report = analyze_paper_with_gemini(paper_text, api_key)
                
                # Show Report on Screen
                st.subheader("📑 AI Editorial Review Report")
                st.markdown(report)
                st.success("Analysis Complete! You can now make the final decision.")
                
                # Generate PDF and provide Download Button
                pdf_bytes = create_pdf(report)
                st.download_button(
                    label="📥 Download Report as PDF",
                    data=pdf_bytes,
                    file_name="MIJMR_Review_Report.pdf",
                    mime="application/pdf"
                )
