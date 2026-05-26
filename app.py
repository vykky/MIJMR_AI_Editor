import streamlit as st
import pdfplumber
import google.generativeai as genai
import time
from fpdf import FPDF

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

# 4. Function to Analyze Text using Gemini 3.5 Flash
# 4. Function to Analyze Text using Gemini 3.5 Flash
def analyze_paper_with_gemini(text, api_key, standard):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-3.5-flash')
    
    if standard == "High Standard (International/Foreign Level)":
        standard_instruction = """
        CRITERIA: Evaluate strictly based on top-tier International/Foreign journal benchmarks. 
        Be highly rigorous. Demand advanced methodology, deep data analysis, original contributions, and flawless logical flow. 
        Do not compromise on quality. If it doesn't match foreign standards, recommend rejection or heavy revisions.
        """
    else:
        # 🟢 Business & Volume Oriented Prompt for Local Papers
        standard_instruction = """
        CRITERIA: Evaluate based on a business-friendly, highly encouraging approach to maximize article acceptance (Local College Standard).
        YOUR GOAL IS TO ACCEPT THE PAPER IF THE BASIC IDEA IS DECENT.
        - Do NOT reject easily. If there are formatting errors or language issues, point them out gently, but lean towards ACCEPTANCE or MINOR REVISION.
        - As long as the core topic is clear and it resembles a research article, it should be approved.
        - Do not demand complex methodologies or high-level data analysis.
        - Make the author feel confident and supported. Keep the tone very positive and welcoming.
        """

    prompt = f"""
    You are the Chief Screening Editor for MIJMR (MIN E KAVI International Journal of Multidisciplinary Research).
    Analyze the following research paper and provide a structured 'Peer Review Report' based on the selected criteria.
    
    {standard_instruction}
    
    Provide the output in the following format:
    
    1. Evaluation Standard Applied
    (State clearly whether this was evaluated under High International Standard or Normal Local Standard).
    
    2. Review of Core Idea & Concept
    (Identify the good aspects of the paper. Focus on the positives. Briefly mention any corrections needed without sounding harsh).
    
    3. Format & Language Check
    (Briefly check if standard sections like Abstract, Keywords, Conclusion are present. If grammar is weak, just suggest a quick proofread, don't penalize heavily).
    
    4. Overall Scoring (Out of 100)
    (For Normal Standard, generally give a score above 70 if the basic structure is present, to keep the author motivated).
    
    5. Final Decision & Actionable Recommendation
    (You MUST state explicitly whether to proceed with publishing or not using the exact format below):
    
    * **PROCEED TO PUBLISH:** [YES] (Default to YES unless it's complete gibberish or heavily plagiarized text).
    * **VERDICT:** [APPROVED / MINOR REVISION NEEDED] (Avoid REJECT unless absolutely necessary).
    
    (Provide a highly encouraging 2-line justification to the Editor-in-Chief, explaining why this paper is good to go for publication).
    
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
    
    # Clean the text
    clean_text = report_text.replace("**", "").replace("*", "")
    clean_text = clean_text.encode('latin-1', 'replace').decode('latin-1')
    
    # Add Body Text
    pdf.set_font("helvetica", size=12)
    pdf.multi_cell(0, 8, clean_text)
    
    return bytes(pdf.output())

# 6. Streamlit User Interface
st.sidebar.header("🎯 Evaluation Settings")
# Dropdown option for the Editor-in-Chief to choose the standard before running analysis
evaluation_standard = st.sidebar.selectbox(
    "Select Paper Standard Level:",
    ["Normal Standard (Local/Tamil Nadu College Level)", "High Standard (International/Foreign Level)"]
)

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
                st.info(f"✅ Text extracted successfully. Evaluating under: {evaluation_standard}...")
                time.sleep(2)
                
                # Step B: AI Analysis with the selected standard
                report = analyze_paper_with_gemini(paper_text, api_key, evaluation_standard)
                
                # Show Report on Screen
                st.subheader("📑 AI Editorial Review Report")
                st.markdown(report)
                st.success("Analysis Complete!")
                
                # Generate PDF and provide Download Button
                pdf_bytes = create_pdf(report)
                st.download_button(
                    label="📥 Download Report as PDF",
                    data=pdf_bytes,
                    file_name="MIJMR_Review_Report.pdf",
                    mime="application/pdf"
                )
