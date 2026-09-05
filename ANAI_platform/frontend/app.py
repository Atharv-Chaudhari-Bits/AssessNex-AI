import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
import json
import re
import io
from config import get_question_types, get_difficulty_levels
from api_client import get_api_client
from utils import setup_logging

logger = setup_logging(__name__)

# Try to import PDF/DOCX parsers
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="AssessNex AI",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if "theme" not in st.session_state:
    st.session_state.theme = "light"

if "api_client" not in st.session_state:
    st.session_state.api_client = get_api_client()

if "generated_questions" not in st.session_state:
    st.session_state.generated_questions = []

if "generated_paper" not in st.session_state:
    st.session_state.generated_paper = []

if "generated_assignment" not in st.session_state:
    st.session_state.generated_assignment = []

if "generation_count" not in st.session_state:
    st.session_state.generation_count = 0

if "generation_request_counter" not in st.session_state:
    st.session_state.generation_request_counter = 0

if "last_generation_time" not in st.session_state:
    st.session_state.last_generation_time = None


# ============================================================================
# THEME CSS FUNCTION
# ============================================================================

def get_theme_css():
    """Get CSS based on current theme."""
    if st.session_state.theme == "dark":
        return """
        <style>
        /* Dark theme */
        :root {
            --primary-color: #0ea5e9;
            --secondary-color: #06b6d4;
            --bg-primary: #1a1a2e;
            --bg-secondary: #16213e;
            --text-primary: #f0f0f0;
        }
        
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        }
        
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f3460 0%, #533483 100%);
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: #0ea5e9;
        }
        
        p { color: #f0f0f0; }
        
        /* Download/Export buttons styling - Dark Theme */
        [data-testid="stDownloadButton"] > button {
            background: linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%) !important;
            color: white !important;
            border: none !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 2px 8px rgba(14, 165, 233, 0.4) !important;
        }
        
        [data-testid="stDownloadButton"] > button:hover {
            background: linear-gradient(135deg, #38bdf8 0%, #22d3ee 100%) !important;
            color: white !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 16px rgba(56, 189, 248, 0.5) !important;
        }
        
        [data-testid="stDownloadButton"] > button:active {
            transform: translateY(0) !important;
            color: white !important;
        }
        
        /* Force white text on download buttons - all states and all child elements */
        [data-testid="stDownloadButton"] button,
        [data-testid="stDownloadButton"] button *,
        [data-testid="stDownloadButton"] > button p,
        [data-testid="stDownloadButton"] > button span,
        [data-testid="stDownloadButton"] > button div,
        [data-testid="stDownloadButton"] button p,
        [data-testid="stDownloadButton"] button span,
        [data-testid="stDownloadButton"] button div,
        [data-testid="stDownloadButton"] button::before,
        [data-testid="stDownloadButton"] button::after {
            color: white !important;
            -webkit-text-fill-color: white !important;
        }
        
        /* Tooltip styling - Dark Theme */
        div[data-baseweb="tooltip"] > div,
        div[data-baseweb="popover"] > div {
            background-color: #334155 !important;
            color: white !important;
        }
        
        div[data-baseweb="tooltip"] p,
        div[data-baseweb="tooltip"] span,
        div[data-baseweb="tooltip"] div,
        div[data-baseweb="popover"] p,
        div[data-baseweb="popover"] span {
            color: white !important;
            -webkit-text-fill-color: white !important;
        }
        
        /* Extended width ONLY for generated questions display */
        .questions-display-section {
            width: 100% !important;
            max-width: 100% !important;
        }
        
        .questions-display-section [data-testid="stContainer"] {
            width: 100% !important;
            max-width: 100% !important;
        }
        
        .questions-display-section [data-testid="stColumn"] {
            width: 100% !important;
        }
        
        /* LaTeX display improvements - Dark Theme */
        .katex-display {
            margin: 0.5rem 0 !important;
            overflow-x: auto;
        }
        
        .katex {
            font-size: 1.1em !important;
            color: #f0f0f0 !important;
        }
        
        /* Code block inside containers - Dark Theme */
        [data-testid="stVerticalBlockBorderWrapper"] .stCodeBlock {
            margin: 0.5rem 0;
        }
        </style>
        """
    else:
        return """
        <style>
        /* Light theme */
        :root {
            --primary-color: #0ea5e9;
            --secondary-color: #06b6d4;
            --bg-primary: #ffffff;
            --bg-secondary: #f5f7fa;
            --text-primary: #1a1a1a;
        }
        
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }
        
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #e8f4f8 0%, #d6e8f0 100%);
            border-right: 2px solid #0ea5e9;
        }
        
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
            color: #0ea5e9;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: #0ea5e9;
        }

        p { color: #1a1a1a; }
        
        /* Sidebar dividers/horizontal rules - Light Theme */
        [data-testid="stSidebar"] hr {
            border: none !important;
            height: 2px !important;
            background: linear-gradient(90deg, transparent, #0ea5e9, transparent) !important;
            margin: 1rem 0 !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] hr,
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] {
            border-color: #0ea5e9 !important;
        }
        
        /* Ensure buttons are visible in light theme sidebar */
        [data-testid="stSidebar"] [data-testid="stButton"] > button {
            background: linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%) !important;
            color: white !important;
            border: none !important;
            font-weight: 600 !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stButton"] > button:hover {
            opacity: 0.9 !important;
        }
        
        /* Download/Export buttons styling - Light Theme */
        [data-testid="stDownloadButton"] > button {
            background: linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%) !important;
            color: white !important;
            border: none !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 2px 8px rgba(14, 165, 233, 0.3) !important;
        }
        
        [data-testid="stDownloadButton"] > button:hover {
            background: linear-gradient(135deg, #0284c7 0%, #0891b2 100%) !important;
            color: white !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(14, 165, 233, 0.4) !important;
        }
        
        [data-testid="stDownloadButton"] > button:active {
            transform: translateY(0) !important;
            color: white !important;
        }
        
        /* Force white text on download buttons - all states and all child elements */
        [data-testid="stDownloadButton"] button,
        [data-testid="stDownloadButton"] button *,
        [data-testid="stDownloadButton"] > button p,
        [data-testid="stDownloadButton"] > button span,
        [data-testid="stDownloadButton"] > button div,
        [data-testid="stDownloadButton"] button p,
        [data-testid="stDownloadButton"] button span,
        [data-testid="stDownloadButton"] button div,
        [data-testid="stDownloadButton"] button::before,
        [data-testid="stDownloadButton"] button::after {
            color: white !important;
            -webkit-text-fill-color: white !important;
        }
        
        /* Tooltip styling - Light Theme */
        div[data-baseweb="tooltip"] > div,
        div[data-baseweb="popover"] > div {
            background-color: #1e293b !important;
            color: white !important;
        }
        
        div[data-baseweb="tooltip"] p,
        div[data-baseweb="tooltip"] span,
        div[data-baseweb="tooltip"] div,
        div[data-baseweb="popover"] p,
        div[data-baseweb="popover"] span {
            color: white !important;
            -webkit-text-fill-color: white !important;
        }
        
        /* Extended width ONLY for generated questions display */
        .questions-display-section {
            width: 100% !important;
            max-width: 100% !important;
        }
        
        .questions-display-section [data-testid="stContainer"] {
            width: 100% !important;
            max-width: 100% !important;
        }
        
        .questions-display-section [data-testid="stColumn"] {
            width: 100% !important;
        }
        
        /* Answer container styling - targets bordered containers after answer headers */
        [data-testid="stVerticalBlockBorderWrapper"] {
            transition: all 0.3s ease;
        }
        
        /* LaTeX display improvements */
        .katex-display {
            margin: 0.5rem 0 !important;
            overflow-x: auto;
        }
        
        .katex {
            font-size: 1.1em !important;
        }
        
        /* Code block inside containers */
        [data-testid="stVerticalBlockBorderWrapper"] .stCodeBlock {
            margin: 0.5rem 0;
        }
        
        /* Mermaid diagram styling */
        .mermaid {
            display: flex;
            justify-content: center;
            margin: 1rem 0;
        }
        
        .mermaid svg {
            max-width: 100%;
            height: auto;
        }
        
        /* Math content styling */
        .math-content {
            line-height: 1.8;
        }
        
        .katex-inline {
            display: inline;
        }
        </style>
        
        <!-- KaTeX CSS and JS for LaTeX rendering -->
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
        <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
        <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
        
        <!-- Mermaid.js CDN for diagram rendering -->
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
        <script>
            // Initialize Mermaid
            mermaid.initialize({
                startOnLoad: false,
                theme: 'default',
                securityLevel: 'loose',
                flowchart: {
                    useMaxWidth: true,
                    htmlLabels: true
                }
            });
            
            // Function to render all mermaid diagrams
            function renderMermaidDiagrams() {
                document.querySelectorAll('.mermaid:not([data-processed])').forEach(function(el) {
                    try {
                        el.setAttribute('data-processed', 'true');
                        mermaid.init(undefined, el);
                    } catch (e) {
                        console.error('Mermaid render error:', e);
                    }
                });
            }
            
            // Function to render KaTeX math
            function renderKaTeXMath() {
                document.querySelectorAll('.katex-inline:not([data-rendered])').forEach(function(el) {
                    if (el.getAttribute('data-latex')) {
                        try {
                            el.setAttribute('data-rendered', 'true');
                            katex.render(el.getAttribute('data-latex'), el, {
                                throwOnError: false,
                                displayMode: false
                            });
                        } catch (e) {
                            el.innerHTML = '$' + el.getAttribute('data-latex') + '$';
                        }
                    }
                });
            }
            
            // Run on page load and observe for changes
            document.addEventListener('DOMContentLoaded', function() {
                setTimeout(function() {
                    renderMermaidDiagrams();
                    renderKaTeXMath();
                }, 500);
            });
            
            // Observe for Streamlit rerenders
            const observer = new MutationObserver(function(mutations) {
                setTimeout(function() {
                    renderMermaidDiagrams();
                    renderKaTeXMath();
                }, 100);
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        </script>
        """


# Apply theme CSS dynamically
st.markdown(get_theme_css(), unsafe_allow_html=True)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def render_content_with_formatting(text: str, q_type: str = ""):
    """
    Render text with code blocks, LaTeX math, and ASCII diagrams properly formatted.
    
    Args:
        text: The text content to render
        q_type: Question type for context-aware rendering
    """
    if not text:
        return
    
    # First, normalize escaped newlines to actual newlines
    text = text.replace('\\n', '\n')
    text = text.replace('\\t', '    ')  # Convert tabs to 4 spaces
    
    # TEXT-ONLY TYPES: Should NOT have code/mermaid - strip them out if present
    text_only_types = ["Multiple Choice", "True/False", "Short Answer", "Long Answer", "Essay", "Fill in the Blank"]
    is_text_only = q_type in text_only_types
    
    # Check if this is a code-related question type
    code_types = ["Code Implementation", "Code Output Prediction", "Coding", "Coding Problem"]
    is_code_question = q_type in code_types
    
    # Check if this is a numerical/math question
    math_types = ["Numerical Problem", "Numerical", "Complexity Analysis", "Algorithm Complexity"]
    is_math_question = q_type in math_types
    
    # Check if this is a diagram question type
    diagram_types = ["Diagram-Based", "Diagram"]
    is_diagram_question = q_type in diagram_types
    
    # SAFETY: For TEXT-ONLY types, strip out any mermaid/code blocks that shouldn't be there
    if is_text_only:
        # Remove mermaid blocks and their content - replace with plain description
        mermaid_pattern = r'```mermaid\s*([\s\S]*?)```'
        if re.search(mermaid_pattern, text, re.IGNORECASE):
            # Extract any meaningful text and replace mermaid with placeholder
            text = re.sub(mermaid_pattern, '[Diagram content - see question context]', text, flags=re.IGNORECASE)
        
        # Remove other code blocks for text-only types (except if question explicitly mentions code)
        code_block_pattern = r'```(\w*)\n?([\s\S]*?)```'
        if not any(kw in text.lower() for kw in ['code', 'function', 'output', 'program']):
            text = re.sub(code_block_pattern, '', text)
        
        # Render as simple markdown text
        st.markdown(text)
        return
    
    # Pattern to find code blocks (```language ... ```)
    code_block_pattern = r'```(\w*)\n?([\s\S]*?)```'
    
    # Check if text has code blocks
    if re.search(code_block_pattern, text):
        # Split text by code blocks and process
        last_end = 0
        for match in re.finditer(code_block_pattern, text):
            # Render text before the code block
            before_text = text[last_end:match.start()]
            if before_text.strip():
                render_text_with_math(before_text)
            
            # Get language and code
            lang = match.group(1).lower() if match.group(1) else "python"
            code = match.group(2)
            
            if code.strip():
                # SPECIAL HANDLING FOR MERMAID - render as diagram using components.html
                if lang == "mermaid":
                    render_mermaid_diagram(code.strip(), "#f0f9ff", "#0EA5E9")
                else:
                    # Regular code - use st.code
                    st.code(code.strip(), language=lang, line_numbers=True)
            
            last_end = match.end()
        
        # Render any remaining text after last code block
        after_text = text[last_end:]
        if after_text.strip():
            render_text_with_math(after_text)
    else:
        # No code blocks - check if it's raw code (for code questions)
        if is_code_question and any([
            'def ' in text,
            'class ' in text,
            'import ' in text,
            'return ' in text,
            'for ' in text and ':' in text,
            'while ' in text and ':' in text,
            'if ' in text and ':' in text,
        ]):
            # Looks like raw code - render as code block
            st.code(text, language="python", line_numbers=True)
        else:
            # Regular text - render with math support
            render_text_with_math(text)


def render_text_with_math(text: str):
    """Render text that may contain LaTeX math expressions."""
    if not text:
        return
    
    # Normalize alternate LaTeX delimiters emitted by models.
    text = text.replace("\\[", "$$").replace("\\]", "$$")
    text = text.replace("\\(", "$").replace("\\)", "$")

    # Fix escaped backslashes in LaTeX.
    text = text.replace('\\\\', '\\')
    
    # Fix corrupted LaTeX commands (e.g., TAB+imes -> \times)
    text = fix_latex_backslashes(text)
    
    # Check for block LaTeX ($$...$$)
    latex_block_pattern = r'\$\$([\s\S]*?)\$\$'
    # Check for inline LaTeX ($...$) - not preceded or followed by $
    inline_latex_pattern = r'(?<!\$)\$(?!\$)([^\$]+?)\$(?!\$)'
    
    # First handle block LaTeX
    if '$$' in text:
        parts = re.split(latex_block_pattern, text)
        
        for i, part in enumerate(parts):
            if i % 2 == 1:
                # This is LaTeX block content
                try:
                    st.latex(part.strip())
                except:
                    st.markdown(f"$${part}$$")
            else:
                # Regular text - may contain inline LaTeX
                if part.strip():
                    render_inline_latex(part)
    elif '$' in text:
        # Only inline LaTeX present
        render_inline_latex(text)
    else:
        # No LaTeX - just render as markdown
        st.markdown(text)


def fix_latex_backslashes(text: str) -> str:
    """
    Fix LaTeX backslashes that may have been corrupted during JSON parsing.
    
    Common issues:
    - \\times becomes TAB + imes (because \\t is interpreted as tab)
    - \\text becomes TAB + ext
    - \\frac becomes frac (backslash lost)
    """
    if not text:
        return text
    
    # CRITICAL FIX: Handle cases where \t was interpreted as TAB character
    # \times -> TAB + imes, \text -> TAB + ext, \theta -> TAB + heta, etc.
    # The TAB character (\t) + suffix needs to be replaced with backslash + t + suffix
    tab_corrupted_fixes = [
        ('imes', r'\times'),      # TAB + imes -> \times
        ('ext{', r'\text{'),      # TAB + ext{ -> \text{
        ('heta', r'\theta'),      # TAB + heta -> \theta
        ('riangle', r'\triangle'), # TAB + riangle -> \triangle
    ]
    
    # Fix tab-corrupted commands - replace TAB+suffix with correct LaTeX
    def fix_tab_corrupted(match):
        content = match.group(0)
        for suffix, correct in tab_corrupted_fixes:
            # Replace TAB character + suffix with correct command
            content = content.replace('\t' + suffix, correct)
            # Also handle already-expanded tabs (4 spaces)
            content = content.replace('    ' + suffix, correct)
        return content
    
    # Apply tab fix to math regions
    text = re.sub(r'\$[^\$]+\$', fix_tab_corrupted, text)
    text = re.sub(r'\$\$[^\$]+\$\$', fix_tab_corrupted, text, flags=re.DOTALL)
    
    # ALSO: Direct replacement for standalone corrupted patterns (outside regex)
    # These catch cases where the content wasn't in a clean $...$ block
    text = text.replace('\times', r'\times')  # This won't work - \t is tab
    
    # Use explicit TAB character replacement
    text = text.replace('\t' + 'imes', r'\times')
    text = text.replace('\t' + 'ext{', r'\text{')
    text = text.replace('\t' + 'heta', r'\theta')
    text = text.replace('\t' + 'an', r'\tan')
    text = text.replace('\t' + 'riangle', r'\triangle')
    
    # Common LaTeX commands that need backslash prefix (for other cases)
    latex_commands = [
        'frac', 'sqrt', 'sum', 'prod', 'int', 'lim', 'log', 'ln', 'sin', 'cos',
        'alpha', 'beta', 'gamma', 'delta', 'epsilon', 'lambda', 'mu', 'sigma', 'pi',
        'infty', 'partial', 'nabla', 'cdot', 'div', 'pm', 'mp', 'leq', 'geq', 'neq',
        'approx', 'equiv', 'subset', 'supset', 'cup', 'cap', 'forall', 'exists',
        'rightarrow', 'leftarrow', 'Rightarrow', 'Leftarrow', 'implies', 'iff',
        'mathbf', 'mathit', 'mathrm', 'mathcal', 'mathbb', 'binom', 'choose',
        'begin', 'end', 'left', 'right', 'big', 'Big', 'bigg', 'Bigg',
        'over', 'atop', 'above', 'displaystyle', 'textstyle', 'times', 'text', 'theta',
    ]
    
    # Fix commands that lost their backslash (only within $ delimiters)
    def fix_in_math(match):
        content = match.group(0)
        for cmd in latex_commands:
            # Pattern: command name not preceded by backslash or letter
            pattern = r'(?<!\\)(?<![a-zA-Z])(' + cmd + r')(?=\{|[^a-zA-Z]|$)'
            content = re.sub(pattern, r'\\' + cmd, content)
        return content
    
    # Process inline math ($...$)
    text = re.sub(r'\$[^\$]+\$', fix_in_math, text)
    
    # Process display math ($$...$$)  
    text = re.sub(r'\$\$[^\$]+\$\$', fix_in_math, text, flags=re.DOTALL)
    
    return text


