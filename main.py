import os
import streamlit as st
import pandas as pd
import pytesseract
from utils import Load_Yaml, generate_sequential_id
from Logics import PdfToText
from logger import logging
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
import textwrap
import time
import re

# Load environment variables
load_dotenv()

# Load Groq API Key
api_key = os.getenv("GROQ_API")

if not api_key:
    st.error("❌ API Key Missing! Add 'GROQ_API' to .env or secrets.toml")
    st.stop()

# Initialize LangChain with Groq API for Llama 3 70B Versatile model
client = ChatGroq(model="deepseek-r1-distill-llama-70b", api_key=api_key)

# Load Configurations
try:
    logging.info("Loading Artifacts ----- Start")
    
    root = "artifacts"
    tesseract_path = os.path.join(os.getcwd(), "Tesseract-OCR", "tesseract.exe")
    poppler_path = os.path.join(os.getcwd(), "poppler-24.08.0", "Library", "bin")
    data_file = os.path.join(root, "ExtractedData.csv")

    os.makedirs(root, exist_ok=True)
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

    if not os.path.exists(data_file):
        df = pd.DataFrame(columns=["ID", "Extracted Text", "Formatted Text"])
    else:
        df = pd.read_csv(data_file)

    logging.info("Loading Artifacts ----- Done")
except Exception as e:
    logging.error(f"Error loading artifacts: {e}")
    df = pd.DataFrame(columns=["ID", "Extracted Text", "Formatted Text"])

# Function to split large text into chunks based on token limit
def split_text_into_chunks(text, max_tokens=6000):
    """Split the large text into smaller chunks that the model can process more efficiently."""
    max_chars = int(max_tokens * 4 / 1.3)  # Estimate characters per token
    return textwrap.wrap(text, max_chars)

# Function to clean the <think> part from the response
def clean_think_part(text):
    """Remove <think> part from the text."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)

# Streamlit UI
st.set_page_config(page_title="PDF OCR Extractor", layout="wide")
st.title("📄 PDF OCR Extractor with Tesseract and Llama 3 70B via Groq")

col1, col2 = st.columns([1, 4])

with col1:
    st.subheader("📊 Extracted Data")
    if not df.empty:
        st.dataframe(df, height=200)
        st.download_button("📥 Download CSV", df.to_csv(index=False), "extracted_text.csv", "text/csv")

with col2:
    uploaded_file = st.file_uploader("📂 Upload a PDF file", type=["pdf"])
    
    if uploaded_file is not None:
        documents_path = os.path.join(os.getcwd(), "documents")
        os.makedirs(documents_path, exist_ok=True)
        
        temp_path = os.path.join(documents_path, uploaded_file.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        ids = df["ID"].tolist()
        doc_id = generate_sequential_id(ids, "DOC_", length=4)

        st.info("🔍 Extracting text from PDF...")

        Obj = PdfToText(tesseract_path=tesseract_path)
        extracted_text = Obj.pdf_to_text(pdf_path=temp_path)

        st.info("📝 Structuring extracted text for readability...")

        # Split the extracted text into smaller chunks
        text_chunks = split_text_into_chunks(extracted_text)

        structured_responses = []
        with st.spinner("Processing..."):
            for chunk in text_chunks:
                # Define a customized prompt to directly request structured text without extra sentences
                format_prompt = PromptTemplate(
                    template="""Structure the following text into a readable, organized format:
                    
                    {extracted_text}
                    
                    Ensure proper formatting without introductory or concluding sentences like "This is a version of your text."
                    Present the key information clearly and concisely.""",
                    input_variables=["extracted_text"],
                )

                formatted_prompt = format_prompt.format(extracted_text=chunk)

                try:
                    # Make the API call to Groq
                    structured_response = client.invoke(formatted_prompt)
                    
                    # Clean the <think> part from the response
                    cleaned_response = clean_think_part(structured_response.content)
                    
                    structured_responses.append(cleaned_response)
                except Exception as e:
                    # Catch any exception (e.g., quota reached, network error, etc.)
                    logging.error(f"Error occurred while invoking Groq API: {e}")
                    st.error("❌ Something went wrong with Groq API. Please try again in some time.")
                    break  # Exit the loop in case of an error

                # Optional: add a short delay to avoid hitting the API rate limit
                time.sleep(2)

        # Combine all structured responses into a single text
        final_structured_text = "\n\n".join(structured_responses)

        # Display formatted text and save data
        if structured_responses:
            st.subheader(f"📑 Formatted Text ({doc_id})")
            st.markdown(final_structured_text)

            # Save structured response to DataFrame
            new_row = {
                "ID": doc_id,
                "Extracted Text": extracted_text,
                "Formatted Text": final_structured_text,
            }
            df.loc[len(df)] = new_row
            df.to_csv(data_file, index=False)

            st.success(f"✅ Text structured and saved with ID: {doc_id}")
