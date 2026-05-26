import streamlit as st
import pdfplumber
import google.generativeai as genai
import time

# 1. Page Configuration
st.set_page_config(page_title="MIJMR AI Editorial Agent", page_icon="🤖", layout="wide")

st.title("🤖 MIJMR - AI Editorial Board Agent")
st.markdown("Upload a Research Paper (PDF) for automated screening and evaluation.")

# 2. Fetch API Key from Streamlit Secrets (Highly Secure)
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("⚠️ Error: Gemini API Key is missing! Please configure it in Streamlit Secrets.")
    st.stop() # Stops the app from running if the key is missing

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
# 4. Function to Analyze Text using Gemini
def analyze_paper_with_gemini(text, api_key):
    genai.configure(api_key=api_key)
    
    # Updated to Gemini 3.5 Flash model
    model = genai.GenerativeModel('gemini-3.5-flash')
    
    prompt = f"""
    You are the highly strict and professional Chief Screening Editor for MIJMR (MIN E KAVI International Journal of Multidisciplinary Research).
    Analyze the following research paper and provide a structured 'Peer Review Report'. 
    IMPORTANT: Focus heavily on the CORE LOGIC, METHODOLOGY, and RESEARCH QUALITY rather than just formatting.
    
    Provide the output in the following format using Markdown:
    
    ### 1. Core Logic & Research Methodology (Crucial)
    (Deeply evaluate the core logic of the paper. Is the research problem clear? Is the methodology scientifically sound? Are the conclusions derived logically from the data? Point out any fundamental flaws in the core concept).
    
    ### 2. Format & Language Verification
    (Briefly check if standard sections like Abstract, Keywords, Conclusion are present, and evaluate the academic tone/grammar).
    
    ### 3. Relevancy & Domain
    (Identify the field of study. Is it suitable for a multidisciplinary journal?).
    
    ### 4. Overall Scoring (Out of 100)
    (Provide a score focusing mainly on research quality, logic, and originality).
    
    ### 5. Final Verdict & Actionable Recommendation
    (You MUST give one of the following exact verdicts based heavily on the core logic, followed by a strict, direct suggestion to the author):
    
    * 🟢 **APPROVED**: (Use this if the core logic, methodology, and formatting are excellent).
    * 🔴 **DECLINED (STRICTLY NO)**: (Use this if the core logic is fundamentally flawed, non-sensical, entirely irrelevant, or lacks basic research value. State clearly why it is rejected).
    * 🟡 **REVISE SPECIFIC SECTION**: (Use this if the overall concept is good, but a specific part—e.g., Data Analysis, Conclusion, or Introduction—is poor. Clearly state EXACTLY WHICH PART needs to be changed and resubmitted).
    
    Here is the Research Paper Text:
    {text}
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"API Error: {e}\n(Please check if the model name is valid and your API limits)."

# 5. Streamlit User Interface
uploaded_file = st.file_uploader("📄 Upload Research Paper (PDF format only)", type=["pdf"])

if uploaded_file is not None:
    st.success("File uploaded successfully!")
    
    if st.button("🚀 Run AI Editorial Analysis"):
        with st.spinner("⏳ AI is reading the paper... Please wait..."):
            # Step A: Extract Text
            paper_text = extract_text_from_pdf(uploaded_file)
            
            if "Error extracting text" in paper_text:
                st.error(paper_text)
            elif len(paper_text.strip()) < 50:
                st.warning("⚠️ Could not extract enough text. This PDF might be an image/scanned document.")
            else:
                st.info("✅ Text extracted successfully. AI is evaluating the content...")
                time.sleep(2) # Small delay for safety
                
                # Step B: AI Analysis
                report = analyze_paper_with_gemini(paper_text, api_key)
                
                st.subheader("📑 AI Editorial Review Report")
                st.markdown(report)
                st.success("Analysis Complete! You can now make the final decision.")
