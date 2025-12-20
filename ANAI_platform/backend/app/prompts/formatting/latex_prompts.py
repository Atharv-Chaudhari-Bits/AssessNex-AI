"""
LaTeX and math expression prompts - Comprehensive templates for mathematical formatting.

This module provides detailed prompts for generating:
- Inline LaTeX expressions
- Block/display LaTeX
- Step-by-step math solutions
- Complex equation arrays and matrices

Each prompt includes:
- Syntax reference
- Common commands
- Best practices
- Examples
"""

# =============================================================================
# LATEX SYSTEM PROMPT
# =============================================================================

LATEX_SYSTEM_PROMPT = """You are an expert LaTeX and mathematical typesetting specialist. Your role is to create properly formatted mathematical expressions that render correctly in Markdown/KaTeX/MathJax environments.

CORE PRINCIPLES:
================

1. SYNTAX PRECISION
   - Use correct delimiter pairs ($...$ for inline, $$...$$ for block)
   - Escape special characters properly
   - Use correct command syntax (\\frac{}{}, not \\frac)
   - Balance all brackets and braces

2. READABILITY
   - Use appropriate sizing for fractions and expressions
   - Add spacing where needed (\\, \\: \\; \\quad)
   - Break long expressions into multiple lines
   - Use alignment for multi-step solutions

3. MATHEMATICAL ACCURACY
   - Use correct mathematical notation
   - Proper symbols for operations
   - Correct formatting for sets, functions, operators
   - Standard notation for derivatives, integrals, etc.

4. RENDERING COMPATIBILITY
   - Stick to standard LaTeX commands
   - Avoid packages that may not be supported
   - Test expressions are self-contained
   - Use KaTeX-compatible commands

COMMON LATEX COMMANDS:
======================

Basic:
\\frac{a}{b}       → Fraction
\\sqrt{x}          → Square root
\\sqrt[n]{x}       → nth root
x^{n}              → Superscript/exponent
x_{i}              → Subscript
\\sum_{i=0}^{n}    → Summation
\\prod_{i=0}^{n}   → Product
\\int_{a}^{b}      → Integral
\\lim_{x \\to a}   → Limit

Greek Letters:
\\alpha \\beta \\gamma \\delta \\epsilon
\\theta \\lambda \\mu \\pi \\sigma
\\phi \\omega \\Gamma \\Delta \\Omega

Operators:
\\times \\div \\pm \\mp \\cdot
\\leq \\geq \\neq \\approx \\equiv
\\in \\notin \\subset \\subseteq
\\cup \\cap \\setminus

Relations:
\\rightarrow \\leftarrow \\Rightarrow \\Leftarrow
\\iff \\implies \\therefore \\because

Formatting:
\\text{text}       → Text in math mode
\\mathbf{x}        → Bold
\\mathit{x}        → Italic
\\mathrm{d}        → Roman (upright)
\\mathcal{L}       → Calligraphic
\\overline{x}      → Overline
\\hat{x}           → Hat accent
\\vec{x}           → Vector arrow

Delimiters:
\\left( \\right)   → Auto-sizing parentheses
\\left[ \\right]   → Auto-sizing brackets
\\left\\{ \\right\\} → Auto-sizing braces
\\left| \\right|   → Auto-sizing vertical bars

OUTPUT FORMAT:
==============
Inline: Use $expression$ for inline math
Block: Use $$expression$$ for display math

Return JSON when requested:
{
    "formatted_content": "the latex expression",
    "type": "inline|block|equation",
    "summary": "brief description"
}"""


# =============================================================================
# INLINE LATEX PROMPT
# =============================================================================

LATEX_INLINE_PROMPT = """Format the following as inline LaTeX expression(s).

INLINE LATEX GUIDELINES:
=========================

1. USE CASES:
   - Variables in text: "where $x$ is the input"
   - Simple equations: "given $y = mx + b$"
   - Single values: "probability $p = 0.5$"
   - Symbols: "the set $\\mathbb{R}$"

2. BEST PRACTICES:
   - Keep expressions short and simple
   - Don't use display-style commands in inline
   - Ensure proper spacing around $ delimiters
   - Use \\text{} for words within expressions

3. AVOID IN INLINE:
   - Large fractions (use \\tfrac or display)
   - Multi-line expressions
   - Large summations or integrals
   - Matrices or arrays

4. EXAMPLES:

   Simple variable: $x$
   
   With subscript: $x_i$ or $a_{n+1}$
   
   Simple equation: $E = mc^2$
   
   With fraction: $\\frac{1}{2}$ or $\\tfrac{1}{2}$
   
   Function: $f(x) = x^2 + 2x + 1$
   
   Set notation: $x \\in \\mathbb{R}$
   
   Probability: $P(A|B) = \\frac{P(B|A)P(A)}{P(B)}$
   
   With text: $\\text{Cost} = \\sum_{i=1}^{n} p_i \\cdot q_i$

INPUT TO FORMAT:
{content}

CONTEXT:
{context}

Return the properly formatted inline LaTeX expression(s)."""


