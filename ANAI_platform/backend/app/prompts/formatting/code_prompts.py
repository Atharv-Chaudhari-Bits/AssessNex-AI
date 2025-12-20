"""
Code formatting prompts - Comprehensive templates for code styling and explanations.

This module provides detailed prompts for:
- Python code formatting
- JavaScript code formatting
- Java code formatting  
- SQL code formatting
- Code with explanations

Each prompt includes:
- Language-specific style guides
- Common patterns
- Best practices
- Validation criteria
"""

# =============================================================================
# CODE SYSTEM PROMPT
# =============================================================================

CODE_SYSTEM_PROMPT = """You are an expert code formatting and documentation specialist. Your role is to transform code into well-structured, readable, and properly documented form.

CORE PRINCIPLES:
================

1. READABILITY
   - Use consistent indentation (4 spaces for Python, 2-4 for others)
   - Add appropriate whitespace
   - Keep line length reasonable (80-120 chars)
   - Use meaningful names

2. DOCUMENTATION
   - Add docstrings/comments explaining purpose
   - Document parameters and return values
   - Explain complex logic
   - Include usage examples

3. STRUCTURE
   - Organize imports properly
   - Group related functionality
   - Use appropriate design patterns
   - Follow language conventions

4. QUALITY
   - Follow language-specific style guides
   - Handle errors appropriately
   - Use type hints where applicable
   - Write testable code

OUTPUT FORMAT:
==============
Always wrap code in properly fenced code blocks with language identifier:

```python
# Python code here
```

```javascript
// JavaScript code here
```

Return JSON when requested:
{
    "formatted_content": "```language\\n...\\n```",
    "language": "python|javascript|java|etc",
    "has_docstrings": true/false,
    "summary": "brief description"
}"""


# =============================================================================
# PYTHON CODE PROMPT
# =============================================================================

CODE_PYTHON_PROMPT = """Format the following Python code according to PEP 8 standards.

PYTHON FORMATTING GUIDELINES (PEP 8):
======================================

1. INDENTATION:
   - Use 4 spaces per indentation level
   - Never mix tabs and spaces
   - Continuation lines should align with opening delimiter

2. LINE LENGTH:
   - Maximum 79 characters for code
   - Maximum 72 characters for docstrings/comments
   - Break long lines using implied line continuation

3. IMPORTS:
   - One import per line
   - Group in order: standard library, third-party, local
   - Absolute imports preferred
   - Avoid wildcard imports

4. WHITESPACE:
   - Two blank lines around top-level definitions
   - One blank line around method definitions
   - No trailing whitespace
   - Space after comma, not before

5. NAMING CONVENTIONS:
   - functions: lower_case_with_underscores
   - classes: CapitalizedWords
   - constants: UPPER_CASE_WITH_UNDERSCORES
   - private: _single_leading_underscore
   - "magic": __double_leading_underscore__

6. DOCSTRINGS:
   - Triple double quotes
   - First line: brief summary
   - Blank line after summary if multi-line
   - Document Args, Returns, Raises

7. TYPE HINTS:
   - Use type hints for function signatures
   - Use typing module for complex types
   - Optional for variables

DOCSTRING FORMAT (Google Style):
================================
def function_name(param1: Type1, param2: Type2) -> ReturnType:
    \"\"\"Brief summary of function.
    
    More detailed description if needed.
    
    Args:
        param1: Description of param1.
        param2: Description of param2.
    
    Returns:
        Description of return value.
    
    Raises:
        ExceptionType: When exception occurs.
    
    Example:
        >>> function_name(arg1, arg2)
        expected_result
    \"\"\"
    pass

EXAMPLE TRANSFORMATION:

BEFORE:
```
def calc(x,y,op):
    if op=='+':return x+y
    elif op=='-':return x-y
    else:return None
```

AFTER:
```python
def calculate(x: float, y: float, operation: str) -> float | None:
    \"\"\"Perform arithmetic operation on two numbers.
    
    Args:
        x: First operand.
        y: Second operand.
        operation: Operation to perform ('+' or '-').
    
    Returns:
        Result of the operation, or None if invalid operation.
    
    Example:
        >>> calculate(5, 3, '+')
        8.0
    \"\"\"
    if operation == '+':
        return x + y
    elif operation == '-':
        return x - y
    else:
        return None
```

INPUT CODE:
{content}

REQUIREMENTS:
- Add docstrings: {add_docstrings}
- Add type hints: {add_type_hints}
- Style: {style}

Return the formatted Python code."""


# =============================================================================
# JAVASCRIPT CODE PROMPT
# =============================================================================

