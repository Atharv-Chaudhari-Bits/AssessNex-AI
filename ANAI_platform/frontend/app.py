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
    
    # Fix escaped backslashes in LaTeX (e.g., \\text -> \text)
    # This can happen during JSON serialization
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

tab1, tab2, tab3, tab4 = st.tabs([" Generate Questions", " Question Paper", " Assignment", " Customised Q&A"])


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
            -  Ensure backend is running at http://localhost:8000
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

    question_type_config = []

    def add_q(type_name, count, marks_each):
        if count > 0:
            question_type_config.append({
                "type": type_name,
                "count": count,
                "marks_each": marks_each,
                "difficulty": "medium",
                "bloom_levels": ["Remember", "Understand", "Apply"]
            })

    marks_each = max(1, total_marks // max(total_questions, 1))

    add_q("Multiple Choice", mcq, marks_each)
    add_q("Short Answer", short_ans, marks_each)
    add_q("Long Answer", long_ans, marks_each)
    add_q("True/False", tf, marks_each)
    add_q("Fill in the Blank", fill, marks_each)
    add_q("Numerical Problem", numerical, marks_each)
    add_q("Code Implementation", code, marks_each)
    add_q("Diagram-Based", diagram, marks_each)

    st.divider()

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
        if diff_total != total_questions or type_total != total_questions:
            st.error("❌ Fix distributions before generating paper")
        else:
            try:
                client = st.session_state.api_client

                payload = {
                    "exam_name": paper_name,
                    "subject": paper_subject,
                    "topic": paper_topic or paper_name,
                    "total_marks": total_marks,
                    "duration_minutes": paper_duration,
                    "question_type_config": question_type_config,
                    "bloom_distribution": bloom_distribution,
                    "instructions": paper_instructions
                }

                response = client.generate_paper_with_payload(payload)

                paper_data = response.get("paper", response)
                st.session_state.generated_paper = paper_data

                st.success("✅ Paper generated successfully!")
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
        
        /* Fix for streamlit default colors */
        .st-emotion-cache-1v0mbdj {
            color: black !important;
        }
        
        p, div, span {
            color: black !important;
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
                        "type": question.get("type", question_type),
                        "options": options,
                        "answer": answer,
                        "marks": question.get("marks", section.get("marks_per_question", 2)),
                        "difficulty": question.get("difficulty", "medium"),
                        "bloom_level": question.get("bloom_level", "Apply"),
                        "explanation": question.get("explanation", ""),
                        "topic": question.get("topic", paper.get("topic", "")),
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
                        # Display question
                        st.markdown(f'<div class="question-text">Q{q["question_number"]}. {q["question"]}</div>', 
                                unsafe_allow_html=True)
                        
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
            # PDF Export (simplified)
            if st.button("🖨️ Generate PDF Preview", use_container_width=True):
                st.info("PDF generation would require additional setup.")
                st.markdown("""
                **For PDF export, you would need:**
                1. Install `reportlab` or `fpdf`
                2. Create a PDF generation function
                3. Format content with proper styling
                
                Currently exporting as text file.
                """)
        
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
# TAB 3: ASSIGNMENT GENERATOR
# ============================================================================

with tab3:
    display_header("📚 Generate Assignment", "Create practice assignments with tracking")
    
    st.markdown("### 📋 Assignment Configuration")
    
    col1, col2 = st.columns(2)
    with col1:
        assign_name = st.text_input("📝 Assignment Name", value="ML Assignment 1", key="assign_name")
        assign_code = st.text_input("🔢 Course Code", value="CS-501", key="assign_code")
    with col2:
        assign_subject = st.selectbox(
            "📚 Subject",
            ["Machine Learning", "Deep Learning", "Natural Language Processing", "Computer Vision", 
             "Artificial Intelligence", "Reinforcement Learning", "Data Science", "Cryptography"],
            key="assign_subject"
        )
        assign_level = st.selectbox("🎯 Difficulty", get_difficulty_levels(), key="assign_level")
    
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        assignment_type = st.selectbox(
            "📂 Assignment Type",
            ["Coding Problem", "Essay", "Case Study", "Problem Solving", "Research", "Project", "Theoretical", "Practical"],
            key="assign_type"
        )
    with col2:
        assign_num = st.slider("📝 Number of Tasks", 1, 10, 3, key="assign_num")
    with col3:
        total_points = st.slider("📊 Total Points", 10, 200, 100, key="assign_points")
    
    col1, col2 = st.columns(2)
    with col1:
        due_days = st.slider("📅 Due in (days)", 1, 30, 7, key="assign_due")
    with col2:
        submission_format = st.selectbox(
            "📤 Submission Format",
            ["PDF", "Jupyter Notebook", "Code Repository", "Google Doc", "Any Format"],
            key="assign_format"
        )
    
    # Topic input
    assign_topic = st.text_input(
        "📌 Specific Topic (Optional)",
        placeholder="Leave blank to use subject as topic",
        key="assign_topic"
    )
    
    assign_description = st.text_area(
        "📋 Assignment Description & Requirements",
        height=120,
        placeholder="Describe the assignment goals, specific topics to cover, requirements, and any special instructions...",
        value=f"Create a comprehensive {assignment_type.lower()} on {assign_subject}. Focus on practical applications and real-world scenarios.",
        key="assign_description"
    )
    
    # Code generation options (for coding assignments)
    if assignment_type in ["Coding Problem", "Project", "Practical"]:
        st.markdown("#### ⚙️ Code Generation Options")
        col1, col2, col3 = st.columns(3)
        with col1:
            include_starter = st.checkbox("📄 Include Starter Code", value=True, key="assign_starter")
        with col2:
            include_solutions = st.checkbox("🔐 Include Solutions", value=True, key="assign_solutions")
        with col3:
            include_tests = st.checkbox("🧪 Include Test Cases", value=True, key="assign_tests")
    else:
        include_starter = False
        include_solutions = True
        include_tests = False
    
    st.divider()
    
    # Document-based generation option
    st.markdown("### 📄 Document-Based Generation (Optional)")
    
    use_assign_document = st.checkbox("📤 Use document content to generate assignment", value=False, key="assign_use_doc")
    assign_document_text = None
    
    if use_assign_document:
        assign_uploaded_file = st.file_uploader(
            "📁 Upload document (PDF, DOCX, or TXT)",
            type=["pdf", "docx", "txt"],
            key="assign_doc_upload"
        )
        
        if assign_uploaded_file:
            try:
                assign_status_placeholder = st.empty()
                assign_status_placeholder.info("📖 Extracting document content...")
                assign_document_text = extract_document_text(assign_uploaded_file)
                assign_status_placeholder.success(f"✅ Extracted {len(assign_document_text)} characters from document")
                
                with st.expander("👁️ Preview extracted text"):
                    st.text_area("", value=assign_document_text[:500] + "...", height=150, disabled=True)
            except Exception as e:
                st.error(f"❌ Error processing document: {str(e)}")
                assign_document_text = None
    
    st.divider()
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
    with col_btn2:
        if st.button("🚀 Generate Assignment", type="primary", use_container_width=True, key="assign_generate"):
            try:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.info("📝 Generating assignment with LangGraph workflow...")
                progress_bar.progress(20)
                
                client = st.session_state.api_client
                
                status_text.info("🔄 Creating diverse tasks and code files...")
                progress_bar.progress(40)
                
                # If document is provided, use document-based generation
                if assign_document_text:
                    response = client.generate_assignment_from_document(
                        document_text=assign_document_text,
                        name=assign_name,
                        course_code=assign_code,
                        subject=assign_subject,
                        assignment_type=assignment_type,
                        difficulty=assign_level,
                        max_marks=total_points,
                        duration_days=due_days,
                        num_tasks=assign_num,
                        description=assign_description
                    )
                else:
                    response = client.generate_assignment(
                        name=assign_name,
                        course_code=assign_code,
                        subject=assign_subject,
                        topic=assign_topic if assign_topic else assign_subject,
                        assignment_type=assignment_type,
                        difficulty=assign_level,
                        max_marks=total_points,
                        duration_days=due_days,
                        num_tasks=assign_num,
                        description=assign_description,
                        include_solutions=include_solutions,
                        include_starter_code=include_starter,
                        include_test_cases=include_tests
                    )

                
                progress_bar.progress(80)
                
                # Extract assignment data from response
                assignment_data = response
                tasks = assignment_data.get('tasks', [])
                
                progress_bar.progress(100)
                status_text.success(f"✅ Assignment generated with {len(tasks)} tasks!")
                
                st.session_state.generated_assignment = assignment_data
                st.balloons()
                
                st.divider()
                
                # Display assignment header
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); 
                            padding: 2rem; border-radius: 15px; margin: 1rem 0; text-align: center;">
                    <h1 style="color: white; margin: 0;">📚 {assign_name}</h1>
                    <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0;">
                        {assign_code} | {assign_subject} | {assignment_type}
                    </p>
                    <p style="color: rgba(255,255,255,0.8); margin: 0;">
                        📅 Due: {due_days} days | 📊 {total_points} points | 📝 {len(tasks)} tasks
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Display assignment description
                st.info(f"**📋 Description:** {assign_description}")
                
                # Display submission guidelines
                guidelines = assignment_data.get('submission_guidelines', [])
                if guidelines:
                    with st.expander("📤 Submission Guidelines", expanded=True):
                        for guideline in guidelines:
                            st.markdown(f"• {guideline}")
                
                # Display evaluation criteria
                criteria = assignment_data.get('evaluation_criteria', [])
                if criteria:
                    with st.expander("📊 Evaluation Criteria", expanded=True):
                        for c in criteria:
                            weight = int(c.get('weight', 0) * 100)
                            criterion = c.get('criterion', '')
                            desc = c.get('description', '')
                            st.markdown(f"• **{criterion}** ({weight}%): {desc}")
                
                # Display learning objectives
                objectives = assignment_data.get('learning_objectives', [])
                if objectives:
                    with st.expander("🎯 Learning Objectives", expanded=True):
                        for obj in objectives:
                            st.markdown(f"✅ {obj}")
                
                st.divider()
                st.markdown("### 📝 Assignment Tasks")
                
                # Display tasks
                for idx, task in enumerate(tasks):
                    task_id = task.get('task_id', f'task_{idx+1}')
                    task_title = task.get('title', f'Task {idx+1}')
                    task_desc = task.get('description', '')
                    task_points = task.get('points', task.get('marks', 0))
                    task_requirements = task.get('requirements', [])
                    task_hints = task.get('hints', [])
                    task_expected = task.get('expected_output', task.get('expected_deliverable', ''))
                    task_starter = task.get('starter_code', '')
                    task_solution = task.get('solution_code', '')
                    
                    with st.expander(f"📌 {task_title} ({task_points} pts)", expanded=True):
                        st.markdown(f"**📝 Description:**")
                        st.markdown(task_desc)
                        
                        if task_requirements:
                            st.markdown(f"**📋 Requirements:**")
                            for req in task_requirements:
                                st.markdown(f"• {req}")
                        
                        if task_expected:
                            st.markdown(f"**✅ Expected Output:**")
                            st.info(task_expected)
                        
                        if task_hints:
                            st.markdown(f"**💡 Hints:**")
                            if isinstance(task_hints, list):
                                for hint in task_hints:
                                    st.success(f"• {hint}")
                            else:
                                st.success(task_hints)
                        
                        # Show starter code if available
                        if task_starter:
                            with st.expander("📄 Starter Code", expanded=False):
                                st.code(task_starter, language="python")
                        
                        # Show solution (hidden by default)
                        if task_solution:
                            with st.expander("🔐 Solution (Instructor Only)", expanded=False):
                                st.code(task_solution, language="python")
                        
                        st.markdown(f"📊 **Points:** {task_points}")
                
                # Display generated files
                generated_files = assignment_data.get('generated_files', [])
                if generated_files:
                    st.divider()
                    st.markdown("### 📁 Generated Files")
                    
                    file_tabs = st.tabs([f"📄 {f.get('filename', 'file')}" for f in generated_files])
                    for i, (file_tab, file_info) in enumerate(zip(file_tabs, generated_files)):
                        with file_tab:
                            filename = file_info.get('filename', 'file')
                            content = file_info.get('content', '')
                            file_type = file_info.get('file_type', '')
                            language = file_info.get('language', 'text')
                            description = file_info.get('description', '')
                            
                            st.markdown(f"**{description}**")
                            st.markdown(f"*Type: {file_type}*")
                            
                            # Display code with syntax highlighting
                            if language in ['python', 'javascript', 'java', 'cpp']:
                                st.code(content, language=language)
                            elif language == 'markdown':
                                st.markdown(content)
                            else:
                                st.code(content)
                            
                            # Download button for each file
                            st.download_button(
                                label=f"📥 Download {filename}",
                                data=content,
                                file_name=filename,
                                mime="text/plain",
                                key=f"download_file_{i}"
                            )
                
                st.divider()
                
                # Export buttons
                col_exp1, col_exp2 = st.columns(2)
                
                with col_exp1:
                    json_str = json.dumps(assignment_data, indent=2)
                    st.download_button(
                        label="📥 Download (JSON)",
                        data=json_str,
                        file_name=f"assignment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        use_container_width=True
                    )
                
                with col_exp2:
                    # Create text export
                    text_export = f"""ASSIGNMENT: {assign_name}
Course Code: {assign_code}
Subject: {assign_subject}
Type: {assignment_type}
Difficulty: {assign_level}
Total Points: {total_points}
Due: {due_days} days
Submission Format: {submission_format}

DESCRIPTION:
{assign_description}

TASKS:
"""
                    for idx, task in enumerate(tasks, 1):
                        text_export += f"\n{idx}. {task.get('title', f'Task {idx}')}\n"
                        text_export += f"   Points: {task.get('marks', 0)}\n"
                        text_export += f"   Description: {task.get('description', '')}\n"
                        if task.get('expected_deliverable'):
                            text_export += f"   Deliverable: {task.get('expected_deliverable', '')}\n"
                    
                    st.download_button(
                        label="📄 Download (TXT)",
                        data=text_export,
                        file_name=f"assignment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                
                # Chat-based feedback section
                st.divider()
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                import traceback
                st.code(traceback.format_exc())


# ============================================================================
# TAB 4: CUSTOMISED QUESTION GENERATION WITH CHAT
# ============================================================================

with tab4:
    display_header("💬 Customised Q&A Generation", "Chat-based question generation with Bloom's Taxonomy")
    
    st.markdown("### 🎯 Setup")
    
    # Configuration columns
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        chat_topic = st.text_input(
            " Chat Topic",
            placeholder="e.g., Machine Learning Algorithms, Database Design, Web Security...",
            key="chat_topic"
        )
    
    with col2:
        chat_difficulty = st.selectbox(
            " Difficulty Level",
            get_difficulty_levels(),
            key="chat_difficulty"
        )
    
    # Bloom's Taxonomy levels selection
    st.markdown("**📚 Bloom's Taxonomy Levels**")
    bloom_levels = ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]
    
    col_bloom1, col_bloom2, col_bloom3 = st.columns(3)
    selected_blooms = []
    
    with col_bloom1:
        if st.checkbox("Remember (Level 1)", value=True, key="bloom_remember"):
            selected_blooms.append("Remember")
        if st.checkbox("Understand (Level 2)", value=True, key="bloom_understand"):
            selected_blooms.append("Understand")
    
    with col_bloom2:
        if st.checkbox("Apply (Level 3)", value=True, key="bloom_apply"):
            selected_blooms.append("Apply")
        if st.checkbox("Analyze (Level 4)", value=False, key="bloom_analyze"):
            selected_blooms.append("Analyze")
    
    with col_bloom3:
        if st.checkbox("Evaluate (Level 5)", value=False, key="bloom_evaluate"):
            selected_blooms.append("Evaluate")
        if st.checkbox("Create (Level 6)", value=False, key="bloom_create"):
            selected_blooms.append("Create")
    
    st.divider()
    
    # Chat history initialization
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "custom_questions" not in st.session_state:
        st.session_state.custom_questions = []
    
    # Chat interface
    st.markdown("### 💭 Chat Interaction")
    
    # Display chat history
    chat_container = st.container(height=400, border=True)
    with chat_container:
        for i, msg in enumerate(st.session_state.chat_history):
            if msg["role"] == "user":
                st.write(f"**You:** {msg['content']}")
            else:
                st.write(f"**AI:** {msg['content']}")
    
    st.markdown("---")
    
    # Chat input and controls
    chat_col1, chat_col2 = st.columns([5, 1], gap="small")
    
    with chat_col1:
        user_input = st.text_input(
            " Your message",
            placeholder="Ask for questions, modify topics, request specific focus areas...",
            key="chat_input"
        )
    
    with chat_col2:
        if st.button("📤 Send", use_container_width=True, key="send_msg"):
            if user_input and chat_topic:
                with st.spinner("Processing your request..."):
                    try:
                        # Add user message to history
                        st.session_state.chat_history.append({
                            "role": "user",
                            "content": user_input
                        })
                        
                        # Call API for chat-based question generation
                        client = st.session_state.api_client
                        response = client.generate_questions(
                            subject=chat_topic,
                            question_type="Multiple Choice",
                            difficulty=chat_difficulty,
                            count=1,
                            additional_context=user_input
                        )
                        
                        # Extract questions from response.data
                        questions_list = response.get("data", []) if response else []
                        if response and questions_list:
                            question = questions_list[0] if questions_list else None
                            if question:
                                # Extract question text from question object
                                question_text = question.get('question_text') or question.get('question') or str(question)
                                st.session_state.custom_questions.append({
                                    "question": question_text,
                                    "bloom_level": user_input,
                                    "timestamp": datetime.now().isoformat(),
                                    "full_data": question
                                })
                                
                                ai_response = f"Generated question with {chat_difficulty} difficulty for topic '{chat_topic}': {question_text}"
                            else:
                                ai_response = "Could not generate question. Please try again."
                        else:
                            ai_response = "Error in generation. Please try again."
                        
                        # Add AI response to history
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": ai_response
                        })
                        
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": f"Error occurred: {str(e)}"
                        })
            else:
                if not chat_topic:
                    st.warning("Please enter a chat topic first")
    
    st.divider()
    
    # Display generated questions
    if st.session_state.custom_questions:
        st.markdown("### ✅ Generated Questions")
        
        for i, q_data in enumerate(st.session_state.custom_questions, 1):
            with st.expander(f"Question {i} - {q_data['bloom_level']}", expanded=False):
                st.write(q_data["question"])
                
                col_export = st.columns([1, 1, 1])
                with col_export[0]:
                    if st.button(f"📋 Copy", key=f"copy_q_{i}"):
                        st.toast("Copied to clipboard!")
                
                with col_export[1]:
                    if st.button(f"❌ Remove", key=f"remove_q_{i}"):
                        st.session_state.custom_questions.pop(i-1)
                        st.rerun()
        
        # Export options
        st.markdown("### 📥 Export Generated Questions")
        
        export_col1, export_col2 = st.columns(2)
        
        with export_col1:
            if st.button("📄 Export as JSON", use_container_width=True):
                json_data = json.dumps(st.session_state.custom_questions, indent=2)
                st.download_button(
                    label="Download JSON",
                    data=json_data,
                    file_name=f"customized_questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with export_col2:
            if st.button("🧹 Clear All", use_container_width=True):
                st.session_state.custom_questions = []
                st.session_state.chat_history = []
                st.rerun()
    else:
        st.info("💡 Start chatting to generate customised questions! Select Bloom's taxonomy levels above and ask questions or request specific topics.")


if __name__ == "__main__":
    pass