# =============================================================================
# BLOCK LATEX PROMPT
# =============================================================================

LATEX_BLOCK_PROMPT = """Format the following as block/display LaTeX expression(s).

BLOCK LATEX GUIDELINES:
========================

1. USE CASES:
   - Important equations to highlight
   - Complex expressions needing space
   - Multi-step derivations
   - Equations to reference

2. FORMATTING:
   - Use $$ delimiters on separate lines
   - Center the expression
   - Use full-size commands (\\frac not \\tfrac)
   - Add appropriate line breaks

3. MULTI-LINE EQUATIONS:
   Use aligned environment:
   $$
   \\begin{aligned}
   f(x) &= x^2 + 2x + 1 \\\\
        &= (x + 1)^2
   \\end{aligned}
   $$

4. EQUATION NUMBERING (if needed):
   \\begin{equation}
   E = mc^2
   \\end{equation}

5. EXAMPLES:

   Simple display:
   $$
   f(x) = \\int_{0}^{\\infty} e^{-x^2} dx
   $$

   Aligned equations:
   $$
   \\begin{aligned}
   \\nabla \\cdot \\mathbf{E} &= \\frac{\\rho}{\\epsilon_0} \\\\
   \\nabla \\cdot \\mathbf{B} &= 0 \\\\
   \\nabla \\times \\mathbf{E} &= -\\frac{\\partial \\mathbf{B}}{\\partial t} \\\\
   \\nabla \\times \\mathbf{B} &= \\mu_0 \\mathbf{J} + \\mu_0 \\epsilon_0 \\frac{\\partial \\mathbf{E}}{\\partial t}
   \\end{aligned}
   $$

   System of equations:
   $$
   \\begin{cases}
   x + y = 10 \\\\
   2x - y = 5
   \\end{cases}
   $$

INPUT TO FORMAT:
{content}

REQUIREMENTS:
- Use alignment: {use_alignment}
- Multi-line: {multi_line}

Return the properly formatted block LaTeX expression."""


# =============================================================================
# MATH EXPRESSION PROMPT
# =============================================================================

LATEX_MATH_PROMPT = """Create a step-by-step mathematical solution.

STEP-BY-STEP MATH GUIDELINES:
==============================

1. STRUCTURE:
   - State the problem clearly
   - Show each step of the solution
   - Explain reasoning between steps
   - Provide final answer clearly

2. FORMATTING:
   - Use block equations for main steps
   - Use inline math for explanations
   - Number or label steps
   - Align related expressions

3. EXPLANATION STYLE:
   - Brief text between equations
   - Highlight key transformations
   - Note applicable rules/theorems
   - Show intermediate results

4. TEMPLATE:

   **Problem:** [Statement]
   
   **Solution:**
   
   **Step 1:** [Description]
   $$
   [First expression]
   $$
   
   **Step 2:** [Description]
   $$
   [Transformed expression]
   $$
   
   **Step 3:** [Description]
   $$
   [Further simplification]
   $$
   
   **Answer:** $[final result]$

5. EXAMPLE:

   **Problem:** Solve for $x$: $2x^2 + 5x - 3 = 0$
   
   **Solution:**
   
   **Step 1:** Apply the quadratic formula $x = \\frac{-b \\pm \\sqrt{b^2-4ac}}{2a}$
   
   Where $a = 2$, $b = 5$, $c = -3$
   
   **Step 2:** Calculate the discriminant
   $$
   b^2 - 4ac = 5^2 - 4(2)(-3) = 25 + 24 = 49
   $$
   
   **Step 3:** Substitute into the formula
   $$
   x = \\frac{-5 \\pm \\sqrt{49}}{2(2)} = \\frac{-5 \\pm 7}{4}
   $$
   
   **Step 4:** Find both solutions
   $$
   x_1 = \\frac{-5 + 7}{4} = \\frac{2}{4} = \\frac{1}{2}
   $$
   $$
   x_2 = \\frac{-5 - 7}{4} = \\frac{-12}{4} = -3
   $$
   
   **Answer:** $x = \\frac{1}{2}$ or $x = -3$

INPUT PROBLEM:
{content}

REQUIREMENTS:
- Detail level: {detail_level}
- Include explanations: {include_explanations}
- Show verification: {show_verification}

Return the step-by-step solution with proper LaTeX formatting."""


# =============================================================================
# EQUATION ARRAY PROMPT
# =============================================================================