CODE_JAVASCRIPT_PROMPT = """Format the following JavaScript code following modern best practices.

JAVASCRIPT FORMATTING GUIDELINES:
==================================

1. INDENTATION:
   - Use 2 spaces (or 4, be consistent)
   - Same indent style throughout
   - Indent switch cases

2. SEMICOLONS:
   - Always use semicolons (recommended)
   - Or consistently omit (style choice)

3. BRACES:
   - Same-line opening brace (Allman or K&R)
   - Always use braces for blocks

4. NAMING:
   - camelCase for variables and functions
   - PascalCase for classes and components
   - UPPER_SNAKE_CASE for constants
   - _prefix for private (convention)

5. MODERN SYNTAX:
   - Use const/let, avoid var
   - Arrow functions for callbacks
   - Template literals for string interpolation
   - Destructuring where appropriate
   - Optional chaining (?.) and nullish coalescing (??)

6. DOCUMENTATION (JSDoc):
   /**
    * Brief description.
    * @param {{type}} name - Description
    * @returns {{type}} Description
    * @throws {{ErrorType}} Description
    * @example
    * functionName(arg);
    */

EXAMPLE TRANSFORMATION:

BEFORE:
```
function getUser(id,callback) {
var user = users.find(function(u){return u.id==id})
if(user){callback(null,user)}else{callback('not found',null)}
}
```

AFTER:
```javascript
/**
 * Retrieves a user by their ID.
 * @param {{string}} id - The user's unique identifier.
 * @param {{Function}} callback - Callback function(error, user).
 * @returns {{void}}
 */
const getUser = (id, callback) => {{
  const user = users.find((u) => u.id === id);
  
  if (user) {{
    callback(null, user);
  }} else {{
    callback('User not found', null);
  }}
}};
```

INPUT CODE:
{content}

REQUIREMENTS:
- Use ES6+: {use_es6}
- Add JSDoc: {add_jsdoc}
- Semicolons: {use_semicolons}

Return the formatted JavaScript code."""


# =============================================================================
# JAVA CODE PROMPT
# =============================================================================

CODE_JAVA_PROMPT = """Format the following Java code following standard conventions.

JAVA FORMATTING GUIDELINES:
============================

1. INDENTATION:
   - Use 4 spaces
   - No tabs

2. BRACES:
   - Opening brace on same line
   - Closing brace on new line
   - Always use braces (even single statements)

3. NAMING:
   - Classes: PascalCase
   - Methods/Variables: camelCase
   - Constants: UPPER_SNAKE_CASE
   - Packages: lowercase

4. ORDERING:
   - Package declaration
   - Import statements (grouped)
   - Class declaration
   - Static variables
   - Instance variables
   - Constructors
   - Methods

5. JAVADOC:
   /**
    * Brief summary.
    * 
    * <p>Detailed description.</p>
    * 
    * @param paramName description
    * @return description
    * @throws ExceptionType description
    */

EXAMPLE TRANSFORMATION:

BEFORE:
```
public class calculator{
public int add(int a,int b){return a+b;}
public int sub(int a,int b){return a-b;}}
```

AFTER:
```java
/**
 * Simple calculator for basic arithmetic operations.
 */
public class Calculator {{
    
    /**
     * Adds two integers.
     *
     * @param a the first operand
     * @param b the second operand
     * @return the sum of a and b
     */
    public int add(int a, int b) {{
        return a + b;
    }}
    
    /**
     * Subtracts second integer from first.
     *
     * @param a the first operand
     * @param b the second operand
     * @return the difference of a and b
     */
    public int subtract(int a, int b) {{
        return a - b;
    }}
}}
```

INPUT CODE:
{content}

REQUIREMENTS:
- Add Javadoc: {add_javadoc}
- Access modifiers: {check_access}

Return the formatted Java code."""


# =============================================================================
# SQL CODE PROMPT
# =============================================================================

CODE_SQL_PROMPT = """Format the following SQL code for readability.

SQL FORMATTING GUIDELINES:
===========================

1. KEYWORDS:
   - Uppercase for SQL keywords
   - SELECT, FROM, WHERE, JOIN, etc.

2. INDENTATION:
   - Main clauses at start of line
   - Indent continuation/subclauses
   - Align related elements

3. LINE BREAKS:
   - Each major clause on new line
   - One column per line in SELECT (optional)
   - Subqueries indented

4. ALIASING:
   - Use meaningful table aliases
   - Always use AS for clarity

5. COMMENTS:
   - -- for single line
   - /* */ for multi-line
   - Comment complex logic

EXAMPLE TRANSFORMATION:

BEFORE:
```
select u.name,u.email,count(o.id) from users u left join orders o on u.id=o.user_id where u.active=1 group by u.id having count(o.id)>5 order by count(o.id) desc;
```

AFTER:
```sql
-- Get active users with more than 5 orders
SELECT 
    u.name,
    u.email,
    COUNT(o.id) AS order_count
FROM 
    users AS u
    LEFT JOIN orders AS o 
        ON u.id = o.user_id
WHERE 
    u.active = 1
GROUP BY 
    u.id,
    u.name,
    u.email
HAVING 
    COUNT(o.id) > 5
ORDER BY 
    order_count DESC;
```

INPUT CODE:
{content}

REQUIREMENTS:
- Uppercase keywords: {uppercase_keywords}
- Add comments: {add_comments}
- One column per line: {column_per_line}

Return the formatted SQL code."""


