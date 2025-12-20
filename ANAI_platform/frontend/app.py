import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
import json
import re
from config import get_question_types, get_difficulty_levels
from api_client import get_api_client
from utils import setup_logging

logger = setup_logging(__name__)

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

tab1, tab2, tab3 = st.tabs([" Generate Questions", " Question Paper", " Assignment"])


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
            ["Machine Learning", "Deep Learning", "Natural Language Processing", "Computer Vision", 
             "Artificial Intelligence", "Reinforcement Learning", "Data Science", "Cryptography"],
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
    
    # Difficulty Distribution
    st.markdown("#### 🎯 Difficulty Distribution")
    col1, col2, col3 = st.columns(3)
    with col1:
        easy_count = st.number_input("🟢 Easy", 0, total_questions, total_questions // 3, key="paper_easy")
    with col2:
        medium_count = st.number_input("🟡 Medium", 0, total_questions, total_questions // 3, key="paper_medium")
    with col3:
        hard_count = st.number_input("🔴 Hard", 0, total_questions, total_questions - 2*(total_questions // 3), key="paper_hard")
    
    diff_total = easy_count + medium_count + hard_count
    if diff_total != total_questions:
        st.warning(f"⚠️ Difficulty total: {diff_total} (Need {total_questions})")
    else:
        st.success(f"✅ Difficulty: Easy({easy_count}) + Medium({medium_count}) + Hard({hard_count}) = {diff_total}")
    
    st.divider()
    
    # Question Type Distribution
    st.markdown("#### 📝 Question Type Distribution")
    
    # Type mapping for API
    type_key_mapping = {
        "Multiple Choice": "MCQ",
        "Short Answer": "ShortAnswer", 
        "Long Answer": "LongAnswer",
        "True/False": "TrueFalse",
        "Fill in the Blank": "FillBlank",
        "Numerical Problem": "Numerical",
        "Code Implementation": "CodeImplementation",
        "Diagram-Based": "DiagramBased"
    }
    
    col1, col2 = st.columns(2)
    type_distribution = {}
    
    with col1:
        type_distribution["MCQ"] = st.number_input("✅ Multiple Choice", 0, total_questions, min(5, total_questions), key="paper_mcq")
        type_distribution["ShortAnswer"] = st.number_input("📝 Short Answer", 0, total_questions, 3, key="paper_short")
        type_distribution["LongAnswer"] = st.number_input("📄 Long Answer", 0, total_questions, 2, key="paper_long")
        type_distribution["TrueFalse"] = st.number_input("❓ True/False", 0, total_questions, 2, key="paper_tf")
    
    with col2:
        type_distribution["FillBlank"] = st.number_input("✏️ Fill in Blank", 0, total_questions, 0, key="paper_fill")
        type_distribution["Numerical"] = st.number_input("🔢 Numerical", 0, total_questions, 2, key="paper_num")
        type_distribution["CodeImplementation"] = st.number_input("💻 Code", 0, total_questions, 1, key="paper_code_q")
        type_distribution["DiagramBased"] = st.number_input("📊 Diagram", 0, total_questions, 0, key="paper_diag")
    
    type_total = sum(type_distribution.values())
    if type_total != total_questions:
        st.warning(f"⚠️ Type total: {type_total} (Need {total_questions})")
    else:
        st.success(f"✅ Question types distributed: {type_total} questions")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        paper_context = st.text_area(
            "📋 Paper Context (Optional)",
            height=80,
            placeholder="Topics, concepts, or focus areas...",
            key="paper_context"
        )
    with col2:
        paper_instructions = st.text_area(
            "📜 Instructions",
            height=80,
            value="Answer all questions. Show all working where applicable.",
            key="paper_instructions"
        )
    
    st.divider()
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
    with col_btn2:
        if st.button("🚀 Generate Paper", type="primary", use_container_width=True, key="paper_generate"):
            if diff_total != total_questions:
                st.error("❌ Difficulty distribution must equal total questions")
            elif type_total != total_questions:
                st.error("❌ Question type distribution must equal total questions")
            else:
                try:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.info("📝 Generating question paper with LLM...")
                    progress_bar.progress(20)
                    
                    # Build distribution for API
                    distribution = {
                        "difficulty": {
                            "Easy": easy_count,
                            "Medium": medium_count,
                            "Hard": hard_count
                        },
                        "types": type_distribution
                    }
                    
                    client = st.session_state.api_client
                    
                    status_text.info("🔄 Calling Paper Generation API...")
                    progress_bar.progress(40)
                    
                    response = client.generate_paper(
                        name=paper_name,
                        course_code=paper_code,
                        semester=paper_semester,
                        subject=paper_subject,
                        total_questions=total_questions,
                        total_marks=total_marks,
                        duration_minutes=paper_duration,
                        distribution=distribution
                    )
                    
                    progress_bar.progress(80)
                    
                    paper_data = response.get('data', {})
                    questions = paper_data.get('questions', [])
                    
                    progress_bar.progress(100)
                    status_text.success(f"✅ Paper generated with {len(questions)} questions!")
                    
                    st.session_state.generated_paper = paper_data
                    st.balloons()
                    
                    st.divider()
                    
                    # Display paper header
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                padding: 2rem; border-radius: 15px; margin: 1rem 0; text-align: center;">
                        <h1 style="color: white; margin: 0;">📄 {paper_name}</h1>
                        <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0;">
                            {paper_code} | Semester {paper_semester} | {paper_subject}
                        </p>
                        <p style="color: rgba(255,255,255,0.8); margin: 0;">
                            ⏱️ {paper_duration} min | 📊 {total_marks} marks | ❓ {len(questions)} questions
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display instructions
                    if paper_instructions:
                        st.info(f"**📜 Instructions:** {paper_instructions}")
                    
                    st.divider()
                    
                    # Display questions by type
                    for idx, question in enumerate(questions):
                        display_question(question, idx)
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())


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
                
                assignment_data = response.get('data', {})
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
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                import traceback
                st.code(traceback.format_exc())


if __name__ == "__main__":
    pass
