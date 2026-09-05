"""
Enhanced Streamlit UI with Document-Based Question Generation.

Adds document upload and parsing capabilities to the existing Streamlit app.
"""

import streamlit as st
import os
import sys
import io
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import PyPDF2
except ImportError:
    st.error("PyPDF2 not installed. Install with: pip install PyPDF2 python-docx")

try:
    from docx import Document
except ImportError:
    st.error("python-docx not installed. Install with: pip install python-docx")

import requests
import json
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

API_BASE = os.getenv("API_BASE", "http://0.0.0.0:8000/api/v1")
UPLOAD_FOLDER = "uploaded_documents"

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ============================================================================
# SESSION STATE
# ============================================================================

if "document_content" not in st.session_state:
    st.session_state.document_content = None

if "document_name" not in st.session_state:
    st.session_state.document_name = None

if "document_questions" not in st.session_state:
    st.session_state.document_questions = []

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def parse_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF file."""
    try:
        pdf_file = io.BytesIO(file_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page_num, page in enumerate(pdf_reader.pages):
            try:
                text += page.extract_text() + "\n"
            except Exception as e:
                st.warning(f"⚠️ Error extracting page {page_num + 1}: {str(e)}")
                continue
        
        return text.strip()
    except Exception as e:
        st.error(f"❌ Failed to parse PDF: {str(e)}")
        return None


def parse_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX file."""
    try:
        docx_file = io.BytesIO(file_bytes)
        doc = Document(docx_file)
        
        text = ""
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text += paragraph.text + "\n"
        
        return text.strip()
    except Exception as e:
        st.error(f"❌ Failed to parse DOCX: {str(e)}")
        return None


def parse_text_file(file_bytes: bytes) -> str:
    """Extract text from TXT file."""
    try:
        text = file_bytes.decode('utf-8')
        return text.strip()
    except Exception as e:
        st.error(f"❌ Failed to parse TXT: {str(e)}")
        return None


def generate_questions_from_document(
    doc_text: str,
    prompt: str,
    subject: str,
    question_type: str,
    difficulty: str,
    num_questions: int
) -> dict:
    """Call backend API to generate questions from document."""
    try:
        response = requests.post(
            f"{API_BASE}/documents/generate-questions",
            json={
                "document_text": doc_text,
                "question_prompt": prompt,
                "subject": subject,
                "question_type": question_type,
                "difficulty_level": difficulty,
                "num_questions": num_questions
            },
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"❌ API Error: {response.text}")
            return None
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timeout. Try with fewer questions or simpler prompt.")
        return None
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None


def summarize_document(doc_text: str) -> dict:
    """Call backend API to summarize document."""
    try:
        response = requests.post(
            f"{API_BASE}/documents/summarize",
            json={"document_text": doc_text},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"❌ API Error: {response.text}")
            return None
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None


def extract_concepts(doc_text: str) -> dict:
    """Call backend API to extract concepts from document."""
    try:
        response = requests.post(
            f"{API_BASE}/documents/extract-concepts",
            json={"document_text": doc_text},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"❌ API Error: {response.text}")
            return None
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None


# ============================================================================
# PAGE LAYOUT
# ============================================================================

st.set_page_config(
    page_title="AssessNex - Document Questions",
    page_icon="📄",
    layout="wide"
)

# ============================================================================
# HEADER
# ============================================================================

st.markdown("## 📄 Document-Based Question Generation")
st.markdown("Upload your documents (PDF, DOCX, TXT) and generate AI-powered questions based on the content.")

st.divider()

# ============================================================================
# MAIN INTERFACE
# ============================================================================

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📤 Upload & Generate",
    "📋 Document Analysis",
    "❓ Generated Questions",
    "⚙️ Settings"
])

# ============================================================================
# TAB 1: UPLOAD & GENERATE
# ============================================================================