def render_inline_latex(text: str):
    """Render text with inline LaTeX expressions ($...$) using KaTeX for reliable rendering."""
    if not text:
        return
    
    # Fix escaped backslashes in LaTeX (e.g., \\text -> \text)
    text = text.replace('\\\\', '\\')
    
    # Fix corrupted LaTeX commands (e.g., extdepth -> \text)
    text = fix_latex_backslashes(text)
    
    # Pattern for inline LaTeX ($...$) - not preceded or followed by $
    inline_pattern = r'(?<!\$)\$([^\$\n]+?)\$(?!\$)'
    
    # Check if there's inline LaTeX
    if re.search(inline_pattern, text):
        # Render using components.html for reliable LaTeX rendering
        render_text_with_inline_latex(text)
    else:
        # No LaTeX - just render as markdown
        st.markdown(text)


def render_latex_content(text: str, bg_color: str = "#f0fff4", border_color: str = "#10b981"):
    """
    Render LaTeX content (both inline and block) with proper styling using components.html.
    This handles both $...$ (inline) and $$...$$ (block) LaTeX.
    
    Args:
        text: Text containing LaTeX expressions
        bg_color: Background color for the container
        border_color: Border color for the container
    """
    if not text:
        return
    
    # Fix escaped backslashes in LaTeX (e.g., \\text -> \text)
    text = text.replace('\\\\', '\\')
    
    # Fix corrupted LaTeX commands (e.g., TAB+imes -> \times)
    text = fix_latex_backslashes(text)
    
    # Escape HTML but preserve LaTeX delimiters
    text_escaped = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # Better height calculation - be more generous
    line_count = text.count('\n') + 1
    char_count = len(text)
    has_block_latex = '$$' in text
    
    # More generous height: account for text wrapping and LaTeX rendering
    base_height = 60
    line_height = 30
    latex_extra = 40 if has_block_latex else 20
    wrap_estimate = (char_count // 60) * 25  # Estimate wrapped lines
    
    estimated_height = max(100, base_height + (line_count * line_height) + latex_extra + wrap_estimate)
    # Cap at reasonable max but allow scrolling if needed
    estimated_height = min(500, estimated_height)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
        <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: transparent;
                overflow: visible;
            }}
            .latex-container {{
                background: {bg_color};
                border-left: 4px solid {border_color};
                border-radius: 8px;
                padding: 16px;
                font-size: 16px;
                line-height: 1.8;
                color: #1f2937;
                word-wrap: break-word;
                overflow-wrap: break-word;
            }}
            .katex {{
                font-size: 1.15em;
            }}
            .katex-display {{
                margin: 12px 0;
                overflow-x: auto;
            }}
        </style>
    </head>
    <body>
        <div class="latex-container" id="content">{text_escaped}</div>
        <script>
            renderMathInElement(document.getElementById('content'), {{
                delimiters: [
                    {{left: '$$', right: '$$', display: true}},
                    {{left: '$', right: '$', display: false}}
                ],
                throwOnError: false
            }});
        </script>
    </body>
    </html>
    """
    
    # Enable scrolling to prevent content cutoff
    components.html(html_content, height=estimated_height, scrolling=True)


def render_code_content(text: str, bg_color: str = "#f0fff4", border_color: str = "#10b981"):
    """
    Render code content with syntax highlighting using components.html.
    
    Args:
        text: Text containing code blocks (```language ... ```)
        bg_color: Background color for non-code parts
        border_color: Border color
    """
    if not text:
        return
    
    # Check for code blocks
    code_pattern = r'```(\w*)\n?([\s\S]*?)```'
    
    # Find all code blocks
    matches = list(re.finditer(code_pattern, text))
    
    if not matches:
        # No code blocks - render as styled text
        st.markdown(f"""
        <div style="background: {bg_color}; border-left: 4px solid {border_color}; 
                    border-radius: 8px; padding: 16px; color: #1f2937;">
            {text}
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Process text with code blocks
    last_end = 0
    for match in matches:
        # Render text before this code block
        before_text = text[last_end:match.start()].strip()
        if before_text:
            st.markdown(f"""
            <div style="background: {bg_color}; border-left: 4px solid {border_color}; 
                        border-radius: 8px; padding: 12px; margin-bottom: 8px; color: #1f2937;">
                {before_text}
            </div>
            """, unsafe_allow_html=True)
        
        # Render the code block
        language = match.group(1) or 'text'
        code = match.group(2).strip()
        st.code(code, language=language, line_numbers=True)
        
        last_end = match.end()
    
    # Render any remaining text after the last code block
    after_text = text[last_end:].strip()
    if after_text:
        st.markdown(f"""
        <div style="background: {bg_color}; border-left: 4px solid {border_color}; 
                    border-radius: 8px; padding: 12px; margin-top: 8px; color: #1f2937;">
            {after_text}
        </div>
        """, unsafe_allow_html=True)


def render_text_content(text: str, bg_color: str = "#f0fff4", border_color: str = "#10b981"):
    """
    Render plain text content with styled container.
    
    Args:
        text: Plain text content
        bg_color: Background color
        border_color: Border color
    """
    if not text:
        return
    
    # Clean any accidental formatting
    text = re.sub(r'```mermaid[\s\S]*?```', '', text)
    text = re.sub(r'```\w*\n?[\s\S]*?```', '', text)
    text = text.strip()
    
    st.markdown(f"""
    <div style="background: {bg_color}; border-left: 4px solid {border_color}; 
                border-radius: 8px; padding: 16px; font-size: 16px; 
                line-height: 1.7; color: #1f2937;">
        {text}
    </div>
    """, unsafe_allow_html=True)


def render_diagram_content(text: str, bg_color: str = "#f0fff4", border_color: str = "#10b981"):
    """
    Render diagram-based content (mermaid) with proper styling.
    For answers/explanations, extract the meaningful text or render the diagram.
    
    Args:
        text: Text potentially containing mermaid diagram code
        bg_color: Background color
        border_color: Border color
    """
    if not text:
        return
    
    # Check for mermaid code blocks
    mermaid_pattern = r'```mermaid\s*([\s\S]*?)```'
    mermaid_match = re.search(mermaid_pattern, text)
    
    if mermaid_match:
        mermaid_code = mermaid_match.group(1).strip()
        
        # For answers - try to extract the answer text from mermaid
        # Look for patterns like "Note over A: answer text" or "A->>B: answer text"
        answer_patterns = [
            r'Note over [^:]+:\s*(.+?)(?:\n|$)',
            r'[A-Z]-+>>?[A-Z]:\s*(.+?)(?:\n|$)',
            r'[A-Z]\s*-->\s*[A-Z]:\s*(.+?)(?:\n|$)',
        ]
        
        extracted_text = None
        for pattern in answer_patterns:
            match = re.search(pattern, mermaid_code)
            if match:
                extracted_text = match.group(1).strip()
                break
        
        # Get any text outside the mermaid block
        text_before = text[:mermaid_match.start()].strip()
        text_after = text[mermaid_match.end():].strip()
        non_mermaid_text = f"{text_before} {text_after}".strip()
        
        # If we have extracted text or non-mermaid text, show that
        if extracted_text or non_mermaid_text:
            display_text = extracted_text or non_mermaid_text
            st.markdown(f"""
            <div style="background: {bg_color}; border-left: 4px solid {border_color}; 
                        border-radius: 8px; padding: 16px; font-size: 16px; 
                        line-height: 1.7; color: #1f2937;">
                {display_text}
            </div>
            """, unsafe_allow_html=True)
        else:
            # No text extracted - render the diagram itself
            render_mermaid_diagram(mermaid_code, bg_color, border_color)
    else:
        # No mermaid - render as plain text
        st.markdown(f"""
        <div style="background: {bg_color}; border-left: 4px solid {border_color}; 
                    border-radius: 8px; padding: 16px; font-size: 16px; 
                    line-height: 1.7; color: #1f2937;">
            {text}
        </div>
        """, unsafe_allow_html=True)