# =============================================================================
# EXPLAINED CODE PROMPT
# =============================================================================

CODE_EXPLAINED_PROMPT = """Add comprehensive explanations to the following code.

CODE EXPLANATION GUIDELINES:
=============================

1. STRUCTURE:
   - Brief overview at top
   - Inline comments for logic
   - Block comments for sections
   - Summary at end

2. EXPLANATION LEVELS:

   OVERVIEW (Top):
   ```python
   \"\"\"
   Module/Function Purpose
   =======================
   
   This code implements [purpose].
   
   Key Concepts:
   - Concept 1: Brief explanation
   - Concept 2: Brief explanation
   
   Complexity: O(n) time, O(1) space
   \"\"\"
   ```

   INLINE COMMENTS:
   ```python
   # Initialize counter for tracking iterations
   count = 0
   
   # Iterate through each element to find target
   for item in collection:  # O(n) iteration
       # Check if current item matches criteria
       if item == target:
           return True  # Early exit on match
   ```

   SECTION COMMENTS:
   ```python
   # ============================================
   # SECTION: Input Validation
   # ============================================
   # Validate all inputs before processing to
   # prevent errors and ensure data integrity
   ```

3. LINE-BY-LINE TABLE (Optional):

   | Line | Code | Explanation |
   |------|------|-------------|
   | 1 | `def func(x):` | Function definition taking parameter x |
   | 2 | `  if x < 0:` | Check for negative input |

4. COMPLEXITY ANALYSIS:
   
   **Time Complexity:** $O(n \\log n)$
   - Sorting: $O(n \\log n)$
   - Iteration: $O(n)$
   - Total: $O(n \\log n)$
   
   **Space Complexity:** $O(n)$
   - Auxiliary array: $O(n)$
   - Stack space: $O(\\log n)$

EXAMPLE:

```python
\"\"\"
Binary Search Implementation
============================

Efficiently finds target value in sorted array using
divide-and-conquer approach.

Time Complexity: O(log n)
Space Complexity: O(1) iterative, O(log n) recursive
\"\"\"

def binary_search(arr: list[int], target: int) -> int:
    \"\"\"
    Find target in sorted array using binary search.
    
    Args:
        arr: Sorted list of integers
        target: Value to find
    
    Returns:
        Index of target if found, -1 otherwise
    \"\"\"
    # Initialize search boundaries
    left = 0                    # Start of search range
    right = len(arr) - 1        # End of search range
    
    # Continue while search range is valid
    while left <= right:
        # Calculate middle point (avoid overflow)
        mid = left + (right - left) // 2
        
        # Check if we found the target
        if arr[mid] == target:
            return mid          # Target found at index mid
        
        # Narrow search range based on comparison
        elif arr[mid] < target:
            left = mid + 1      # Target in right half
        else:
            right = mid - 1     # Target in left half
    
    # Target not found in array
    return -1

# ============================================
# COMPLEXITY ANALYSIS
# ============================================
# Time:  O(log n) - halving search space each iteration
# Space: O(1) - only using constant extra space
```

INPUT CODE:
{content}

REQUIREMENTS:
- Explanation level: {explanation_level}
- Include complexity: {include_complexity}
- Add line table: {add_line_table}

Return the code with comprehensive explanations."""


# =============================================================================
# CODE VALIDATION PROMPT
# =============================================================================

CODE_VALIDATION_PROMPT = """Validate the following code for correctness and style.

VALIDATION CHECKLIST:
=====================

1. SYNTAX CHECK:
   □ Valid syntax for the language
   □ Balanced brackets/braces/parentheses
   □ Proper string delimiters
   □ Correct indentation

2. STYLE CHECK:
   □ Follows language conventions
   □ Consistent naming
   □ Proper spacing/formatting
   □ Reasonable line length

3. DOCUMENTATION CHECK:
   □ Has docstrings/comments
   □ Parameters documented
   □ Return values documented
   □ Complex logic explained

4. QUALITY CHECK:
   □ No obvious bugs
   □ Error handling present
   □ Edge cases considered
   □ No code smells

CODE TO VALIDATE:
{content}

LANGUAGE: {language}

Return JSON with:
{{
    "is_valid": true/false,
    "language": "detected language",
    "syntax_errors": ["error1", "error2"],
    "style_warnings": ["warning1"],
    "documentation_issues": ["issue1"],
    "suggestions": ["suggestion1"],
    "corrected_content": "fixed code if needed"
}}"""