with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📤 Upload Document")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a document",
            type=["pdf", "docx", "txt"],
            help="Supported formats: PDF, DOCX, TXT (Max 10MB)"
        )
        
        if uploaded_file is not None:
            file_bytes = uploaded_file.read()
            file_name = uploaded_file.name
            file_type = uploaded_file.type
            
            # Parse based on file type
            with st.spinner("📖 Parsing document..."):
                if file_type == "application/pdf":
                    doc_text = parse_pdf(file_bytes)
                elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    doc_text = parse_docx(file_bytes)
                else:
                    doc_text = parse_text_file(file_bytes)
            
            if doc_text:
                st.session_state.document_content = doc_text
                st.session_state.document_name = file_name
                
                # Show document info
                word_count = len(doc_text.split())
                char_count = len(doc_text)
                
                info_col1, info_col2, info_col3 = st.columns(3)
                with info_col1:
                    st.metric("📄 Words", f"{word_count:,}")
                with info_col2:
                    st.metric("🔤 Characters", f"{char_count:,}")
                with info_col3:
                    st.metric("📑 File", file_name.split('/')[-1][:20])
                
                # Show preview
                with st.expander("👁️ Preview (first 500 chars)"):
                    st.text(doc_text[:500] + "...")
    
    with col1:
        st.divider()
        st.subheader("❓ Generate Questions")
        
        if st.session_state.document_content:
            # Question generation form
            gen_col1, gen_col2 = st.columns(2)
            
            with gen_col1:
                subject = st.selectbox(
                    "📚 Subject",
                    ["Machine Learning", "Data Science", "Python", "AI", "General"],
                    key="doc_subject"
                )
                
                difficulty = st.select_slider(
                    "📊 Difficulty",
                    options=["Easy", "Medium", "Hard"],
                    value="Medium"
                )
            
            with gen_col2:
                question_type = st.selectbox(
                    "❓ Question Type",
                    ["Multiple Choice", "Short Answer", "Long Answer", "Essay", "Code"],
                    key="doc_qtype"
                )
                
                num_questions = st.slider(
                    "🔢 Number of Questions",
                    min_value=1,
                    max_value=20,
                    value=5
                )
            
            # Custom prompt
            prompt = st.text_area(
                "💬 What would you like to know?",
                placeholder="E.g., 'Generate questions about supervised learning' or 'Create questions on key concepts'",
                height=100
            )
            
            # Generate button
            if st.button("✨ Generate Questions", use_container_width=True, type="primary"):
                if not prompt.strip():
                    st.error("❌ Please enter a prompt")
                else:
                    with st.spinner("🤖 Generating questions..."):
                        result = generate_questions_from_document(
                            st.session_state.document_content,
                            prompt,
                            subject,
                            question_type,
                            difficulty,
                            num_questions
                        )
                        
                        if result:
                            st.session_state.document_questions = result.get("data", [])
                            st.success(f"✅ Generated {len(st.session_state.document_questions)} questions!")
        else:
            st.info("📤 Upload a document first to generate questions")
    
    with col2:
        st.subheader("📚 Paste Text")
        
        pasted_text = st.text_area(
            "Or paste document content directly",
            height=300,
            placeholder="Paste text here...",
            key="paste_text"
        )
        
        if pasted_text.strip():
            if st.button("✅ Use Pasted Text", use_container_width=True):
                st.session_state.document_content = pasted_text.strip()
                st.session_state.document_name = "Pasted Text"
                st.success("✅ Text loaded!")
                st.rerun()

# ============================================================================
# TAB 2: DOCUMENT ANALYSIS
# ============================================================================

with tab2:
    if st.session_state.document_content:
        st.subheader(f"📖 Analyzing: {st.session_state.document_name}")
        
        analysis_col1, analysis_col2 = st.columns(2)
        
        # Summarize
        with analysis_col1:
            if st.button("📝 Summarize Document", use_container_width=True):
                with st.spinner("⏳ Summarizing..."):
                    summary_result = summarize_document(st.session_state.document_content)
                    
                    if summary_result:
                        st.success("✅ Summary generated!")
                        st.markdown(summary_result.get("summary", "No summary available"))
        
        # Extract concepts
        with analysis_col2:
            if st.button("🧠 Extract Key Concepts", use_container_width=True):
                with st.spinner("⏳ Extracting concepts..."):
                    concepts_result = extract_concepts(st.session_state.document_content)
                    
                    if concepts_result:
                        st.success("✅ Concepts extracted!")
                        concepts = concepts_result.get("concepts", {})
                        
                        if concepts.get("definitions"):
                            st.subheader("📚 Key Definitions")
                            for defn in concepts.get("definitions", [])[:5]:
                                st.write(f"• {defn}")
                        
                        if concepts.get("topics"):
                            st.subheader("📌 Main Topics")
                            for topic in concepts.get("topics", [])[:5]:
                                st.write(f"• {topic}")
                        
                        if concepts.get("entities"):
                            st.subheader("🏷️ Entities")
                            for entity in concepts.get("entities", [])[:5]:
                                st.write(f"• {entity}")
    else:
        st.info("📤 Upload a document first to analyze it")