def render_text_with_inline_latex(text: str):
    """
    Render text with inline LaTeX expressions using components.html for reliable KaTeX rendering.
    
    Args:
        text: Text containing inline LaTeX ($...$)
    """
    # Fix corrupted LaTeX first
    text = fix_latex_backslashes(text)
    
    # Escape HTML but preserve LaTeX
    text_escaped = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # Better height calculation
    line_count = text.count('\n') + 1
    char_count = len(text)
    wrap_estimate = (char_count // 50) * 25  # Estimate wrapped lines
    estimated_height = max(80, min(400, line_count * 35 + wrap_estimate))
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
        <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
        <style>
            body {{
                margin: 0;
                padding: 8px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 16px;
                line-height: 1.7;
                color: #1f2937;
                background: transparent;
                overflow: visible;
            }}
            .math-content {{
                word-wrap: break-word;
                overflow-wrap: break-word;
            }}
            .katex {{
                font-size: 1.1em;
            }}
        </style>
    </head>
    <body>
        <div class="math-content" id="content">{text_escaped}</div>
        <script>
            renderMathInElement(document.getElementById('content'), {{
                delimiters: [
                    {{left: '$$', right: '$$', display: true}},
                    {{left: '$', right: '$', display: false}}
                ],
                throwOnError: false
            }});
        </script>
    </body>
    </html>
    """
    
    # Enable scrolling to prevent content cutoff
    components.html(html_content, height=estimated_height, scrolling=True)


def render_mermaid_content(text: str, style_type: str = "answer"):
    """
    Render Mermaid diagram content with proper styling using components.html for reliable JS execution.
    
    Args:
        text: Content that may contain Mermaid diagrams
        style_type: "answer" or "explanation" for styling context
    """
    import hashlib
    
    # Colors based on style
    if style_type == "answer":
        bg_color = "#ecfdf5"
        border_color = "#10b981"
    else:
        bg_color = "#fffbeb"
        border_color = "#f59e0b"
    
    # Extract Mermaid code from markdown blocks
    mermaid_pattern = r'```mermaid\s*([\s\S]*?)```'
    matches = list(re.finditer(mermaid_pattern, text, re.IGNORECASE))
    
    if matches:
        last_end = 0
        for match in matches:
            # Text before Mermaid block
            before = text[last_end:match.start()].strip()
            if before:
                st.markdown(before)
            
            # Render Mermaid diagram using components.html for reliable JS
            mermaid_code = match.group(1).strip()
            if mermaid_code:
                render_mermaid_diagram(mermaid_code, bg_color, border_color)
            
            last_end = match.end()
        
        # Text after last Mermaid block
        after = text[last_end:].strip()
        if after:
            st.markdown(after)
    else:
        # Check for raw Mermaid content (without code blocks)
        mermaid_keywords = ['graph ', 'flowchart ', 'sequenceDiagram', 'classDiagram', 'stateDiagram', 'erDiagram', 'gantt', 'pie']
        is_raw_mermaid = any(text.strip().startswith(kw) for kw in mermaid_keywords)
        
        if is_raw_mermaid:
            render_mermaid_diagram(text, bg_color, border_color)
        else:
            # Not Mermaid - render as regular text
            st.markdown(text)


def render_mermaid_diagram(mermaid_code: str, bg_color: str = "#f0f9ff", border_color: str = "#0EA5E9"):
    """
    Render a single Mermaid diagram using components.html for reliable JavaScript execution.
    
    Args:
        mermaid_code: Raw mermaid diagram code
        bg_color: Background color for the container
        border_color: Border color for the container
    """
    import hashlib
    
    # Clean up the mermaid code
    mermaid_code = mermaid_code.strip()
    
    # Generate unique ID
    diagram_id = f"mermaid_{hashlib.md5(mermaid_code.encode()).hexdigest()[:12]}"
    
    # Escape the mermaid code for JavaScript string
    mermaid_code_escaped = mermaid_code.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')
    
    # Calculate height based on content
    line_count = len(mermaid_code.split('\n'))
    estimated_height = max(300, min(600, line_count * 35 + 100))
    
    # Create standalone HTML with mermaid rendering
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: transparent;
            }}
            .diagram-container {{
                background: linear-gradient(135deg, {bg_color} 0%, {bg_color}ee 100%);
                border-left: 4px solid {border_color};
                padding: 1.5rem;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
            .mermaid {{
                display: flex;
                justify-content: center;
                align-items: center;
            }}
            .mermaid svg {{
                max-width: 100%;
                height: auto;
            }}
            .error-message {{
                color: #dc2626;
                padding: 1rem;
                background: #fef2f2;
                border-radius: 8px;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="diagram-container">
            <div class="mermaid" id="{diagram_id}">
{mermaid_code}
            </div>
        </div>
        <script>
            mermaid.initialize({{
                startOnLoad: true,
                theme: 'default',
                securityLevel: 'loose',
                flowchart: {{
                    useMaxWidth: true,
                    htmlLabels: true,
                    curve: 'basis'
                }},
                sequence: {{
                    useMaxWidth: true,
                    diagramMarginX: 50,
                    diagramMarginY: 10,
                    actorMargin: 50,
                    width: 150,
                    height: 65
                }}
            }});
        </script>
    </body>
    </html>
    """
    
    # Render using components.html which properly executes JavaScript
    components.html(html_content, height=estimated_height, scrolling=True)


def extract_code_for_download(text: str) -> str:
    """
    Extract clean code from text for download purposes.
    Removes markdown code blocks and returns pure code.
    
    Args:
        text: Text that may contain code blocks
        
    Returns:
        Clean code string suitable for saving to a file
    """
    # First normalize escaped sequences
    text = text.replace('\\n', '\n').replace('\\t', '    ')
    
    # Check for code blocks
    code_pattern = r'```(\w*)\n?([\s\S]*?)```'
    matches = list(re.finditer(code_pattern, text))
    
    if matches:
        # Extract all code blocks
        code_parts = []
        for match in matches:
            code = match.group(2).strip()
            if code:
                code_parts.append(code)
        return '\n\n'.join(code_parts)
    else:
        # No code blocks - return cleaned text
        return text.strip()


def render_styled_content(text: str, q_type: str, style_type: str = "answer", content_flags: dict = None):
    """
    Render content with consistent styling based on question type.
    Both answer and explanation use the same rendering logic per type.
    
    Args:
        text: Content to render
        q_type: Question type for context
        style_type: "answer" (green) or "explanation" (yellow) - used for styling
        content_flags: Optional dict with has_code, has_latex, has_diagram flags from LLM
    """
    
    # Define colors based on style type
    if style_type == "answer":
        bg_color = "#ecfdf5"
        border_color = "#10b981"
        text_color = "#065f46"
    else:  # explanation
        bg_color = "#fffbeb"  
        border_color = "#f59e0b"
        text_color = "#78350f"
    
    # Define TECHNICAL types that need special rendering
    code_types = ["Code Implementation", "Code Output Prediction", "Coding", "Coding Problem"]
    math_types = ["Numerical Problem", "Numerical", "Complexity Analysis", "Algorithm Complexity"]
    diagram_types = ["Diagram-Based", "Diagram"]
    
    # Normalize text and fix LaTeX
    text = text.replace('\\n', '\n').replace('\\t', '    ')
    text = fix_latex_backslashes(text)  # Fix corrupted LaTeX
    
    # Check question type
    is_code_type = q_type in code_types
    is_diagram_type = q_type in diagram_types
    is_math_type = q_type in math_types
    
    # Use content_flags from LLM if available, otherwise detect
    if content_flags:
        has_code = content_flags.get('has_code', False)
        has_latex = content_flags.get('has_latex', False)
        has_mermaid = content_flags.get('has_diagram', False)
    else:
        # Fallback to content detection
        has_mermaid = '```mermaid' in text.lower() or any(kw in text for kw in ['graph ', 'flowchart ', 'sequenceDiagram', 'classDiagram', 'stateDiagram'])
        has_latex = '$' in text
        has_code = '```' in text and not has_mermaid
    
    # =========================================================================
    # TYPE-SPECIFIC RENDERING WITH PROPER STYLED CONTAINERS
    # =========================================================================
    
    # For CODE TYPES: Use render_code_content with styled container
    if is_code_type or has_code:
        render_code_content(text, bg_color, border_color)
        return
    
    # For DIAGRAM TYPES: Use diagram rendering
    if is_diagram_type or has_mermaid:
        render_diagram_content(text, bg_color, border_color)
        return
    
    # For MATH TYPES: Use LaTeX rendering with styled container
    if is_math_type or has_latex:
        render_latex_content(text, bg_color, border_color)
        return
    
    # =========================================================================
    # NON-TECHNICAL TYPES: ALWAYS use styled HTML div (consistent for answer & explanation)
    # =========================================================================
    
    # Simple text types (Multiple Choice, True/False, Essay, Short Answer, etc.)
    # Always render with colored background - same style for both answer and explanation
    safe_text = text.replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {bg_color} 0%, {bg_color}dd 100%);
        border-left: 4px solid {border_color};
        padding: 1rem;
        border-radius: 8px;
        color: {text_color};
        font-weight: 500;
        line-height: 1.6;
    ">{safe_text}</div>
    """, unsafe_allow_html=True)


# ============================================================================
# DOCUMENT PARSING HELPER FUNCTIONS
# ============================================================================

def parse_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF file."""
    if not PDF_AVAILABLE:
        raise Exception("PyPDF2 not installed. Run: pip install PyPDF2")
    
    try:
        pdf_file = io.BytesIO(file_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page_num, page in enumerate(pdf_reader.pages):
            try:
                text += page.extract_text() + "\n"
            except Exception as e:
                logger.warning(f"Error extracting page {page_num + 1}: {str(e)}")
                continue
        
        return text.strip()
    except Exception as e:
        raise Exception(f"Failed to parse PDF: {str(e)}")


def parse_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX file."""
    if not DOCX_AVAILABLE:
        raise Exception("python-docx not installed. Run: pip install python-docx")
    
    try:
        docx_file = io.BytesIO(file_bytes)
        doc = Document(docx_file)
        
        text = ""
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text += paragraph.text + "\n"
        
        return text.strip()
    except Exception as e:
        raise Exception(f"Failed to parse DOCX: {str(e)}")


def parse_text_file(file_bytes: bytes) -> str:
    """Extract text from TXT file."""
    try:
        text = file_bytes.decode('utf-8')
        return text.strip()
    except Exception as e:
        raise Exception(f"Failed to parse TXT: {str(e)}")


def extract_document_text(uploaded_file) -> str:
    """Extract text from uploaded file based on file type."""
    try:
        file_bytes = uploaded_file.read()
        
        if uploaded_file.type == "application/pdf":
            return parse_pdf(file_bytes)
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return parse_docx(file_bytes)
        elif uploaded_file.type == "text/plain":
            return parse_text_file(file_bytes)
        else:
            raise Exception(f"Unsupported file type: {uploaded_file.type}")
    except Exception as e:
        raise Exception(f"Error processing document: {str(e)}")


def display_question(question: dict, index: int):
    """Display a single question with all details, including code and math formatting."""
    with st.container(border=True):
        # Get metadata
        diff = question.get('difficulty_level', 'N/A')
        subject = question.get('subject', 'N/A')
        q_type = question.get('question_type', 'N/A')
        
        # Difficulty badge color
        if diff == 'Easy':
            diff_color = "#10b981"
            diff_bg = "#ecfdf5"
            diff_icon = "🟢"
        elif diff == 'Medium':
            diff_color = "#f59e0b"
            diff_bg = "#fffbeb"
            diff_icon = "🟡"
        else:
            diff_color = "#ef4444"
            diff_bg = "#fef2f2"
            diff_icon = "🔴"
        
        # Question type icon mapping
        type_icons = {
            "Code Implementation": "💻",
            "Code Output Prediction": "🖥️",
            "Coding": "💻",
            "Coding Problem": "💻",
            "Numerical Problem": "🔢",
            "Numerical": "🔢",
            "Diagram-Based": "📊",
            "Diagram": "📊",
            "Multiple Choice": "📝",
            "True/False": "✅",
            "Essay": "📄",
            "Scenario-Based": "🎯",
        }
        q_type_icon = type_icons.get(q_type, "📝")
        
        # Question header with inline metadata badges
        st.markdown(f"""
        <div style="margin-bottom: 1rem;">
            <div style="display: flex; align-items: center; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.75rem;">
                <span style="background: linear-gradient(135deg, #0EA5E9 0%, #06B6D4 100%); 
                            color: white; padding: 0.25rem 0.75rem; border-radius: 20px; 
                            font-weight: 600; font-size: 0.9rem;">Q{index + 1}</span>
                <span style="background: {diff_bg}; color: {diff_color}; padding: 0.25rem 0.75rem; 
                            border-radius: 20px; font-weight: 500; font-size: 0.85rem;">{diff_icon} {diff}</span>
                <span style="background: #e0f2fe; color: #0369a1; padding: 0.25rem 0.75rem; 
                            border-radius: 20px; font-weight: 500; font-size: 0.85rem;">📚 {subject}</span>
                <span style="background: #f3e8ff; color: #7c3aed; padding: 0.25rem 0.75rem; 
                            border-radius: 20px; font-weight: 500; font-size: 0.85rem;">{q_type_icon} {q_type}</span>
            </div>
            <h4 style="color: #0EA5E9; margin-bottom: 0.5rem; margin-top: 0;">📖 Question</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Render question text with formatting support
        question_text = question.get('question_text', 'N/A')
        render_content_with_formatting(question_text, q_type)

        visual = question.get("visual")
        if isinstance(visual, dict) and visual.get("image_base64"):
            try:
                import base64 as _base64
                image_bytes = _base64.b64decode(visual["image_base64"])
                st.image(image_bytes, caption=visual.get("title", "Generated visual"), use_container_width=True)
            except Exception as exc:
                logger.warning("Could not render generated visual: %s", exc)
                st.warning("The visual could not be displayed, but the question text is still available.")
        st.write("")
        
        # Options with improved styling
        options = question.get('options', [])
        if options and isinstance(options, list) and len(options) > 0:
            st.markdown("""
            <div style="margin-bottom: 0.5rem;">
                <h4 style="color: #06B6D4; margin: 0;">🎯 Options</h4>
            </div>
            """, unsafe_allow_html=True)
            
            options_html = """<div style='
                background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
                border-left: 4px solid #0EA5E9;
                padding: 1.2rem;
                border-radius: 8px;
                line-height: 1.8;
            '>"""
            
            for i, option in enumerate(options):
                # Convert to string if it's not already
                if not isinstance(option, str):
                    option = str(option) if option is not None else ""
                
                # Safely check if option is a string and starts with letter
                option_display = option
                if len(option) > 0:
                    try:
                        if option[0].isalpha() and len(option) > 1 and option[1] in ').:':
                            option_display = option
                        else:
                            option_display = f"{chr(65+i)}) {option}"
                    except (IndexError, TypeError):
                        option_display = f"{chr(65+i)}) {option}"
                else:
                    option_display = f"{chr(65+i)}) {option}"
                
                # Alternate colors for better readability
                bg_color = "#ffffff" if i % 2 == 0 else "#f9fafb"
                options_html += f"""<div style='
                    background: {bg_color};
                    padding: 0.75rem;
                    margin: 0.5rem 0;
                    border-radius: 6px;
                    color: #1f2937;
                '><b style="color: #0EA5E9;">{option_display}</b></div>"""
            
            options_html += "</div>"
            st.markdown(options_html, unsafe_allow_html=True)
            st.write("")
        
        # Answer and Explanation with better layout
        col1, col2 = st.columns([1, 1], gap="large")
        
        # Define types that need special formatting
        expected_answer = question.get('expected_answer', 'N/A')
        code_types = ["Code Implementation", "Code Output Prediction", "Coding", "Coding Problem"]
        is_code_type = q_type in code_types
        
        # Get content flags from LLM if available
        content_flags = question.get('content_flags', None)
        
        with col1:
            st.markdown("""
            <h4 style="color: #10b981; margin-bottom: 0.5rem; margin-top: 0;">✅ Expected Answer</h4>
            """, unsafe_allow_html=True)
            
            # Normalize answer - convert escaped sequences
            answer_text = str(expected_answer) if expected_answer else 'N/A'
            answer_text = answer_text.replace('\\n', '\n').replace('\\t', '    ')
            
            # Render answer with styled wrapper
            render_styled_content(answer_text, q_type, style_type="answer", content_flags=content_flags)
            
            # Add download button for code types
            if is_code_type and answer_text and answer_text != 'N/A':
                code_content = extract_code_for_download(answer_text)
                if code_content:
                    st.download_button(
                        label="📥 Download Code",
                        data=code_content,
                        file_name=f"question_{index + 1}_solution.py",
                        mime="text/x-python",
                        key=f"download_code_{index}_{st.session_state.get('generation_count', 0)}"
                    )
        
        with col2:
            explanation = question.get('explanation')
            if explanation:
                st.markdown("""
                <h4 style="color: #f59e0b; margin-bottom: 0.5rem; margin-top: 0;">💡 Explanation</h4>
                """, unsafe_allow_html=True)
                
                # Normalize explanation - convert escaped sequences
                exp_text = str(explanation).replace('\\n', '\n').replace('\\t', '    ')
                
                # Render explanation with styled wrapper
                render_styled_content(exp_text, q_type, style_type="explanation", content_flags=content_flags)
        
        st.write("")


def display_header(title: str, description: str):
    """Display responsive header."""
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #0EA5E9 0%, #06B6D4 100%); 
                padding: 1.5rem 1rem; border-radius: 15px; margin-bottom: 2rem; box-shadow: 0 8px 24px rgba(14, 165, 233, 0.2);">
        <h1 style="color: white; margin: 0; font-size: 2em;">{title}</h1>
        <p style="color: rgba(255,255,255,0.95); margin: 0.5rem 0 0 0; font-size: 0.95rem; font-weight: 500;">
            {description}
        </p>
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.markdown("##  Settings")
    st.divider()
    
    # Theme selector
    st.markdown("###  Theme")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(" Light", use_container_width=True, key="light_btn"):
            st.session_state.theme = "light"
            st.rerun()
    
    with col2:
        if st.button(" Dark", use_container_width=True, key="dark_btn"):
            st.session_state.theme = "dark"
            st.rerun()
    
    current = " Dark" if st.session_state.theme == "dark" else " Light"
    st.info(f"Current: {current}")
    
    st.divider()
    
    # Clear cache button
    if st.button("[*] Clear Cache", use_container_width=True, type="secondary"):
        st.session_state.generated_questions = []
        st.session_state.generated_paper = []
        st.session_state.generated_assignment = []
        st.session_state.generation_count = 0
        st.session_state.generation_request_counter = 0
        st.session_state.last_generation_time = None
        st.rerun()
    
    st.divider()
    
    # Stats
    st.markdown("###  Statistics")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Generated", st.session_state.generation_count)
    
    with col2:
        st.metric("Loaded", len(st.session_state.generated_questions))
    
    if st.session_state.last_generation_time:
        st.caption(f"Last: {st.session_state.last_generation_time}")


# ============================================================================
# MAIN HEADER
# ============================================================================

st.markdown("""
<div style="background: linear-gradient(135deg, #0EA5E9 0%, #06B6D4 100%); 
            padding: 3rem; border-radius: 15px; margin-bottom: 2.5rem; box-shadow: 0 8px 24px rgba(14, 165, 233, 0.2);">
    <h1 style="color: white; margin: 0; font-size: 3em;"> AssessNex AI</h1>
    <p style="color: rgba(255,255,255,0.95); margin: 0.5rem 0 0 0; font-size: 1.2rem; font-weight: 500;">
        Professional MTech-Level Question Generator with AI
    </p>
    <p style="color: rgba(255,255,255,0.85); margin: 0.5rem 0 0 0; font-size: 0.95rem;">
        Generate 12+ types of AI and Technical Questions  Advanced Difficulty Levels  Complete Papers & Assignments
    </p>
</div>
""", unsafe_allow_html=True)


# ============================================================================
# TAB INTERFACE
# ============================================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([" Generate Questions", " Question Paper", " Assignment", " Customised Q&A", " 🧾 Evaluate Paper"])


# ============================================================================
# TAB 1: GENERATE QUESTIONS
# ============================================================================

with tab1:
    display_header(" Generate Questions", "Create individual questions with AI")
    
    # Input layout with better spacing (doubled widths)
    col1, col2, col3, col4 = st.columns([2.4, 2.4, 2.4, 2], gap="large")
    
    with col1:
        subject = st.selectbox(
            " Subject",
            ["Machine Learning", "Deep Learning", "Natural Language Processing", "Computer Vision",
             "Artificial Intelligence", "Reinforcement Learning", "Data Science", "Cryptography"],
            key="q_subject"
        )
    
    with col2:
        difficulty = st.selectbox(" Difficulty", get_difficulty_levels(), key="q_difficulty")
    
    with col3:
        q_type = st.selectbox(" Question Type", get_question_types(), key="q_type")
    
    with col4:
        num = st.slider(" Count", 1, 25, 5, key="q_count")
    
    # Context input - full width
    context = st.text_area(
        " Additional Context (Optional)",
        placeholder="e.g., Focus on loss functions in neural networks...",
        height=80,
        key="q_context"
    )
    
    st.divider()
    
    # Generate Button
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
    
    # Use a flag to track if generation should happen
    generate_clicked = False
    with col_btn2:
        if st.button(" Generate Questions", type="primary", use_container_width=True):
            generate_clicked = True
    
    # Handle generation OUTSIDE the column context for full-width display
    if generate_clicked:
        # Increment counter to ensure fresh generation
        st.session_state.generation_request_counter += 1
        # Clear old questions immediately
        st.session_state.generated_questions = []
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.info(" Generating questions...")
            progress_bar.progress(30)
            
            client = st.session_state.api_client
            progress_bar.progress(60)
            
            response = client.generate_questions(subject, q_type, difficulty, num, context or None)
            
            # Log the response for debugging
            logger.debug(f"Raw response from API: {response}")
            logger.info(f"Response type: {type(response)}, Keys: {response.keys() if isinstance(response, dict) else 'N/A'}")
            
            # Parse response - validate structure
            questions = response.get('data') or response.get('questions', [])
            
            # Ensure questions is a list and validate each item
            if not isinstance(questions, list):
                questions = [questions] if questions else []
            
            logger.info(f"Questions before validation: {len(questions)} questions")
            logger.debug(f"First question sample: {questions[0] if questions else 'None'}")
            
            # Filter out invalid questions and log any issues
            valid_questions = []
            for idx, q in enumerate(questions):
                logger.debug(f"Question {idx}: Type={type(q)}, Keys={q.keys() if isinstance(q, dict) else 'N/A'}")
                if isinstance(q, dict) and q.get('question_text'):
                    # Validate question structure before adding
                    if not isinstance(q.get('options'), (list, type(None))):
                        logger.warning(f"Invalid options type for question {idx}: {type(q.get('options'))} = {q.get('options')}")
                        q['options'] = None  # Fix invalid options
                    valid_questions.append(q)
                else:
                    logger.warning(f"Skipping invalid question {idx}: {q}")
            
            questions = valid_questions
            logger.info(f"Valid questions after filtering: {len(questions)}")
            
            if questions and len(questions) > 0:
                progress_bar.progress(100)
                status_text.success(f" Successfully generated {len(questions)} questions!")
                
                st.session_state.generated_questions = questions
                st.session_state.generation_count += len(questions)
                st.session_state.last_generation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                st.balloons()
                
                # Show questions immediately - NOW OUTSIDE COLUMN CONTEXT
                st.divider()
                st.markdown(f"""
                <div class="questions-display-section">
                    <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                                padding: 1.5rem; border-radius: 10px; margin: 1rem 0; width: 100%; box-sizing: border-box;">
                        <h2 style="color: white; margin: 0; width: 100%;"> Generated Questions ({len(questions)})</h2>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Display questions with full width
                st.markdown('<div class="questions-display-section">', unsafe_allow_html=True)
                for idx, question in enumerate(questions):
                    try:
                        logger.debug(f"Displaying question {idx}: {json.dumps(question, indent=2, default=str)}")
                        with st.container():
                            display_question(question, idx)
                    except Exception as e:
                        logger.error(f"Error displaying question {idx}: {str(e)}", exc_info=True)
                        st.error(f"Error displaying question {idx + 1}: {str(e)}")
                        continue
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Export section - full width
                st.divider()
                st.markdown("###  Export Options")
                
                # Export format description
                st.markdown("""
                <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); 
                            padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid #0EA5E9;">
                    <p style="margin: 0; color: #0369a1; font-size: 0.9rem;">
                        📥 <strong>Download your questions</strong> in multiple formats for different use cases
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                col_export1, col_export2, col_export3, col_export4 = st.columns(4)
                
                with col_export1:
                    json_str = json.dumps(questions, indent=2)
                    st.download_button(
                        label="📄 JSON",
                        data=json_str,
                        file_name=f"questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        use_container_width=True,
                        help="Download as JSON - Best for programmatic use"
                    )
                
                with col_export2:
                    csv_str = "Question,Type,Difficulty,Answer,Subject,Options,Explanation\n"
                    for q in questions:
                        options_str = " | ".join(q.get('options', [])) if q.get('options') else ""
                        csv_str += f'"{q.get("question_text", "")}","{q.get("question_type", "")}","{q.get("difficulty_level", "")}","{q.get("expected_answer", "")}","{q.get("subject", "")}","{options_str}","{q.get("explanation", "")}"\n'
                    st.download_button(
                        label="📊 CSV",
                        data=csv_str,
                        file_name=f"questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        help="Download as CSV - Best for Excel/Sheets"
                    )
                
                with col_export3:
                    # Generate formatted text/markdown
                    md_str = f"# Generated Questions\n\n"
                    md_str += f"**Subject:** {subject} | **Difficulty:** {difficulty} | **Type:** {q_type}\n"
                    md_str += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | **Total:** {len(questions)} questions\n\n"
                    md_str += "---\n\n"
                    
                    for idx, q in enumerate(questions, 1):
                        md_str += f"## Question {idx}\n\n"
                        md_str += f"**Difficulty:** {q.get('difficulty_level', 'N/A')} | **Type:** {q.get('question_type', 'N/A')}\n\n"
                        md_str += f"{q.get('question_text', '')}\n\n"
                        
                        if q.get('options'):
                            md_str += "**Options:**\n"
                            for i, opt in enumerate(q.get('options', [])):
                                md_str += f"- {chr(65+i)}) {opt}\n"
                            md_str += "\n"
                        
                        md_str += f"**Answer:** {q.get('expected_answer', 'N/A')}\n\n"
                        
                        if q.get('explanation'):
                            md_str += f"**Explanation:** {q.get('explanation', '')}\n\n"
                        
                        md_str += "---\n\n"
                    
                    st.download_button(
                        label="📝 Markdown",
                        data=md_str,
                        file_name=f"questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                        mime="text/markdown",
                        use_container_width=True,
                        help="Download as Markdown - Best for documentation"
                    )
                
                with col_export4:
                    # Generate plain text format for printing
                    txt_str = "=" * 60 + "\n"
                    txt_str += "           GENERATED QUESTIONS\n"
                    txt_str += "=" * 60 + "\n\n"
                    txt_str += f"Subject: {subject}\n"
                    txt_str += f"Difficulty: {difficulty}\n"
                    txt_str += f"Type: {q_type}\n"
                    txt_str += f"Total Questions: {len(questions)}\n"
                    txt_str += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    txt_str += "-" * 60 + "\n\n"
                    
                    for idx, q in enumerate(questions, 1):
                        txt_str += f"Q{idx}. {q.get('question_text', '')}\n\n"
                        
                        if q.get('options'):
                            for i, opt in enumerate(q.get('options', [])):
                                txt_str += f"    {chr(65+i)}) {opt}\n"
                            txt_str += "\n"
                        
                        txt_str += f"Answer: {q.get('expected_answer', 'N/A')}\n"
                        
                        if q.get('explanation'):
                            txt_str += f"Explanation: {q.get('explanation', '')}\n"
                        
                        txt_str += "\n" + "-" * 60 + "\n\n"
                    
                    st.download_button(
                        label="📃 Text",
                        data=txt_str,
                        file_name=f"questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        use_container_width=True,
                        help="Download as Text - Best for printing"
                    )
                
                # Additional export options row
                st.write("")
                col_extra1, col_extra2, col_extra3, col_extra4 = st.columns(4)
                
                with col_extra1:
                    # Answer key only
                    answer_key = "ANSWER KEY\n" + "=" * 40 + "\n\n"
                    for idx, q in enumerate(questions, 1):
                        answer_key += f"Q{idx}: {q.get('expected_answer', 'N/A')}\n"
                    
                    st.download_button(
                        label="🔑 Answer Key",
                        data=answer_key,
                        file_name=f"answer_key_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        use_container_width=True,
                        help="Download answer key only"
                    )
                
                with col_extra2:
                    # Questions only (no answers) - for student handout
                    student_str = f"QUESTION PAPER\n"
                    student_str += f"Subject: {subject} | Total: {len(questions)} Questions\n"
                    student_str += "=" * 50 + "\n\n"
                    
                    for idx, q in enumerate(questions, 1):
                        student_str += f"Q{idx}. {q.get('question_text', '')}\n\n"
                        
                        if q.get('options'):
                            for i, opt in enumerate(q.get('options', [])):
                                student_str += f"    {chr(65+i)}) {opt}\n"
                            student_str += "\n"
                        
                        student_str += "\n"
                    
                    st.download_button(
                        label="📋 Student Copy",
                        data=student_str,
                        file_name=f"student_questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        use_container_width=True,
                        help="Questions only - No answers (for students)"
                    )
                
                with col_extra3:
                    # Copy to clipboard functionality using a text area
                    clipboard_text = "\n\n".join([f"Q{i+1}: {q.get('question_text', '')}" for i, q in enumerate(questions)])
                    st.download_button(
                        label="📑 Quick List",
                        data=clipboard_text,
                        file_name=f"quick_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        use_container_width=True,
                        help="Simple question list for quick reference"
                    )
                
                with col_extra4:
                    # Statistics summary
                    stats_str = "GENERATION STATISTICS\n"
                    stats_str += "=" * 40 + "\n\n"
                    stats_str += f"Total Questions: {len(questions)}\n"
                    stats_str += f"Subject: {subject}\n"
                    stats_str += f"Difficulty: {difficulty}\n"
                    stats_str += f"Type: {q_type}\n"
                    stats_str += f"Generated At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    
                    # Count by difficulty
                    diff_counts = {}
                    for q in questions:
                        d = q.get('difficulty_level', 'Unknown')
                        diff_counts[d] = diff_counts.get(d, 0) + 1
                    
                    stats_str += "Difficulty Distribution:\n"
                    for d, count in diff_counts.items():
                        stats_str += f"  - {d}: {count}\n"
                    
                    st.download_button(
                        label="📈 Stats",
                        data=stats_str,
                        file_name=f"stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        use_container_width=True,
                        help="Download generation statistics"
                    )
            else:
                progress_bar.progress(0)
                status_text.error(f" No questions generated\n\nResponse: {response}")
        
        except Exception as e:
            st.error(f"""
             **Error generating questions:**
            
            {str(e)}
            
            **Troubleshooting:**
            -  Ensure backend is running at http://0.0.0.0:8000
            -  Check backend logs for errors
            -  Try with fewer questions (1-5)
            -  Ensure context is concise
            """)


# ============================================================================
# TAB 2: QUESTION PAPER GENERATOR
# ============================================================================

with tab2:
    display_header("📄 Generate Question Paper", "Create complete papers with custom distribution")

    st.markdown("### 📋 Paper Configuration")

    col1, col2 = st.columns(2)
    with col1:
        paper_name = st.text_input("📝 Paper Name", value="Midterm Examination", key="paper_name")
        paper_code = st.text_input("🔢 Course Code", value="CS-501", key="paper_code")
    with col2:
        paper_semester = st.selectbox("📅 Semester", list(range(1, 9)), key="paper_semester")
        paper_subject = st.selectbox(
            "📚 Subject",
            [
                "Machine Learning", "Deep Learning", "Natural Language Processing",
                "Computer Vision", "Artificial Intelligence",
                "Reinforcement Learning", "Data Science", "Cryptography"
            ],
            key="paper_subject"
        )

    col1, col2, col3 = st.columns(3)
    with col1:
        total_questions = st.slider("❓ Total Questions", 5, 50, 15, key="paper_total")
    with col2:
        total_marks = st.slider("📊 Total Marks", 10, 200, 100, key="paper_marks")
    with col3:
        paper_duration = st.slider("⏱️ Duration (min)", 30, 240, 90, step=15, key="paper_duration")

    st.divider()

    # ---------------- Difficulty Distribution ----------------
    st.markdown("#### 🎯 Difficulty Distribution")

    col1, col2, col3 = st.columns(3)
    with col1:
        easy_count = st.number_input("🟢 Easy", 0, total_questions, total_questions // 3)
    with col2:
        medium_count = st.number_input("🟡 Medium", 0, total_questions, total_questions // 3)
    with col3:
        hard_count = st.number_input(
            "🔴 Hard", 0, total_questions, total_questions - 2 * (total_questions // 3)
        )

    diff_total = easy_count + medium_count + hard_count
    if diff_total != total_questions:
        st.warning(f"⚠️ Difficulty total: {diff_total} (Need {total_questions})")
    else:
        st.success("✅ Difficulty distribution valid")

    difficulty_distribution = {
        "Easy": easy_count,
        "Medium": medium_count,
        "Hard": hard_count
    }

    st.divider()

    # ---------------- Question Type Distribution ----------------
    st.markdown("#### 📝 Question Type Distribution")

    col1, col2 = st.columns(2)

    with col1:
        mcq = st.number_input("✅ Multiple Choice", 0, total_questions, min(5, total_questions))
        short_ans = st.number_input("📝 Short Answer", 0, total_questions, 3)
        long_ans = st.number_input("📄 Long Answer", 0, total_questions, 2)
        tf = st.number_input("❓ True/False", 0, total_questions, 2)

    with col2:
        fill = st.number_input("✏️ Fill in Blank", 0, total_questions, 0)
        numerical = st.number_input("🔢 Numerical", 0, total_questions, 2)
        code = st.number_input("💻 Code Implementation", 0, total_questions, 1)
        diagram = st.number_input("📊 Diagram Based", 0, total_questions, 0)

    type_total = mcq + short_ans + long_ans + tf + fill + numerical + code + diagram
    if type_total != total_questions:
        st.warning(f"⚠️ Question type total: {type_total} (Need {total_questions})")
    else:
        st.success("✅ Question type distribution valid")

    # Per-section configuration: the values selected here are sent verbatim to the backend.
    marks_each = max(1, total_marks // max(total_questions, 1))
    st.markdown("#### ⚙️ Section Configuration")
    active_types = [
        ("Multiple Choice", mcq), ("Short Answer", short_ans), ("Long Answer", long_ans),
        ("True/False", tf), ("Fill in the Blank", fill), ("Numerical Problem", numerical),
        ("Code Implementation", code), ("Diagram-Based", diagram),
    ]
    section_settings = {}
    for idx, (type_name, count) in enumerate(active_types):
        if count <= 0:
            continue
        c1, c2 = st.columns(2)
        with c1:
            section_settings[type_name] = {
                "difficulty": st.selectbox(
                    f"{type_name} difficulty", ["mixed", "easy", "medium", "hard"],
                    index=0,
                    key=f"difficulty_{idx}",
                )
            }
        with c2:
            section_settings[type_name]["marks_each"] = st.number_input(
                f"{type_name} marks each", min_value=1, max_value=max(1, total_marks),
                value=max(1, marks_each), key=f"marks_each_{idx}"
            )

    question_type_config = []
    for type_name, count in active_types:
        if count > 0:
            cfg = section_settings[type_name]
            question_type_config.append({
                "type": type_name,
                "count": int(count),
                "marks_each": int(cfg["marks_each"]),
                "difficulty": cfg["difficulty"],
                "bloom_levels": [],
            })

    configured_marks = sum(c["count"] * c["marks_each"] for c in question_type_config)
    if configured_marks != total_marks:
        st.warning(f"⚠️ Section marks total {configured_marks}, but paper total is {total_marks}. Adjust marks per question or Total Marks before generating.")
    else:
        st.success(f"✅ Section configuration matches {total_marks} total marks")

    st.divider()
    st.markdown("#### 🧠 Bloom's Taxonomy Distribution")
    bloom_defaults = {"Remember": 10, "Understand": 25, "Apply": 30, "Analyze": 20, "Evaluate": 10, "Create": 5}
    bloom_distribution = {}
    bloom_cols = st.columns(3)
    for i, level in enumerate(bloom_defaults):
        with bloom_cols[i % 3]:
            bloom_distribution[level] = st.number_input(
                level, min_value=0, max_value=100, value=bloom_defaults[level], step=5, key=f"bloom_{level}"
            )
    bloom_total = sum(bloom_distribution.values())
    if bloom_total != 100:
        st.warning(f"⚠️ Bloom distribution totals {bloom_total}%. It must total 100%.")
    else:
        st.success("✅ Bloom distribution totals 100%")

    # ---------------- Document-Based Generation ----------------
    st.markdown("### 📄 Document-Based Generation (Optional)")

    use_document = st.checkbox("📤 Use document content to generate paper", value=False)
    document_text = None

    if use_document:
        uploaded_file = st.file_uploader(
            "📁 Upload document (PDF, DOCX, TXT)",
            type=["pdf", "docx", "txt"]
        )

        if uploaded_file:
            document_text = extract_document_text(uploaded_file)
            st.success(f"✅ Extracted {len(document_text)} characters")

    st.divider()

    paper_topic = st.text_area(
        "📋 Paper Topic / Context (Optional)",
        height=80,
        placeholder="Topics, concepts, or focus areas..."
    )

    paper_instructions = st.text_area(
        "📜 Instructions",
        height=80,
        value="Answer all questions. Show all working where applicable."
    )

    bloom_distribution = {
        "Remember": 10,
        "Understand": 25,
        "Apply": 30,
        "Analyze": 20,
        "Evaluate": 10,
        "Create": 5
    }

    st.divider()

    # ---------------- Generate Button ----------------
    if st.button("🚀 Generate Paper", type="primary", use_container_width=True):
        if diff_total != total_questions or type_total != total_questions or configured_marks != total_marks or bloom_total != 100:
            st.error("❌ Fix distributions before generating paper")
        else:
            try:
                client = st.session_state.api_client

                payload = {
                    "exam_name": paper_name,
                    "subject": paper_subject,
                    "topic": paper_topic or paper_name,
                    "total_marks": int(total_marks),
                    "duration_minutes": int(paper_duration),
                    "question_type_config": question_type_config,
                    "difficulty_distribution": difficulty_distribution,
                    "bloom_distribution": bloom_distribution,
                    "instructions": paper_instructions,
                    "enable_validation": True,
                    "enable_metrics": True,
                    "enable_explainability": True,
                }

                progress_bar = st.progress(0)
                status_box = st.empty()
                status_box.info("⏳ Starting paper generation…")

                def update_paper_progress(message, progress):
                    progress_bar.progress(max(0, min(100, int(progress))))
                    status_box.info(f"🧠 {message}")

                response = client.generate_paper_with_payload(
                    payload,
                    progress_callback=update_paper_progress,
                )

                paper_data = response.get("paper", response)
                st.session_state.generated_paper = paper_data
                progress_bar.progress(100)
                status_box.success("✅ Question paper, answer key and quality checks are ready.")
                st.balloons()

            except Exception as e:
                st.error("❌ Backend validation failed")
                import traceback
                st.code(traceback.format_exc())
    # ---------------- Display Generated Paper ----------------
    if "generated_paper" in st.session_state and st.session_state.generated_paper:
        
        st.divider()
        
        # Add custom CSS for better styling
        st.markdown("""
        <style>
        /* Force all text to be black */
        .stMarkdown, .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown li, .stMarkdown ul, .stMarkdown ol {
            color: black !important;
        }
        
        /* Specific styling for paper elements */
        .paper-header-container {
            background-color: #e8f4fd;
            padding: 25px;
            border-radius: 10px;
            border-left: 5px solid #1e88e5;
            margin-bottom: 25px;
        }
        
        .paper-title {
            color: #0d47a1 !important;
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 15px;
            text-align: center;
        }
        
        .paper-info {
            color: #1565c0 !important;
            font-size: 18px;
            margin: 10px 0;
        }
        
        .section-title {
            color: #1a237e !important;
            font-size: 24px;
            font-weight: 600;
            margin-top: 30px;
            padding-bottom: 10px;
            border-bottom: 2px solid #1a237e;
        }
        
        .question-text {
            color: #000000 !important;
            font-size: 18px;
            font-weight: 500;
            margin: 20px 0 15px 0;
            line-height: 1.5;
        }
        
        .options-container {
            margin-left: 25px;
            margin-bottom: 15px;
        }
        
        .option-text {
            color: #424242 !important;
            font-size: 16px;
            margin: 8px 0;
            padding-left: 10px;
        }
        
        .marks-badge {
            color: #d32f2f !important;
            font-weight: 600;
            font-size: 16px;
            background-color: #ffebee;
            padding: 4px 12px;
            border-radius: 15px;
            display: inline-block;
            margin-top: 10px;
        }
        
        .question-divider {
            border-top: 1px dashed #b0bec5;
            margin: 25px 0;
        }
        
        
        
        /* Export button styling */
        .export-button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("## 📄 Generated Question Paper")
        
        # ==================== DATA TRANSFORMATION FUNCTION ====================
        def transform_backend_data(response):
            """
            Transform backend response to frontend-compatible format.
            Handles field name mismatches, missing data, and formatting issues.
            """
            if not response:
                return {"error": "No response data"}
            
            # Extract paper from response
            if isinstance(response, dict) and "paper" in response:
                paper = response["paper"]
                # Keep the full response for metadata
                full_response = response
            else:
                paper = response
                full_response = {}
            
            # Ensure paper has sections
            if "sections" not in paper:
                paper["sections"] = []
            
            # Transform each section and question
            transformed_sections = []
            total_questions = 0
            
            for section_idx, section in enumerate(paper.get("sections", [])):
                # Ensure section has required fields
                section_title = section.get("title", f"Section {chr(65 + section_idx)}")
                question_type = section.get("question_type", "Multiple Choice")
                
                transformed_section = {
                    "title": section_title,
                    "question_type": question_type,
                    "instructions": section.get("instructions", ""),
                    "questions": []
                }
                
                # Transform questions in this section
                questions = section.get("questions", [])
                for q_idx, question in enumerate(questions):
                    total_questions += 1
                    
                    # ===== FIX 1: Handle question text =====
                    # Try multiple possible field names for question text
                    question_text = None
                    possible_question_fields = ["question", "question_text", "prompt", "text", "query"]
                    
                    for field in possible_question_fields:
                        if field in question and question[field]:
                            question_text = str(question[field]).strip()
                            break
                    
                    # If still no question text, create one
                    if not question_text or question_text.lower() == "none":
                        # Generate descriptive question text
                        topic = paper.get("topic", paper.get("subject", "the topic"))
                        difficulty = question.get("difficulty", "medium")
                        question_type_local = question.get("type", question_type)
                        
                        question_text = f"{question_type_local} question on {topic}"
                        
                        # Add difficulty context
                        if difficulty:
                            question_text += f" ({difficulty} difficulty)"
                        
                        # Mark as auto-generated
                        question["_auto_generated"] = True
                    
                    # ===== FIX 2: Handle options =====
                    options = []
                    if "options" in question and question["options"]:
                        raw_options = question["options"]
                        if isinstance(raw_options, list):
                            # Clean each option
                            for opt_idx, opt in enumerate(raw_options):
                                if opt and str(opt).strip().lower() != "none":
                                    opt_text = str(opt).strip()
                                    
                                    # Ensure option has letter prefix
                                    option_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
                                    if opt_idx < len(option_letters):
                                        # Check if already has letter
                                        if len(opt_text) > 2 and opt_text[1] == ')':
                                            options.append(opt_text)
                                        else:
                                            options.append(f"{option_letters[opt_idx]}) {opt_text}")
                                    else:
                                        options.append(f"{opt_idx + 1}) {opt_text}")
                    
                    # ===== FIX 3: Handle answer =====
                    answer = None
                    possible_answer_fields = ["answer", "expected_answer", "correct_answer", "solution"]
                    
                    for field in possible_answer_fields:
                        if field in question and question[field]:
                            answer = str(question[field]).strip()
                            break
                    
                    # ===== FIX 4: Create transformed question =====
                    transformed_question = {
                        "id": question.get("id", f"q_{total_questions}"),
                        "question_number": total_questions,
                        "question": question_text,
                        "type": question.get("type", question.get("question_type", question_type)),
                        "options": options,
                        "answer": answer,
                        "marks": question.get("marks", section.get("marks_per_question", 2)),
                        "difficulty": question.get("difficulty", question.get("difficulty_level", "medium")),
                        "bloom_level": question.get("bloom_level", "Apply"),
                        "explanation": question.get("explanation", ""),
                        "topic": question.get("topic", paper.get("topic", "")),
                        "visual": question.get("visual"),
                        "_original_data": {k: v for k, v in question.items() if k not in ["question", "options", "answer"]}
                    }
                    
                    transformed_section["questions"].append(transformed_question)
                
                transformed_sections.append(transformed_section)
            
            # ===== FIX 5: Ensure paper has required top-level fields =====
            final_paper = {
                "exam_name": paper.get("exam_name", paper.get("header", {}).get("exam_name", "Question Paper")),
                "subject": paper.get("subject", paper_subject),
                "topic": paper.get("topic", ""),
                "total_marks": paper.get("total_marks", total_marks),
                "duration_minutes": paper.get("duration_minutes", paper_duration),
                "instructions": paper.get("instructions", paper.get("header", {}).get("instructions", [])),
                "answer_key": paper.get("answer_key", paper.get("header", {}).get("answer_key", [])),
                "quality_results": paper.get("quality_results", {}),
                "sections": transformed_sections,
                "_metadata": {
                    "total_questions": total_questions,
                    "total_sections": len(transformed_sections),
                    "transformation_applied": True,
                    "original_response_keys": list(response.keys()) if isinstance(response, dict) else []
                },
                "_full_response": full_response  # Keep original for debug
            }
            
            return final_paper
        
        # ==================== APPLY TRANSFORMATION ====================
        try:
            # Transform backend data
            transformed_paper = transform_backend_data(st.session_state.generated_paper)
            
            # Debug info in sidebar
            st.sidebar.markdown("### 🔍 Data Status")
            
            # Show transformation stats
            st.sidebar.info(f"""
            📊 Paper Statistics:
            - Sections: {len(transformed_paper['sections'])}
            - Total Questions: {transformed_paper['_metadata']['total_questions']}
            - Transformation Applied: ✅
            """)
            
            # Debug expander
            with st.sidebar.expander("📋 Debug Details"):
                st.json(transformed_paper["_metadata"])
                
                # Show sample of transformed questions
                st.markdown("**Sample Questions:**")
                for i, section in enumerate(transformed_paper["sections"][:2]):
                    for j, q in enumerate(section["questions"][:1]):
                        st.text(f"Q{q['question_number']}: {q['question'][:80]}...")
                        if q.get("_auto_generated"):
                            st.warning("⚠️ Auto-generated question text")
            
            # Get the transformed paper
            paper = transformed_paper
            
        except Exception as e:
            st.error(f"Error transforming paper data: {str(e)}")
            # Fallback to original
            response = st.session_state.generated_paper
            if isinstance(response, dict) and "paper" in response:
                paper = response["paper"]
            else:
                paper = response
            st.warning("Using untransformed data (may have display issues)")
        
        # ==================== DISPLAY PAPER ====================
        
        # Header section
        st.markdown(f"""
        <div class="paper-header-container">
            <div class="paper-title">📝 {paper.get('exam_name', 'Question Paper')}</div>
            <div class="paper-info">
                <strong>📚 Subject:</strong> {paper.get('subject', paper_subject)}<br>
                <strong>⏱️ Duration:</strong> {paper.get('duration_minutes', paper_duration)} minutes<br>
                <strong>📊 Total Marks:</strong> {paper.get('total_marks', total_marks)}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Export button at the top
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("📥 Export Paper", use_container_width=True, type="primary"):
                st.session_state.export_paper = paper
                st.rerun()
        
        # Instructions
        instructions = paper.get("instructions", [])
        if instructions and isinstance(instructions, list) and len(instructions) > 0:
            # Filter out empty instructions
            valid_instructions = [inst for inst in instructions if inst and str(inst).strip()]
            if valid_instructions:
                st.markdown("### 📜 Instructions")
                for i, inst in enumerate(valid_instructions, 1):
                    st.markdown(f"<p style='color: black !important; font-size: 16px;'>{i}. {inst}</p>", unsafe_allow_html=True)
                st.divider()
        
        # Display sections and questions
        sections = paper.get("sections", [])
        
        if not sections:
            st.warning("No sections found in the paper.")
        else:
            for section_idx, section in enumerate(sections):
                section_title = section.get("title", f"Section {chr(65 + section_idx)}")
                st.markdown(f'<div class="section-title">{section_title}</div>', unsafe_allow_html=True)
                
                # Show section instructions if available
                section_instructions = section.get("instructions")
                if section_instructions and str(section_instructions).strip():
                    st.markdown(f"*{section_instructions}*")
                
                questions = section.get("questions", [])
                
                if not questions:
                    st.info(f"No questions in {section_title}")
                else:
                    for q in questions:
                        # Display question with the same robust math/diagram renderer used elsewhere.
                        st.markdown(f'<div class="question-text">Q{q["question_number"]}.</div>', unsafe_allow_html=True)
                        render_content_with_formatting(q.get("question", ""), q.get("type", section.get("question_type", "")))

                        visual = q.get("visual")
                        if isinstance(visual, dict) and visual.get("image_base64"):
                            try:
                                import base64 as _base64
                                st.image(_base64.b64decode(visual["image_base64"]), caption=visual.get("title", "Generated graph"), use_container_width=True)
                            except Exception as exc:
                                logger.warning("Could not display paper visual: %s", exc)
                        
                        # Display options for MCQ/TrueFalse
                        if q["type"] in ["Multiple Choice", "True/False"] and q.get("options"):
                            st.markdown('<div class="options-container">', unsafe_allow_html=True)
                            for option in q["options"]:
                                st.markdown(f'<div class="option-text">{option}</div>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Display marks
                        marks = q.get("marks")
                        if marks:
                            st.markdown(f'<div class="marks-badge">Marks: {marks}</div>', unsafe_allow_html=True)
                        
                        # Display metadata in columns
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            difficulty = q.get("difficulty")
                            if difficulty:
                                difficulty_color = {
                                    "easy": "🟢",
                                    "medium": "🟡", 
                                    "hard": "🔴"
                                }.get(difficulty.lower(), "⚪")
                                st.caption(f"**Difficulty:** {difficulty_color} {difficulty}")
                        
                        with col2:
                            q_type = q.get("type")
                            if q_type:
                                st.caption(f"**Type:** {q_type}")
                        
                        with col3:
                            bloom = q.get("bloom_level")
                            if bloom:
                                st.caption(f"**Bloom's:** {bloom}")
                        
                        # Show answer if in teacher mode
                        if st.session_state.get("teacher_mode", False):
                            answer = q.get("answer")
                            if answer:
                                with st.expander(f"📝 Answer (Q{q['question_number']})"):
                                    st.success(f"**Correct Answer:** {answer}")
                                    
                                    explanation = q.get("explanation")
                                    if explanation:
                                        st.info(f"**Explanation:** {explanation}")
                        
                        st.markdown('<div class="question-divider"></div>', unsafe_allow_html=True)
        
        # Teacher-facing answer key
        answer_key = paper.get("answer_key", [])
        if answer_key:
            st.divider()
            st.markdown("## 🔑 Answer Key & Marking Scheme")
            st.caption("This section is kept separate from the student-facing paper so it can be shared only with instructors.")
            for answer_section in answer_key:
                st.markdown(f"### {answer_section.get('section_title', answer_section.get('section_id', 'Section'))}")
                for answer in answer_section.get("answers", []):
                    qnum = answer.get("question_number", "?")
                    marks = answer.get("marks", "")
                    st.markdown(f"**Q{qnum}** · {marks} marks")
                    render_content_with_formatting(str(answer.get("answer", "")), "Long Answer")
                    if answer.get("marking_scheme"):
                        with st.expander(f"Marking scheme — Q{qnum}"):
                            render_content_with_formatting(str(answer["marking_scheme"]), "Long Answer")
                    if answer.get("explanation"):
                        with st.expander(f"Explanation — Q{qnum}"):
                            render_content_with_formatting(str(answer["explanation"]), "Long Answer")

        # Summary statistics
        st.divider()
        st.markdown("### 📊 Paper Summary")
        
        total_q = paper["_metadata"]["total_questions"] if "_metadata" in paper else sum(len(s.get("questions", [])) for s in sections)
        total_marks_calc = sum(
            q.get("marks", 0) 
            for section in sections 
            for q in section.get("questions", [])
        )
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Questions", total_q)
        with col2:
            st.metric("Total Marks", total_marks_calc)
        with col3:
            st.metric("Sections", len(sections))
        with col4:
            # Calculate average difficulty
            difficulties = []
            for section in sections:
                for q in section.get("questions", []):
                    if q.get("difficulty"):
                        difficulties.append(q["difficulty"])
            
            if difficulties:
                diff_count = {
                    "easy": difficulties.count("easy"),
                    "medium": difficulties.count("medium"),
                    "hard": difficulties.count("hard")
                }
                avg_diff = max(diff_count.items(), key=lambda x: x[1])[0] if diff_count else "N/A"
                st.metric("Avg Difficulty", avg_diff.title())
            else:
                st.metric("Avg Difficulty", "N/A")
        
        # ==================== EXPORT FUNCTIONALITY ====================
        st.divider()
        st.markdown("### 📤 Export Options")
        
        # Create export content
        export_content = f"""QUESTION PAPER
    {"=" * 60}

    EXAM: {paper.get('exam_name', 'Question Paper')}
    SUBJECT: {paper.get('subject', paper_subject)}
    TOPIC: {paper.get('topic', 'General')}
    DURATION: {paper.get('duration_minutes', paper_duration)} minutes
    TOTAL MARKS: {paper.get('total_marks', total_marks)}

    {"=" * 60}

    """
        
        # Add instructions
        instructions = paper.get("instructions", [])
        if instructions and isinstance(instructions, list):
            valid_inst = [inst for inst in instructions if inst and str(inst).strip()]
            if valid_inst:
                export_content += "INSTRUCTIONS:\n"
                for i, inst in enumerate(valid_inst, 1):
                    export_content += f"{i}. {inst}\n"
                export_content += "\n"
        
        # Add questions
        for section in sections:
            export_content += f"\n{section.get('title', 'SECTION')}\n"
            export_content += "-" * 50 + "\n\n"
            
            for q in section.get("questions", []):
                export_content += f"Q{q.get('question_number', '?')}. {q.get('question', '')}\n"
                
                # Add options
                options = q.get("options", [])
                if options:
                    for opt in options:
                        export_content += f"   {opt}\n"
                
                # Add metadata
                export_content += f"   [Marks: {q.get('marks', 'N/A')}"
                
                difficulty = q.get("difficulty")
                if difficulty:
                    export_content += f" | Difficulty: {difficulty}"
                
                bloom = q.get("bloom_level")
                if bloom:
                    export_content += f" | Bloom's: {bloom}"
                
                export_content += "]\n\n"
        
        export_content += "\n" + "=" * 60 + "\n"
        export_content += "ANSWER KEY\n"
        export_content += "-" * 50 + "\n"
        for answer_section in paper.get("answer_key", []):
            export_content += f"{answer_section.get('section_title', answer_section.get('section_id', 'SECTION'))}\n"
            for answer in answer_section.get("answers", []):
                export_content += f"Q{answer.get('question_number', '?')}. {answer.get('answer', '')} [Marks: {answer.get('marks', 'N/A')}]\n"
                if answer.get('marking_scheme'):
                    export_content += f"Marking scheme: {answer.get('marking_scheme')}\n"
                if answer.get('explanation'):
                    export_content += f"Explanation: {answer.get('explanation')}\n"
            export_content += "\n"
        export_content += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        export_content += "=" * 60
        
        # Export buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Download as text file
            st.download_button(
                label="📄 Download as Text",
                data=export_content,
                file_name=f"{paper.get('exam_name', 'paper').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True,
                type="secondary"
            )
        
        with col2:
            # Copy to clipboard
            if st.button("📋 Copy to Clipboard", use_container_width=True):
                st.session_state.clipboard_content = export_content
                st.success("✅ Content ready to copy! Use Ctrl+C from the text area below.")
                st.text_area("Paper Content", export_content, height=200, key="export_textarea")
        
        with col3:
            try:
                client = st.session_state.api_client
                pdf_bytes = client.export_paper(paper, "pdf", include_answers=False)
                st.download_button("🖨️ Student PDF", data=pdf_bytes, file_name=f"{paper.get('exam_name','paper').replace(' ','_')}_student.pdf", mime="application/pdf", use_container_width=True)
                teacher_pdf = client.export_paper(paper, "pdf", include_answers=True)
                st.download_button("🔑 Teacher PDF", data=teacher_pdf, file_name=f"{paper.get('exam_name','paper').replace(' ','_')}_teacher.pdf", mime="application/pdf", use_container_width=True)
                docx_bytes = client.export_paper(paper, "docx", include_answers=False)
                st.download_button("📝 Editable DOCX", data=docx_bytes, file_name=f"{paper.get('exam_name','paper').replace(' ','_')}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
            except Exception as exc:
                st.warning(f"Professional export unavailable: {exc}")

        # ==================== QUALITY GATE ====================
        quality = paper.get("quality_results", {})
        if quality:
            st.divider()
            score = quality.get("overall_score", 0)
            st.markdown("### 🛡️ AI Quality Gate")
            st.metric("Paper quality score", f"{score}/100")
            if quality.get("passed"):
                st.success("Quality checks passed. Review the flagged items below before publishing.")
            else:
                st.warning(f"Quality gate found {quality.get('issues_count', 0)} issue(s). Review before publishing.")
            reports = quality.get("question_reports", [])
            flagged = [(i + 1, r) for i, r in enumerate(reports) if r.get("issues")]
            if flagged:
                with st.expander("Review flagged questions", expanded=False):
                    for qnum, report in flagged:
                        st.markdown(f"**Question {qnum} — {report.get('score', 0)}/100**")
                        for issue in report.get("issues", []):
                            st.write(f"• {issue}")

        # ==================== QUESTION BANK ====================
        if st.session_state.get("api_client"):
            with st.expander("📚 Save generated questions to Question Bank"):
                st.caption("Questions are stored locally in the configured SQLite question bank. You can search them later or reuse them in future papers.")
                if st.button("Save all questions", use_container_width=True):
                    saved = 0
                    for section in sections:
                        for q in section.get("questions", []):
                            try:
                                payload_q = dict(q)
                                payload_q["question_text"] = payload_q.get("question", payload_q.get("question_text", ""))
                                payload_q["question_type"] = payload_q.get("type", section.get("question_type", ""))
                                st.session_state.api_client.save_question_to_bank(payload_q, paper.get("topic", ""))
                                saved += 1
                            except Exception as exc:
                                logger.warning("Question bank save failed: %s", exc)
                    st.success(f"Saved {saved} question(s) to the bank.")

        # ==================== TEACHER MODE TOGGLE ====================
        st.divider()
        with st.expander("👨‍🏫 Teacher Options"):
            teacher_mode = st.toggle("Enable Teacher Mode", value=st.session_state.get("teacher_mode", False))
            st.session_state.teacher_mode = teacher_mode
            
            if teacher_mode:
                st.success("Teacher mode enabled - answers are visible")
                
                # Show answer key
                st.markdown("### 📝 Answer Key")
                answer_key_content = ""
                for section in sections:
                    for q in section.get("questions", []):
                        answer = q.get("answer")
                        if answer:
                            answer_key_content += f"Q{q['question_number']}: {answer}\n"
                
                if answer_key_content:
                    st.text_area("Answer Key", answer_key_content, height=200)
                else:
                    st.warning("No answers available in the paper data.")

# ============================================================================
# TAB 3: ASSIGNMENT GENERATOR (Enhanced with Bloom's Taxonomy)
# ============================================================================

# Helper function for key concept extraction
def extract_key_concepts(text, max_concepts=5):
    """
    Extract key concepts from text using simple NLP techniques.
    
    Args:
        text: Input text to extract concepts from
        max_concepts: Maximum number of concepts to return
        
    Returns:
        list: List of key concepts
    """
    import re
    from collections import Counter
    
    if not text or len(text) < 10:
        return []
    
    try:
        # Find capitalized phrases (potential key terms)
        # Pattern matches words starting with capital letters, possibly followed by lowercase
        pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        concepts = re.findall(pattern, text)
        
        # Also find common technical terms (could be lowercase)
        tech_pattern = r'\b(machine learning|neural network|deep learning|algorithm|data|model|training|testing|validation|regression|classification|clustering|python|tensorflow|pytorch|keras|api|database|server|client|framework|library)\b'
        tech_terms = re.findall(tech_pattern, text.lower())
        
        # Combine and count
        all_terms = concepts + tech_terms
        if not all_terms:
            # If no capitalized terms found, take common words
            words = re.findall(r'\b\w{4,}\b', text.lower())
            # Filter out common stop words
            stop_words = {'this', 'that', 'with', 'from', 'have', 'were', 'will', 'would', 'could', 'should', 'their', 'there', 'about', 'which'}
            words = [w for w in words if w not in stop_words and len(w) > 3]
            common_words = Counter(words).most_common(max_concepts)
            return [word for word, count in common_words]
        
        # Count frequencies and return top concepts
        concept_counts = Counter(all_terms)
        top_concepts = [concept for concept, count in concept_counts.most_common(max_concepts)]
        
        return top_concepts
        
    except Exception as e:
        # Fallback to simple word extraction
        words = re.findall(r'\b\w{5,}\b', text.lower())
        common_words = Counter(words).most_common(max_concepts)
        return [word for word, count in common_words]

with tab3:
    # Get theme from session state
    current_theme = st.session_state.get('theme', 'dark')
    
    # Theme-specific colors - FIXED for light theme
    theme_colors = {
        'dark': {
            'bg': '#1E1E2E',
            'card': '#2D2D3F',
            'text': '#FFFFFF',
            'accent': '#8b5cf6',
            'secondary': '#10b981',
            'border': '#374151',
            'header_bg': '#0F0F1A',
            'text_secondary': '#9CA3AF',
            'card_text': '#FFFFFF'
        },
        'light': {
            'bg': '#F3F4F6',
            'card': '#FFFFFF',
            'text': '#111827',
            'accent': '#7c3aed',
            'secondary': '#059669',
            'border': '#E5E7EB',
            'header_bg': '#FFFFFF',
            'text_secondary': '#6B7280',
            'card_text': '#111827'
        }
    }
    
    colors = theme_colors[current_theme]
    
    # Custom CSS for theme-aware styling
    st.markdown(f"""
    <style>
    /* Theme-aware styles */
    .stApp {{
        background-color: {colors['bg']};
    }}
    
    .main-header {{
        color: {colors['text']} !important;
    }}
    
    .bloom-card {{
        background-color: {colors['card']};
        border: 1px solid {colors['border']};
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        color: {colors['card_text']};
    }}
    
    .bloom-level {{
        background: linear-gradient(135deg, {colors['accent']}20, {colors['secondary']}20);
        border-left: 4px solid {colors['accent']};
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        color: {colors['text']};
    }}
    
    .bloom-badge {{
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 0.5rem;
        color: white;
    }}
    
    .remember-badge {{ background: #3B82F6; color: white; }}
    .understand-badge {{ background: #10B981; color: white; }}
    .apply-badge {{ background: #F59E0B; color: white; }}
    .analyze-badge {{ background: #8B5CF6; color: white; }}
    .evaluate-badge {{ background: #EF4444; color: white; }}
    .create-badge {{ background: #EC4899; color: white; }}
    
    .task-card {{
        background: {colors['card']};
        border: 1px solid {colors['border']};
        border-radius: 12px;
        padding: 1.25rem;
        margin: 1rem 0;
        transition: transform 0.2s;
        color: {colors['card_text']};
    }}
    
    .task-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 12px rgba(0, 0, 0, 0.15);
    }}
    
    .task-card h3 {{
        color: {colors['text']} !important;
    }}
    
    .task-card p {{
        color: {colors['text_secondary']};
    }}
    
    .bloom-indicator {{
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        border-radius: 16px;
        font-size: 0.8rem;
        font-weight: 500;
        color: white;
    }}
    
    /* Fix for text colors in light theme */
    .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6 {{
        color: {colors['text']} !important;
    }}
    
    .stExpander {{
        background-color: {colors['card']};
        border: 1px solid {colors['border']};
        border-radius: 8px;
    }}
    
    .stInfo {{
        background-color: {colors['card']};
        color: {colors['text']};
        border: 1px solid {colors['border']};
    }}
    </style>
    """, unsafe_allow_html=True)

    display_header("📚 Generate Assignment with Bloom's Taxonomy", 
                   "Create practice assignments with cognitive level tracking")
    
    st.markdown("### 📋 Assignment Configuration")
    
    # Main configuration in columns
    col1, col2 = st.columns(2)
    with col1:
        assign_name = st.text_input("📝 Assignment Name", 
                                   value="ML Assignment 1", 
                                   key="assign_name",
                                   help="Enter a descriptive name for the assignment")
        assign_code = st.text_input("🔢 Course Code", 
                                   value="CS-501", 
                                   key="assign_code",
                                   help="Course code (e.g., CS-501)")
    with col2:
        assign_subject = st.selectbox(
            "📚 Subject",
            ["Machine Learning", "Deep Learning", "Natural Language Processing", "Computer Vision", 
             "Artificial Intelligence", "Reinforcement Learning", "Data Science", "Cryptography"],
            key="assign_subject",
            help="Select the main subject area"
        )
    
    st.divider()
    
    # ========================================================================
    # BLOOM'S TAXONOMY CONFIGURATION
    # ========================================================================
    st.markdown("### 🧠 Cognitive Level Configuration (Bloom's Taxonomy)")
    
    # Bloom's taxonomy levels with descriptions
    bloom_levels = {
        "Remember": {
            "icon": "🔵",
            "color": "#3B82F6",
            "description": "Recall facts and basic concepts",
            "verbs": "Define, List, Recall, Name, Identify",
            "cognitive_demand": "Lowest - Simple recall",
            "default_weight": 10
        },
        "Understand": {
            "icon": "🟢",
            "color": "#10B981",
            "description": "Explain ideas or concepts",
            "verbs": "Explain, Describe, Summarize, Interpret",
            "cognitive_demand": "Low - Comprehension",
            "default_weight": 15
        },
        "Apply": {
            "icon": "🟠",
            "color": "#F59E0B",
            "description": "Use information in new situations",
            "verbs": "Apply, Demonstrate, Solve, Use",
            "cognitive_demand": "Medium - Application",
            "default_weight": 25
        },
        "Analyze": {
            "icon": "🟣",
            "color": "#8B5CF6",
            "description": "Draw connections among ideas",
            "verbs": "Analyze, Compare, Contrast, Examine",
            "cognitive_demand": "Medium-High - Analysis",
            "default_weight": 20
        },
        "Evaluate": {
            "icon": "🔴",
            "color": "#EF4444",
            "description": "Justify a stand or decision",
            "verbs": "Evaluate, Critique, Assess, Judge",
            "cognitive_demand": "High - Evaluation",
            "default_weight": 15
        },
        "Create": {
            "icon": "🟤",
            "color": "#EC4899",
            "description": "Produce new or original work",
            "verbs": "Create, Design, Develop, Formulate",
            "cognitive_demand": "Highest - Synthesis",
            "default_weight": 15
        }
    }
    
    # Bloom's taxonomy selection with hierarchy
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Primary Bloom level selector (with hierarchy inheritance)
        primary_bloom_level = st.selectbox(
            "🎯 Primary Cognitive Level",
            options=list(bloom_levels.keys()),
            index=2,  # Default to Apply
            key="primary_bloom",
            help="Select the highest cognitive level. Lower levels will be automatically included."
        )
        
        # Show selected level details
        selected_level = bloom_levels[primary_bloom_level]
        st.markdown(f"""
        <div class="bloom-level">
            <span class="bloom-badge" style="background: {selected_level['color']};">
                {selected_level['icon']} {primary_bloom_level}
            </span>
            <p style="margin-top: 0.5rem; color: {colors['text']};"><strong>Description:</strong> {selected_level['description']}</p>
            <p style="color: {colors['text']};"><strong>Action Verbs:</strong> {selected_level['verbs']}</p>
            <p style="color: {colors['text']};"><strong>Cognitive Demand:</strong> {selected_level['cognitive_demand']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Automatically include lower levels
        bloom_keys = list(bloom_levels.keys())
        selected_index = bloom_keys.index(primary_bloom_level)
        included_levels = bloom_keys[:selected_index + 1]
        
        st.info(f"""✅ **Included Levels:** {', '.join([f'{bloom_levels[lvl]["icon"]} {lvl}' for lvl in included_levels])}""")
    
    with col2:
        st.markdown("#### 📊 Bloom's Distribution")
        st.markdown("Adjust the percentage distribution across levels")
        
        # Create distribution sliders for included levels
        bloom_distribution = {}
        total_percentage = 0
        
        # Show sliders only for included levels
        for level in included_levels:
            default_weight = bloom_levels[level]["default_weight"]
            # Adjust default weights to sum to 100
            total_default = sum(bloom_levels[l]["default_weight"] for l in included_levels)
            adjusted_default = int(default_weight * (100 / total_default)) if total_default > 0 else 0
            
            percentage = st.slider(
                f"{bloom_levels[level]['icon']} {level}",
                min_value=0,
                max_value=100,
                value=adjusted_default,
                key=f"bloom_dist_{level}",
                help=f"Weight for {level} level questions"
            )
            bloom_distribution[level] = percentage
            total_percentage += percentage
        
        # Show total and validation
        if total_percentage != 100:
            st.warning(f"⚠️ Total distribution: {total_percentage}% (should be 100%)")
        else:
            st.success(f"✅ Total: {total_percentage}%")
    
    st.divider()
    
    # ========================================================================
    # ASSIGNMENT DETAILS
    # ========================================================================
    col1, col2, col3 = st.columns(3)
    with col1:
        assignment_type = st.selectbox(
            "📂 Assignment Type",
            ["Coding Problem", "Essay", "Case Study", "Problem Solving", "Research", "Project", "Theoretical", "Practical"],
            key="assign_type",
            help="Select the type of assignment"
        )
    with col2:
        assign_num = st.slider("📝 Number of Tasks", 1, 15, 5, key="assign_num",
                              help="Number of individual tasks in the assignment")
    with col3:
        total_points = st.slider("📊 Total Points", 10, 200, 100, key="assign_points",
                                help="Total marks for the assignment")
    
    col1, col2 = st.columns(2)
    with col1:
        due_days = st.slider("📅 Due in (days)", 1, 30, 7, key="assign_due",
                            help="Number of days until submission")
    with col2:
        submission_format = st.selectbox(
            "📤 Submission Format",
            ["PDF", "Jupyter Notebook", "Code Repository", "Google Doc", "Any Format"],
            key="assign_format",
            help="Required format for submission"
        )
    
    # Topic input with autocomplete suggestions
    assign_topic = st.text_input(
        "📌 Specific Topic (Optional)",
        placeholder="e.g., Neural Networks, Decision Trees, Clustering Algorithms",
        key="assign_topic",
        help="Leave blank to use subject as topic"
    )
    
    assign_description = st.text_area(
        "📋 Assignment Description & Requirements",
        height=120,
        placeholder="Describe the assignment goals, specific topics to cover, requirements, and any special instructions...",
        value=f"Create a comprehensive {assignment_type.lower()} on {assign_subject} that demonstrates {primary_bloom_level} level understanding.",
        key="assign_description",
        help="Provide detailed instructions for the assignment"
    )
    
    # ========================================================================
    # INTERACTIVE CHAT CONTEXT
    # ========================================================================
    with st.expander("💬 Interactive Context (Optional)", expanded=False):
        st.markdown("""
        Provide additional context through chat. This helps customize the assignment 
        to your specific needs.
        """)
        
        # Chat-like interface for context
        col1, col2 = st.columns([3, 1])
        with col1:
            chat_input = st.text_input(
                "💭 Add context message",
                placeholder="e.g., Focus on real-world applications, include ethical considerations, etc.",
                key="chat_context_input"
            )
        with col2:
            if st.button("➕ Add", use_container_width=True):
                if chat_input:
                    if 'chat_messages' not in st.session_state:
                        st.session_state.chat_messages = []
                    st.session_state.chat_messages.append(chat_input)
                    st.rerun()
        
        # Display chat messages
        if 'chat_messages' in st.session_state and st.session_state.chat_messages:
            st.markdown("**Context Messages:**")
            for i, msg in enumerate(st.session_state.chat_messages):
                col_msg1, col_msg2 = st.columns([10, 1])
                with col_msg1:
                    st.markdown(f"💬 {msg}")
                with col_msg2:
                    if st.button("✕", key=f"remove_msg_{i}"):
                        st.session_state.chat_messages.pop(i)
                        st.rerun()
            
            if st.button("Clear All", key="clear_chat"):
                st.session_state.chat_messages = []
                st.rerun()
    
    # ========================================================================
    # CODE GENERATION OPTIONS
    # ========================================================================
    if assignment_type in ["Coding Problem", "Project", "Practical"]:
        st.markdown("#### ⚙️ Code Generation Options")
        col1, col2, col3 = st.columns(3)
        with col1:
            include_starter = st.checkbox("📄 Include Starter Code", value=True, 
                                        key="assign_starter",
                                        help="Provide starter code for tasks")
        with col2:
            include_solutions = st.checkbox("🔐 Include Solutions", value=True, 
                                          key="assign_solutions",
                                          help="Include solution code (instructor only)")
        with col3:
            include_tests = st.checkbox("🧪 Include Test Cases", value=True, 
                                      key="assign_tests",
                                      help="Generate test cases for verification")
    else:
        include_starter = False
        include_solutions = True
        include_tests = False
    
    st.divider()
    
    # ========================================================================
    # DOCUMENT-BASED GENERATION
    # ========================================================================
    st.markdown("### 📄 Document-Based Generation")
    
    use_assign_document = st.checkbox("📤 Use document content for generation", 
                                     value=False, 
                                     key="assign_use_doc",
                                     help="Upload a document to base the assignment on")
    
    assign_document_text = None
    
    if use_assign_document:
        assign_uploaded_file = st.file_uploader(
            "📁 Upload document (PDF, DOCX, or TXT)",
            type=["pdf", "docx", "txt"],
            key="assign_doc_upload",
            help="Upload lecture notes, textbook chapters, or reference materials"
        )
        
        if assign_uploaded_file:
            try:
                with st.spinner("📖 Extracting document content..."):
                    assign_document_text = extract_document_text(assign_uploaded_file)
                    
                st.success(f"✅ Successfully extracted {len(assign_document_text)} characters")
                
                # Document preview with theme-aware styling
                with st.expander("👁️ Document Preview", expanded=False):
                    preview_text = assign_document_text[:1000] + "..." if len(assign_document_text) > 1000 else assign_document_text
                    st.text_area("Extracted Content", value=preview_text, height=200, disabled=True)
                    
                    # Key concepts extraction
                    st.markdown("**📌 Key Concepts Detected:**")
                    key_concepts = extract_key_concepts(assign_document_text)
                    if key_concepts:
                        for concept in key_concepts[:5]:
                            st.markdown(f"• {concept}")
                    else:
                        st.markdown("No key concepts detected")
                        
            except Exception as e:
                st.error(f"❌ Error processing document: {str(e)}")
                assign_document_text = None
    
    st.divider()
    
    # ========================================================================
    # GENERATION BUTTON
    # ========================================================================
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        generate_button = st.button(
            "🚀 Generate Assignment with Bloom's Taxonomy", 
            type="primary", 
            use_container_width=True,
            key="assign_generate",
            disabled=total_percentage != 100 if 'total_percentage' in locals() else False
        )
    
    # ========================================================================
    # ASSIGNMENT GENERATION AND DISPLAY
    # ========================================================================
    if generate_button:
        try:
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Step 1: Initialize
            status_text.info("🚀 Initializing assignment generation...")
            progress_bar.progress(10)
            
            client = st.session_state.api_client
            
            # Step 2: Prepare context
            status_text.info("📝 Preparing context with Bloom's taxonomy...")
            progress_bar.progress(20)
            
            # Combine chat messages into context
            chat_context = "\n".join(st.session_state.get('chat_messages', []))
            
            # Step 3: Generate assignment
            status_text.info("🔄 Generating tasks with Bloom's taxonomy levels...")
            progress_bar.progress(40)
            
            # Prepare distribution for API
            bloom_distribution_dict = {
                level: weight 
                for level, weight in bloom_distribution.items() 
                if weight > 0
            }
            
            # Call API with document if provided
            if assign_document_text:
                response = client.generate_assignment_from_document(
                    document_text=assign_document_text,
                    name=assign_name,
                    course_code=assign_code,
                    subject=assign_subject,
                    assignment_type=assignment_type,
                    difficulty="custom",
                    max_marks=total_points,
                    duration_days=due_days,
                    num_tasks=assign_num,
                    description=assign_description,
                    bloom_distribution=bloom_distribution_dict,
                    chat_context=chat_context,
                    topic=assign_topic if assign_topic else assign_subject
                )
            else:
                response = client.generate_assignment(
                    name=assign_name,
                    course_code=assign_code,
                    subject=assign_subject,
                    topic=assign_topic if assign_topic else assign_subject,
                    assignment_type=assignment_type,
                    difficulty="custom",
                    max_marks=total_points,
                    duration_days=due_days,
                    num_tasks=assign_num,
                    description=assign_description,
                    include_solutions=include_solutions,
                    include_starter_code=include_starter,
                    include_test_cases=include_tests,
                    bloom_distribution=bloom_distribution_dict,
                    chat_context=chat_context
                )
            
            progress_bar.progress(80)
            
            # Extract assignment data
            assignment_data = response
            tasks = assignment_data.get('tasks', [])
            
            progress_bar.progress(100)
            status_text.success(f"✅ Assignment generated with {len(tasks)} tasks!")
            st.balloons()
            
            # Store in session state
            st.session_state.generated_assignment = assignment_data
            st.session_state.generated_assignment_display = {
                'assign_name': assign_name,
                'assign_code': assign_code,
                'assign_subject': assign_subject,
                'assignment_type': assignment_type,
                'primary_bloom_level': primary_bloom_level,
                'bloom_distribution': bloom_distribution,
                'due_days': due_days,
                'total_points': total_points,
                'assign_description': assign_description,
                'tasks': tasks,
                'submission_guidelines': assignment_data.get('submission_guidelines', []),
                'evaluation_criteria': assignment_data.get('evaluation_criteria', []),
                'learning_objectives': assignment_data.get('learning_objectives', []),
                'generated_files': assignment_data.get('generated_files', [])
            }
            
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error generating assignment: {str(e)}")
            import traceback
            with st.expander("🔍 Error Details"):
                st.code(traceback.format_exc())
    
    # ========================================================================
    # DISPLAY GENERATED ASSIGNMENT (from session state)
    # ========================================================================
    if 'generated_assignment_display' in st.session_state:
        display_data = st.session_state.generated_assignment_display
        
        st.divider()
        
        # Header with theme-aware styling
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {colors['accent']} 0%, {colors['secondary']} 100%); 
                    padding: 2.5rem; border-radius: 20px; margin: 1rem 0; 
                    text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.2);">
            <h1 style="color: white; margin: 0; font-size: 2.5rem;">📚 {display_data['assign_name']}</h1>
            <p style="color: rgba(255,255,255,0.95); margin: 0.5rem 0; font-size: 1.1rem;">
                {display_data['assign_code']} | {display_data['assign_subject']} | {display_data['assignment_type']}
            </p>
            <div style="display: flex; justify-content: center; gap: 2rem; margin-top: 1rem;">
                <span style="color: white; background: rgba(255,255,255,0.2); padding: 0.5rem 1rem; border-radius: 30px;">
                    📅 Due: {display_data['due_days']} days
                </span>
                <span style="color: white; background: rgba(255,255,255,0.2); padding: 0.5rem 1rem; border-radius: 30px;">
                    📊 {display_data['total_points']} points
                </span>
                <span style="color: white; background: rgba(255,255,255,0.2); padding: 0.5rem 1rem; border-radius: 30px;">
                    🧠 Primary: {display_data['primary_bloom_level']}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Description
        st.info(f"**📋 Description:** {display_data['assign_description']}")
        
        # Bloom's Distribution Summary
        with st.expander("📊 Bloom's Taxonomy Distribution", expanded=True):
            cols = st.columns(len(display_data['bloom_distribution']))
            for idx, (level, weight) in enumerate(display_data['bloom_distribution'].items()):
                with cols[idx]:
                    level_info = bloom_levels[level]
                    st.markdown(f"""
                    <div style="text-align: center; padding: 1rem; 
                               background: {level_info['color']}20; 
                               border-radius: 12px;">
                        <span style="font-size: 2rem;">{level_info['icon']}</span>
                        <h4 style="margin: 0.5rem 0; color: {colors['text']};">{level}</h4>
                        <div style="font-size: 1.5rem; font-weight: bold; color: {level_info['color']};">
                            {weight}%
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Submission Guidelines
        if display_data['submission_guidelines']:
            with st.expander("📤 Submission Guidelines", expanded=True):
                for guideline in display_data['submission_guidelines']:
                    st.markdown(f"• {guideline}")
        
        # Evaluation Criteria with Bloom's alignment
        if display_data['evaluation_criteria']:
            with st.expander("📊 Evaluation Criteria (Bloom's Aligned)", expanded=True):
                for c in display_data['evaluation_criteria']:
                    bloom_level = c.get('bloom_level', 'Understand')
                    level_info = bloom_levels.get(bloom_level, bloom_levels['Understand'])
                    weight = int(c.get('weight', 0) * 100)
                    criterion = c.get('criterion', '')
                    desc = c.get('description', '')
                    st.markdown(f"""
                    <div style="padding: 0.5rem; margin: 0.5rem 0; 
                               background: {colors['card']}; border-radius: 8px;
                               border: 1px solid {colors['border']};">
                        <span class="bloom-badge" style="background: {level_info['color']};">
                            {level_info['icon']} {bloom_level}
                        </span>
                        <strong style="color: {colors['text']};">{criterion}</strong> ({weight}%) - {desc}
                    </div>
                    """, unsafe_allow_html=True)
        
        # Learning Objectives
        if display_data['learning_objectives']:
            with st.expander("🎯 Learning Objectives", expanded=True):
                for obj in display_data['learning_objectives']:
                    st.markdown(f"✅ {obj}")
        
        st.divider()
        
        # ========================================================================
        # TASKS DISPLAY
        # ========================================================================
        st.markdown("### 📝 Assignment Tasks")
        
        for idx, task in enumerate(display_data['tasks']):
            task_bloom = task.get('bloom_level', task.get('cognitive_level', 'Understand'))
            level_info = bloom_levels.get(task_bloom, bloom_levels['Understand'])
            
            with st.container():
                st.markdown(f"""
                <div class="task-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h3 style="margin: 0; color: {colors['text']};">Task {idx + 1}: {task.get('title', f'Task {idx+1}')}</h3>
                        <span class="bloom-badge" style="background: {level_info['color']};">
                            {level_info['icon']} {task_bloom}
                        </span>
                    </div>
                    <p style="margin: 1rem 0; color: {colors['text_secondary']};">{task.get('description', '')}</p>
                    <div style="display: flex; gap: 1rem; margin: 1rem 0;">
                        <span style="background: {colors['border']}; padding: 0.25rem 1rem; border-radius: 20px; color: {colors['text']};">
                            📊 {task.get('points', 0)} points
                        </span>
                        <span style="background: {colors['border']}; padding: 0.25rem 1rem; border-radius: 20px; color: {colors['text']};">
                            {level_info['verbs'].split(',')[0].strip()}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Task details expander
                with st.expander(f"📋 Task {idx + 1} Details", expanded=False):
                    # Requirements
                    task_requirements = task.get('requirements', [])
                    if task_requirements:
                        st.markdown("**📋 Requirements:**")
                        for req in task_requirements:
                            st.markdown(f"• {req}")
                    
                    # Expected Output
                    task_expected = task.get('expected_output', task.get('expected_deliverable', ''))
                    if task_expected:
                        st.markdown("**✅ Expected Output:**")
                        st.info(task_expected)
                    
                    # Hints
                    task_hints = task.get('hints', [])
                    if task_hints:
                        st.markdown("**💡 Hints:**")
                        if isinstance(task_hints, list):
                            for hint in task_hints:
                                st.success(f"• {hint}")
                        else:
                            st.success(task_hints)
                    
                    # Bloom's justification
                    bloom_justification = task.get('bloom_justification', '')
                    if bloom_justification:
                        st.markdown("**🧠 Bloom's Level Justification:**")
                        st.caption(bloom_justification)
                    
                    # Starter code
                    task_starter = task.get('starter_code', '')
                    if task_starter:
                        with st.expander("📄 Starter Code", expanded=False):
                            st.code(task_starter, language="python")
                    
                    # Solution (instructor only)
                    task_solution = task.get('solution_code', '')
                    if task_solution and include_solutions:
                        with st.expander("🔐 Solution (Instructor Only)", expanded=False):
                            st.code(task_solution, language="python")
        
        # ========================================================================
        # GENERATED FILES
        # ========================================================================
        if display_data['generated_files']:
            st.divider()
            st.markdown("### 📁 Generated Files")
            
            file_tabs = st.tabs([f"📄 {f.get('filename', 'file')}" for f in display_data['generated_files']])
            for i, (file_tab, file_info) in enumerate(zip(file_tabs, display_data['generated_files'])):
                with file_tab:
                    filename = file_info.get('filename', 'file')
                    content = file_info.get('content', '')
                    file_type = file_info.get('file_type', '')
                    language = file_info.get('language', 'text')
                    description = file_info.get('description', '')
                    
                    st.markdown(f"**{description}**")
                    st.markdown(f"*Type: {file_type}*")
                    
                    if language in ['python', 'javascript', 'java', 'cpp']:
                        st.code(content, language=language)
                    elif language == 'markdown':
                        st.markdown(content)
                    else:
                        st.code(content)
                    
                    st.download_button(
                        label=f"📥 Download {filename}",
                        data=content,
                        file_name=filename,
                        mime="text/plain",
                        key=f"download_file_display_{i}",
                        use_container_width=True
                    )
        
        st.divider()
        
        # ========================================================================
        # EXPORT OPTIONS
        # ========================================================================
        col_exp1, col_exp2, col_exp3 = st.columns(3)
        
        with col_exp1:
            json_str = json.dumps(st.session_state.generated_assignment, indent=2)
            st.download_button(
                label="📥 Download JSON",
                data=json_str,
                file_name=f"assignment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
                key="download_json_display"
            )
        
        with col_exp2:
            # Create markdown export with Bloom's taxonomy
            md_export = f"""# {display_data['assign_name']}
**Course:** {display_data['assign_code']} | **Subject:** {display_data['assign_subject']}  
**Type:** {display_data['assignment_type']} | **Primary Bloom's Level:** {display_data['primary_bloom_level']}  
**Total Points:** {display_data['total_points']} | **Due:** {display_data['due_days']} days

## Description
{display_data['assign_description']}

## Bloom's Taxonomy Distribution
"""
            for level, weight in display_data['bloom_distribution'].items():
                level_info = bloom_levels[level]
                md_export += f"- {level_info['icon']} **{level}**: {weight}%\n"
            
            md_export += "\n## Tasks\n"
            for idx, task in enumerate(display_data['tasks'], 1):
                task_bloom = task.get('bloom_level', 'Understand')
                level_info = bloom_levels.get(task_bloom, bloom_levels['Understand'])
                md_export += f"\n### {idx}. {task.get('title', f'Task {idx}')} [{level_info['icon']} {task_bloom}]\n"
                md_export += f"**Points:** {task.get('points', 0)}\n\n"
                md_export += f"{task.get('description', '')}\n\n"
                
                requirements = task.get('requirements', [])
                if requirements:
                    md_export += "**Requirements:**\n"
                    for req in requirements:
                        md_export += f"- {req}\n"
                    md_export += "\n"
            
            st.download_button(
                label="📄 Download Markdown",
                data=md_export,
                file_name=f"assignment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True,
                key="download_md_display"
            )
        
        with col_exp3:
            # Create PDF-friendly HTML export
            html_export = f"""
            <html>
            <head><title>{display_data['assign_name']}</title></head>
            <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
                <h1>{display_data['assign_name']}</h1>
                <p><strong>Course:</strong> {display_data['assign_code']} | <strong>Subject:</strong> {display_data['assign_subject']}</p>
                <p><strong>Bloom's Primary Level:</strong> {display_data['primary_bloom_level']}</p>
                <p><strong>Total Points:</strong> {display_data['total_points']} | <strong>Due:</strong> {display_data['due_days']} days</p>
                <hr>
                <h2>Description</h2>
                <p>{display_data['assign_description']}</p>
                <hr>
                <h2>Tasks</h2>
            """
            
            for idx, task in enumerate(display_data['tasks'], 1):
                html_export += f"""
                <h3>{idx}. {task.get('title', f'Task {idx}')}</h3>
                <p><strong>Points:</strong> {task.get('points', 0)}</p>
                <p>{task.get('description', '')}</p>
                """
            
            html_export += """
            </body>
            </html>
            """
            
            st.download_button(
                label="📄 Download HTML",
                data=html_export,
                file_name=f"assignment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                mime="text/html",
                use_container_width=True,
                key="download_html_display"
            )





# ============================================================================
# TAB 4: CUSTOMISED QUESTION GENERATION WITH BLOOM'S TAXONOMY
# ============================================================================

with tab4:
    display_header("🎓 Bloom's Taxonomy Question Generator", "Generate MTech-level questions calibrated to specific cognitive levels")
    
    # ========================================================================
    # CONFIGURATION SECTION
    # ========================================================================
    st.markdown("### ⚙️ Configuration")
    
    # Input layout matching Tab 1 style
    col1, col2, col3 = st.columns([2.4, 2.4, 2.4], gap="large")
    
    with col1:
        chat_topic = st.text_input(
            "📚 **Topic/Subject**",
            placeholder="e.g., Deep Learning, Natural Language Processing, Computer Vision...",
            key="bloom_topic",
            help="Enter the main topic for question generation"
        )
    
    with col2:
        # All question types with emojis
        question_types = {
            "Multiple Choice": "📝",
            "Long Answer": "📄",
            "Short Answer": "📝",
            "Diagram-Based": "📊",
            "Code-Based": "💻",
            "Code Implementation": "💻",
            "Code Output Prediction": "🖥️",
            "Coding Problem": "💻",
            "Numerical Problem": "🔢",
            "True/False": "✅",
            "Essay": "📄",
            "Scenario-Based": "🎯"
        }
        
        question_type = st.selectbox(
            "❓ **Question Type**",
            options=list(question_types.keys()),
            format_func=lambda x: f"{question_types[x]} {x}",
            key="bloom_question_type",
            help="Select the format of questions to generate"
        )
    
    with col3:
        st.markdown(" ")  # Placeholder for alignment
    
    # ========================================================================
    # BLOOM'S TAXONOMY SELECTION - HIERARCHICAL RADIO
    # ========================================================================
    st.markdown("---")
    st.markdown("### 🧠 **Bloom's Taxonomy Level**")
    st.markdown("*Select the highest cognitive level - all lower levels will be automatically included*")
    
    # Initialize selected bloom level in session state
    if "selected_bloom_level" not in st.session_state:
        st.session_state.selected_bloom_level = "Apply"  # Default
    
    # Define Bloom's taxonomy hierarchy
    bloom_hierarchy = ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]
    
    bloom_options = {
        "Remember": "🔵 Recall facts and basic concepts",
        "Understand": "🟢 Explain ideas or concepts",
        "Apply": "🟠 Use information in new situations",
        "Analyze": "🟣 Draw connections among ideas",
        "Evaluate": "🔴 Justify a stand or decision",
        "Create": "🟤 Produce new or original work"
    }
    
    # Use radio for hierarchical selection
    selected_top_level = st.radio(
        "**Select highest cognitive level:**",
        options=bloom_hierarchy,
        index=bloom_hierarchy.index(st.session_state.selected_bloom_level),
        horizontal=True,
        key="bloom_hierarchy_radio",
        help="Select the highest level - all lower levels will be automatically included"
    )
    
    # Update session state
    st.session_state.selected_bloom_level = selected_top_level
    
    # Calculate selected levels (all levels up to and including selected)
    selected_levels = bloom_hierarchy[:bloom_hierarchy.index(selected_top_level) + 1]
    
    # Show selected levels as badges
    if selected_levels:
        badges_html = ""
        for level in selected_levels:
            color = {
                "Remember": "#4299E1",
                "Understand": "#48BB78", 
                "Apply": "#ED8936",
                "Analyze": "#9F7AEA",
                "Evaluate": "#F56565",
                "Create": "#D69E2E"
            }.get(level, "#0EA5E9")
            
            badges_html += f'<span style="background: {color}; color: white; padding: 0.25rem 0.75rem; border-radius: 20px; margin-right: 0.5rem; font-size: 0.85rem;">{bloom_options[level].split()[0]} {level}</span>'
        
        st.markdown(f"""
        <div style="margin: 1rem 0;">
            <span style="color: var(--text-secondary); margin-right: 1rem;">✅ Selected levels:</span>
            {badges_html}
        </div>
        """, unsafe_allow_html=True)
    
    # ========================================================================
    # TOPIC FOCUS (OPTIONAL)
    # ========================================================================
    with st.expander("🔍 **Topic Focus** (Optional)", expanded=False):
        topic_focus = st.text_input(
            "Specific subtopics",
            placeholder="e.g., Transformers, Attention Mechanism, BERT (comma-separated)",
            key="bloom_topic_focus",
            help="Enter specific areas within the main topic to focus on"
        )
        
        require_justification = st.checkbox(
            "Include Bloom's level justification in explanation",
            value=True,
            key="bloom_justification",
            help="Adds explicit reasoning why the question targets the selected Bloom's level"
        )
    
    # ========================================================================
    # DOCUMENT UPLOAD SECTION
    # ========================================================================
    with st.expander("📄 **Document Upload for Context** (Optional)", expanded=False):
        st.markdown("""
        <div style="background: var(--card-bg); border: 2px dashed var(--border-color); border-radius: 10px; padding: 20px; text-align: center; margin-bottom: 15px;">
            <span style="font-size: 2rem;">📎</span>
            <p style="color: var(--text-secondary); margin: 10px 0;">Upload lecture notes, research papers, or any relevant document</p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['txt', 'pdf', 'docx', 'md'],
            help="Upload TXT, PDF, DOCX, or MD files",
            key="bloom_document_upload",
            label_visibility="collapsed"
        )
        
        if uploaded_file is not None:
            try:
                # Store file info in session state
                st.session_state.bloom_uploaded_file = {
                    "name": uploaded_file.name,
                    "type": uploaded_file.type,
                    "bytes": uploaded_file.getvalue(),
                    "size": uploaded_file.size
                }
                
                # Show file preview
                st.markdown(f"""
                <div style="background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 8px; padding: 15px; margin-top: 10px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 1.5rem;">📄</span>
                        <div>
                            <strong>{uploaded_file.name}</strong><br>
                            <span style="font-size: 0.8rem; color: var(--text-secondary);">
                                {(uploaded_file.size / 1024):.1f} KB • {uploaded_file.type}
                            </span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
                st.session_state.bloom_uploaded_file = None
        else:
            st.session_state.bloom_uploaded_file = None
        
        st.divider()
        
        # Manual context input
        additional_context = st.text_area(
            "📝 Additional context (optional)",
            placeholder="Enter any specific instructions, requirements, or context for question generation...",
            height=80,
            key="bloom_additional_context",
            help="Add any specific requirements or context"
        )
    
    st.divider()
    
    # ========================================================================
    # CHAT INTERFACE
    # ========================================================================
    st.markdown("### 💬 Chat with Question Generator")
    
    # Initialize session state for chat
    if "bloom_chat_history" not in st.session_state:
        st.session_state.bloom_chat_history = []
    
    if "bloom_questions" not in st.session_state:
        st.session_state.bloom_questions = []
    
    # Custom CSS for theme-aware text colors
    st.markdown("""
    <style>
    /* Theme-aware text colors for answer and explanation boxes */
    .answer-box {
        background-color: #ecfdf5;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #10b981;
        color: #1f2937 !important;
    }
    .explanation-box {
        background-color: #fffbeb;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #f59e0b;
        color: #1f2937 !important;
    }
    .options-box {
        background-color: #f0f9ff;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #0EA5E9;
        color: #1f2937 !important;
        margin-bottom: 1rem;
    }
    
    /* Dark mode overrides */
    @media (prefers-color-scheme: dark) {
        .answer-box {
            background-color: #064e3b;
            border-left: 4px solid #10b981;
            color: #f3f4f6 !important;
        }
        .explanation-box {
            background-color: #78350f;
            border-left: 4px solid #f59e0b;
            color: #f3f4f6 !important;
        }
        .options-box {
            background-color: #1e3a8a;
            border-left: 4px solid #0EA5E9;
            color: #f3f4f6 !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Chat display
    chat_container = st.container(height=300, border=True)
    
    with chat_container:
        if not st.session_state.bloom_chat_history:
            st.info("👋 Start a conversation! Ask for questions, request modifications, or specify focus areas.")
        else:
            for msg in st.session_state.bloom_chat_history:
                if msg["role"] == "user":
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                padding: 12px; border-radius: 15px 15px 5px 15px; 
                                margin: 10px 0; max-width: 80%; margin-left: auto;">
                        <b style="color: white;">🧑‍💻 You:</b><br>
                        <span style="color: white;">{msg['content']}</span>
                        <div style="font-size: 0.7rem; color: rgba(255,255,255,0.7); margin-top: 5px;">{msg.get('timestamp', '')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background: var(--card-bg); 
                                padding: 12px; border-radius: 15px 15px 15px 5px; 
                                margin: 10px 0; max-width: 80%; border: 1px solid var(--border-color);">
                        <b style="color: #0EA5E9;">🤖 AI:</b><br>
                        <span style="color: var(--text-primary);">{msg['content']}</span>
                        <div style="font-size: 0.7rem; color: var(--text-secondary); margin-top: 5px;">{msg.get('timestamp', '')}</div>
                    </div>
                    """, unsafe_allow_html=True)
    
    # Chat input
    col1, col2 = st.columns([5, 1])
    
    with col1:
        user_message = st.text_input(
            "Message",
            placeholder="Ask for questions, request modifications, or specify focus areas...",
            key="bloom_user_input",
            label_visibility="collapsed"
        )
    
    with col2:
        send_button = st.button("📤 Send", use_container_width=True, type="primary", key="bloom_send")
    
    # Action buttons
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        generate_button = st.button(
            "🎯 Generate Question", 
            use_container_width=True,
            key="bloom_generate",
            disabled=not chat_topic or not st.session_state.selected_bloom_level
        )
    
    with col_b:
        if st.button("🗑️ Clear Chat", use_container_width=True, key="bloom_clear_chat"):
            st.session_state.bloom_chat_history = []
            st.rerun()
    
    with col_c:
        if st.button("🧹 Clear All", use_container_width=True, key="bloom_clear_all"):
            st.session_state.bloom_chat_history = []
            st.session_state.bloom_questions = []
            st.session_state.bloom_uploaded_file = None
            st.rerun()
    
    st.divider()
    
    # ========================================================================
    # HANDLE GENERATION
    # ========================================================================
    
    # Handle send button
    if send_button and user_message and chat_topic and st.session_state.selected_bloom_level:
        with st.spinner("🧠 Generating calibrated question..."):
            try:
                from datetime import datetime
                current_time = datetime.now().strftime("%H:%M")
                
                # Add user message to chat
                st.session_state.bloom_chat_history.append({
                    "role": "user",
                    "content": user_message,
                    "timestamp": current_time
                })
                
                # Parse topic focus
                topic_focus_list = [tf.strip() for tf in topic_focus.split(",")] if topic_focus else []
                topic_focus_str = ",".join(topic_focus_list) if topic_focus_list else ""
                
                # Get API client
                client = st.session_state.api_client
                
                # Check if we have an uploaded file
                if hasattr(st.session_state, 'bloom_uploaded_file') and st.session_state.bloom_uploaded_file:
                    # Use document-based generation
                    response = client.generate_customized_question_with_document(
                        topic=chat_topic,
                        bloom_level=st.session_state.selected_bloom_level,
                        file_bytes=st.session_state.bloom_uploaded_file["bytes"],
                        file_type=st.session_state.bloom_uploaded_file["type"],
                        question_type=question_type,
                        chat_context=user_message,
                        topic_focus=topic_focus_str,
                        additional_context=additional_context if additional_context else None,
                        require_bloom_justification=require_justification
                    )
                else:
                    # Use regular generation
                    response = client.generate_customized_question(
                        topic=chat_topic,
                        bloom_level=st.session_state.selected_bloom_level,
                        question_type=question_type,
                        chat_context=user_message,
                        topic_focus=topic_focus_str,
                        additional_context=additional_context if additional_context else None,
                        require_bloom_justification=require_justification
                    )
                
                # Process response
                if response and "data" in response and response["data"]:
                    question_data = response["data"][0]
                    
                    # Store question with all data (NEWEST FIRST - insert at beginning)
                    st.session_state.bloom_questions.insert(0, {
                        "topic": chat_topic,
                        "bloom_level": st.session_state.selected_bloom_level,
                        "all_levels": selected_levels.copy(),
                        "question_type": question_type,
                        "question": question_data.get("question_text", ""),
                        "options": question_data.get("options", []),
                        "answer": question_data.get("expected_answer", ""),
                        "explanation": question_data.get("explanation", ""),
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
                    # Interactive AI response with question preview
                    question_preview = question_data.get("question_text", "")[:150] + "..." if len(question_data.get("question_text", "")) > 150 else question_data.get("question_text", "")
                    
                    ai_response = f"""✅ **Question Generated Successfully!**

**📋 {st.session_state.selected_bloom_level} Level Question:**
{question_preview}

**📌 Type:** {question_type}

You can view the complete question with options and answer in the "Generated Questions" section below.

*What would you like to do next?*
- Ask for another question on the same topic
- Request a different Bloom's level
- Ask for clarification or modification
- Upload a document for more context"""
                else:
                    ai_response = "❌ Could not generate question. Please try again with different parameters."
                
                # Add AI response to chat
                st.session_state.bloom_chat_history.append({
                    "role": "assistant",
                    "content": ai_response,
                    "timestamp": datetime.now().strftime("%H:%M")
                })
                
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.session_state.bloom_chat_history.append({
                    "role": "assistant",
                    "content": f"❌ Error: {str(e)}",
                    "timestamp": datetime.now().strftime("%H:%M")
                })
    
    # Handle generate button
    if generate_button:
        with st.spinner(f"🎯 Generating {st.session_state.selected_bloom_level} level question..."):
            try:
                from datetime import datetime
                
                # Parse topic focus
                topic_focus_list = [tf.strip() for tf in topic_focus.split(",")] if topic_focus else []
                topic_focus_str = ",".join(topic_focus_list) if topic_focus_list else ""
                
                # Prepare chat context
                chat_message = f"Generate a {st.session_state.selected_bloom_level} level question about {chat_topic}"
                
                # Get API client
                client = st.session_state.api_client
                
                # Check if we have an uploaded file
                if hasattr(st.session_state, 'bloom_uploaded_file') and st.session_state.bloom_uploaded_file:
                    # Use document-based generation
                    response = client.generate_customized_question_with_document(
                        topic=chat_topic,
                        bloom_level=st.session_state.selected_bloom_level,
                        file_bytes=st.session_state.bloom_uploaded_file["bytes"],
                        file_type=st.session_state.bloom_uploaded_file["type"],
                        question_type=question_type,
                        chat_context=chat_message,
                        topic_focus=topic_focus_str,
                        additional_context=additional_context if additional_context else None,
                        require_bloom_justification=require_justification
                    )
                else:
                    # Use regular generation
                    response = client.generate_customized_question(
                        topic=chat_topic,
                        bloom_level=st.session_state.selected_bloom_level,
                        question_type=question_type,
                        chat_context=chat_message,
                        topic_focus=topic_focus_str,
                        additional_context=additional_context if additional_context else None,
                        require_bloom_justification=require_justification
                    )
                
                # Process response
                if response and "data" in response and response["data"]:
                    question_data = response["data"][0]
                    
                    # Store question with all data (NEWEST FIRST - insert at beginning)
                    st.session_state.bloom_questions.insert(0, {
                        "topic": chat_topic,
                        "bloom_level": st.session_state.selected_bloom_level,
                        "all_levels": selected_levels.copy(),
                        "question_type": question_type,
                        "question": question_data.get("question_text", ""),
                        "options": question_data.get("options", []),
                        "answer": question_data.get("expected_answer", ""),
                        "explanation": question_data.get("explanation", ""),
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
                    st.success(f"✅ {st.session_state.selected_bloom_level} level question generated successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to generate question")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    st.divider()
    
    # ========================================================================
    # GENERATED QUESTIONS DISPLAY - SHOWING NEWEST FIRST
    # ========================================================================
    
    if st.session_state.bloom_questions:
        st.markdown(f"### 📚 Generated Questions ({len(st.session_state.bloom_questions)})")
        
        # Show questions (already in reverse chronological order from insert(0))
        for i, q in enumerate(st.session_state.bloom_questions[:10], 1):  # Show first 10 (newest)
            with st.expander(f"**Q{i}** - {q['bloom_level']} - {q['topic'][:30]}...", expanded=False):
                # Question text
                st.markdown("**❓ Question:**")
                st.markdown(q['question'])
                
                # Options - with theme-aware styling
                if q.get('options') and len(q['options']) > 0:
                    st.markdown("**🎯 Options:**")
                    options_html = "<div class='options-box'>"
                    for opt in q['options']:
                        options_html += f"<div>{opt}</div>"
                    options_html += "</div>"
                    st.markdown(options_html, unsafe_allow_html=True)
                
                # Answer and explanation in columns
                col_q1, col_q2 = st.columns(2)
                
                with col_q1:
                    st.markdown("**✅ Answer:**")
                    st.markdown(f"<div class='answer-box'>{q['answer']}</div>", unsafe_allow_html=True)
                
                with col_q2:
                    st.markdown("**📝 Explanation:**")
                    st.markdown(f"<div class='explanation-box'>{q['explanation']}</div>", unsafe_allow_html=True)
                
                # Metadata
                st.caption(f"*Type: {q['question_type']} | Includes levels: {', '.join(q.get('all_levels', [q['bloom_level']]))}*")
                
                if st.button(f"🗑️ Remove", key=f"remove_q_{i}_{hash(q['timestamp'])}"):
                    st.session_state.bloom_questions.pop(i-1)
                    st.rerun()
        
        # Export section
        st.divider()
        st.markdown("### 📥 Export Options")
        
        col_exp1, col_exp2, col_exp3 = st.columns(3)
        
        with col_exp1:
            export_data = json.dumps(st.session_state.bloom_questions, indent=2, default=str)
            st.download_button(
                label="📄 Export as JSON",
                data=export_data,
                file_name=f"bloom_questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col_exp2:
            # Create CSV export
            csv_str = "Topic,Bloom Level,Question Type,Question,Options,Answer,Explanation,Timestamp\n"
            for q in st.session_state.bloom_questions:
                options_str = " | ".join(q.get('options', [])) if q.get('options') else ""
                # Escape quotes in fields
                topic = q["topic"].replace('"', '""')
                bloom = q["bloom_level"].replace('"', '""')
                q_type = q["question_type"].replace('"', '""')
                question = q["question"].replace('"', '""')
                answer = q["answer"].replace('"', '""')
                explanation = q["explanation"].replace('"', '""')
                timestamp = q["timestamp"].replace('"', '""')
                options_str = options_str.replace('"', '""')
                
                csv_str += f'"{topic}","{bloom}","{q_type}","{question}","{options_str}","{answer}","{explanation}","{timestamp}"\n'
            
            st.download_button(
                label="📊 Export as CSV",
                data=csv_str,
                file_name=f"bloom_questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col_exp3:
            if st.button("🧹 Clear All Questions", use_container_width=True):
                st.session_state.bloom_questions = []
                st.rerun()
    
    else:
        st.info("""
        ### 🎯 No questions generated yet
        
        1. **Enter a topic** above
        2. **Select a Bloom's level** (higher levels automatically include lower ones)
        3. **Upload a document** for context (optional)
        4. **Chat** with the AI or click 'Generate Question'
        
        The AI will generate questions calibrated to your selected cognitive level!
        """)

if __name__ == "__main__":
    pass