LATEX_EQUATION_PROMPT = """Create a LaTeX equation array, matrix, or complex expression.

COMPLEX MATH STRUCTURES:
=========================

1. MATRICES:

   Basic matrix:
   $$
   \\begin{pmatrix}
   a & b \\\\
   c & d
   \\end{pmatrix}
   $$

   Matrix types:
   - pmatrix: (parentheses)
   - bmatrix: [brackets]
   - Bmatrix: {braces}
   - vmatrix: |vertical bars| (determinant)
   - Vmatrix: ||double vertical||

   Large matrix:
   $$
   A = \\begin{bmatrix}
   a_{11} & a_{12} & \\cdots & a_{1n} \\\\
   a_{21} & a_{22} & \\cdots & a_{2n} \\\\
   \\vdots & \\vdots & \\ddots & \\vdots \\\\
   a_{m1} & a_{m2} & \\cdots & a_{mn}
   \\end{bmatrix}
   $$

2. SYSTEMS OF EQUATIONS:

   Using cases:
   $$
   \\begin{cases}
   x + y + z = 6 \\\\
   2x - y + z = 3 \\\\
   x + 2y - z = 2
   \\end{cases}
   $$

   Using aligned:
   $$
   \\left\\{\\begin{aligned}
   x + y + z &= 6 \\\\
   2x - y + z &= 3 \\\\
   x + 2y - z &= 2
   \\end{aligned}\\right.
   $$

3. PIECEWISE FUNCTIONS:

   $$
   f(x) = \\begin{cases}
   x^2 & \\text{if } x \\geq 0 \\\\
   -x^2 & \\text{if } x < 0
   \\end{cases}
   $$

4. ARRAYS WITH ALIGNMENT:

   $$
   \\begin{array}{lcr}
   \\text{Left} & \\text{Center} & \\text{Right} \\\\
   l & c & r \\\\
   \\text{long} & \\text{item} & \\text{here}
   \\end{array}
   $$

5. AUGMENTED MATRIX:

   $$
   \\left[\\begin{array}{ccc|c}
   1 & 2 & 3 & 4 \\\\
   5 & 6 & 7 & 8 \\\\
   9 & 10 & 11 & 12
   \\end{array}\\right]
   $$

6. DETERMINANTS:

   $$
   \\det(A) = \\begin{vmatrix}
   a & b \\\\
   c & d
   \\end{vmatrix} = ad - bc
   $$

7. SUMMATION AND PRODUCTS:

   $$
   \\sum_{i=1}^{n} \\sum_{j=1}^{m} a_{ij} = \\prod_{k=1}^{n} b_k
   $$

8. INTEGRALS:

   Multiple:
   $$
   \\iint_D f(x,y) \\, dA = \\iiint_V g(x,y,z) \\, dV
   $$

   With limits:
   $$
   \\int_{0}^{\\infty} \\int_{0}^{\\infty} e^{-(x^2+y^2)} \\, dx \\, dy = \\frac{\\pi}{4}
   $$

INPUT TO FORMAT:
{content}

STRUCTURE TYPE: {structure_type}

REQUIREMENTS:
- Matrix style: {matrix_style}
- Include labels: {include_labels}
- Show steps: {show_steps}

Return the properly formatted LaTeX structure."""


# =============================================================================
# LATEX VALIDATION PROMPT
# =============================================================================

LATEX_VALIDATION_PROMPT = """Validate the following LaTeX expression for correctness.

VALIDATION CHECKLIST:
=====================

1. DELIMITER BALANCE:
   □ $ pairs for inline math
   □ $$ pairs for block math
   □ \\begin{} and \\end{} pairs
   □ Brackets: () [] {{}} matched
   □ \\left and \\right pairs

2. COMMAND SYNTAX:
   □ Correct command names (\\frac not \\frak)
   □ Required arguments present
   □ Optional arguments in correct position
   □ No typos in command names

3. STRUCTURE VALIDITY:
   □ Environments properly nested
   □ Matrix rows have consistent columns
   □ Alignment characters (&) balanced
   □ Line breaks (\\\\) in appropriate places

4. RENDERING CHECK:
   □ Expression will render correctly
   □ No ambiguous syntax
   □ Standard commands used
   □ Compatible with KaTeX/MathJax

COMMON ERRORS:
==============
- Missing closing brace: \\frac{1{2} → \\frac{1}{2}
- Wrong command: \\frak → \\frac
- Unescaped special chars: _ outside math → \\_
- Missing argument: \\sqrt → \\sqrt{x}
- Unbalanced delimiters: \\left( without \\right)

LATEX TO VALIDATE:
{content}

Return JSON with:
{{
    "is_valid": true/false,
    "expression_type": "inline|block|equation|matrix",
    "errors": ["error1", "error2"],
    "warnings": ["warning1"],
    "suggestions": ["suggestion1"],
    "corrected_content": "fixed LaTeX if needed"
}}"""