# ============================================================================
# TAB 3: GENERATED QUESTIONS
# ============================================================================

with tab3:
    if st.session_state.document_questions:
        st.subheader(f"❓ Generated Questions ({len(st.session_state.document_questions)})")
        
        # Export options
        exp_col1, exp_col2, exp_col3 = st.columns(3)
        
        with exp_col1:
            # JSON export
            json_data = json.dumps(st.session_state.document_questions, indent=2)
            st.download_button(
                label="📥 JSON Export",
                data=json_data,
                file_name=f"questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        with exp_col2:
            # Text export
            text_export = "GENERATED QUESTIONS\n" + "=" * 50 + "\n\n"
            for i, q in enumerate(st.session_state.document_questions, 1):
                text_export += f"{i}. {q.get('question_text', q.get('text', 'N/A'))}\n"
                if q.get('options'):
                    for j, opt in enumerate(q.get('options', []), ord('A')):
                        text_export += f"   {chr(j)}) {opt}\n"
                if q.get('answer'):
                    text_export += f"   Answer: {q.get('answer')}\n"
                if q.get('explanation'):
                    text_export += f"   Explanation: {q.get('explanation')}\n"
                text_export += "\n"
            
            st.download_button(
                label="📄 Text Export",
                data=text_export,
                file_name=f"questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with exp_col3:
            if st.button("🗑️ Clear Questions", use_container_width=True):
                st.session_state.document_questions = []
                st.rerun()
        
        st.divider()
        
        # Display questions
        for idx, question in enumerate(st.session_state.document_questions, 1):
            with st.container(border=True):
                # Question header
                q_type = question.get('question_type', 'Question')
                difficulty = question.get('difficulty', 'Medium')
                
                col_q1, col_q2, col_q3 = st.columns([3, 1, 1])
                
                with col_q1:
                    st.markdown(f"**Q{idx}. {question.get('question_text', question.get('text', 'N/A'))}**")
                
                with col_q2:
                    difficulty_color = {
                        "Easy": "🟢",
                        "Medium": "🟡",
                        "Hard": "🔴"
                    }.get(difficulty, "⚪")
                    st.caption(f"{difficulty_color} {difficulty}")
                
                with col_q3:
                    st.caption(f"📝 {q_type}")
                
                # Options
                if question.get('options'):
                    st.markdown("**Options:**")
                    for j, option in enumerate(question.get('options', []), 1):
                        st.write(f"{chr(64 + j)}) {option}")
                
                # Answer
                if question.get('answer'):
                    with st.expander("✅ Show Answer"):
                        st.markdown(f"**Answer:** {question.get('answer')}")
                        
                        if question.get('explanation'):
                            st.markdown(f"**Explanation:** {question.get('explanation')}")
    else:
        st.info("❌ No questions generated yet. Generate questions in the 'Upload & Generate' tab!")

# ============================================================================
# TAB 4: SETTINGS
# ============================================================================

with tab4:
    st.subheader("⚙️ Settings")
    
    # API settings
    st.markdown("### 🌐 API Configuration")
    
    api_base_input = st.text_input(
        "API Base URL",
        value=API_BASE,
        help="Backend API base URL"
    )
    
    if api_base_input != API_BASE:
        os.environ["API_BASE"] = api_base_input
        st.success("✅ API URL updated (refresh page to apply)")
    
    # Document settings
    st.markdown("### 📄 Document Settings")
    
    max_chars = st.number_input(
        "Max characters to send to API",
        value=3000,
        min_value=500,
        max_value=10000,
        help="Larger documents may be truncated to improve performance"
    )
    
    st.info(f"ℹ️ Current API Base: {API_BASE}")
    
    # Display current document
    if st.session_state.document_content:
        st.markdown("### 📋 Current Document")
        st.markdown(f"**File:** {st.session_state.document_name}")
        st.markdown(f"**Words:** {len(st.session_state.document_content.split()):,}")
        st.markdown(f"**Characters:** {len(st.session_state.document_content):,}")
        
        if st.button("🗑️ Clear Current Document"):
            st.session_state.document_content = None
            st.session_state.document_name = None
            st.session_state.document_questions = []
            st.rerun()

# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.8rem;'>
💡 AssessNex AI - Document-Based Question Generation<br>
Powered by Azure OpenAI & LangGraph<br>
<a href='http://0.0.0.0:8000/docs' target='_blank'>📚 API Documentation</a>
</div>
""", unsafe_allow_html=True)
