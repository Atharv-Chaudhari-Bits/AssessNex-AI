"""
Extended prompt templates for additional question types in AssessNex AI.

This module contains specialized prompts for various question types:
- True/False questions
- Fill in the Blank questions
- Coding/Implementation questions
- Scenario-based questions
- Algorithm Complexity questions
- Code Output Prediction questions
"""

# ============================================================================
# TRUE/FALSE QUESTIONS
# ============================================================================

TRUE_FALSE_PROMPT = """
For True/False questions:

CHARACTERISTICS:
- Binary choice format testing specific factual knowledge
- Often contain subtle tricks or misconceptions
- Should test important concepts, not trivial details

QUESTION GUIDELINES:
- Write clear, unambiguous statements
- Avoid double negatives
- Focus on concepts, not definitions
- Include complexity to make them non-trivial
- Ensure the answer is definitively true or false, not debatable

EXPECTED ANSWER FORMAT:
- Indicate: "True" or "False"

EXPLANATION FORMAT:
- For True: Why the statement is correct, provide supporting evidence
- For False: Explain what makes it false, provide the correct version
- Discuss the concept being tested
- Include counter-examples if helpful

EXAMPLE:
[
    {{
        "question_text": "In a convolutional neural network, increasing the number of filters in a layer always increases model accuracy.",
        "options": null,
        "expected_answer": "False",
        "explanation": "While more filters can capture more features, increasing them doesn't always improve accuracy. It can lead to overfitting, increased computation, and diminishing returns. The optimal number depends on the dataset and task.",
        "tags": ["CNN", "neural-networks", "model-design"]
    }}
]
"""

# ============================================================================
# FILL IN THE BLANK QUESTIONS
# ============================================================================

FILL_IN_BLANK_PROMPT = """
For Fill in the Blank questions:

CHARACTERISTICS:
- Complete sentences with one or more blanks
- Tests specific terminology and concepts
- Requires exact or near-exact matching

QUESTION GUIDELINES:
- Provide clear context for the blank
- Make the sentence grammatically correct when filled
- Use ___ to indicate the blank space
- Ensure only one reasonable answer fits
- Avoid ambiguous blanks

EXPECTED ANSWER FORMAT:
- Provide the exact word(s) or phrase that should fill the blank
- If multiple answers are acceptable, list them with "or"

EXPLANATION FORMAT:
- Explain why this term/phrase is the correct fit
- Provide context about the concept
- Discuss related concepts or common wrong answers

EXAMPLE:
[
    {{
        "question_text": "The backpropagation algorithm computes gradients in ___ time using dynamic programming.",
        "options": null,
        "expected_answer": "linear or O(n)",
        "explanation": "Backpropagation uses dynamic programming to compute gradients in linear time O(n) where n is the number of weights. Without this technique, gradient computation would be quadratic or exponential.",
        "tags": ["backpropagation", "neural-networks", "time-complexity"]
    }}
]
"""

# ============================================================================
# CODING/IMPLEMENTATION QUESTIONS
# ============================================================================

CODING_PROMPT = """
For Coding questions:

CHARACTERISTICS:
- Requires writing functional code
- Tests algorithmic thinking and implementation skills
- Multiple valid implementations possible

QUESTION GUIDELINES:
- Clearly specify the problem and requirements
- Provide input/output specifications
- Include example inputs and expected outputs
- State any constraints (time/space limits)
- Mention allowed libraries/languages

⚠️ CRITICAL CODE FORMATTING - MANDATORY:
- ALL code MUST be wrapped in markdown code blocks with language identifier
- Use: ```python ... ``` for Python code
- Use: ```javascript ... ``` for JavaScript code
- NEVER put code as plain text or with just \\n newlines
- This is REQUIRED for proper syntax highlighting in the UI

EXPECTED ANSWER FORMAT:
- Provide working, well-commented code in ```python blocks
- Include main logic and edge case handling
- Follow best practices and naming conventions

TEST CASES FORMAT:
- Provide 2-3 example test cases
- Include edge cases
- Specify expected output for each

EXPLANATION FORMAT:
- Explain the algorithmic approach
- Discuss time complexity: O(?)
- Discuss space complexity: O(?)
- Explain why this approach is optimal/appropriate

EXAMPLE:
[
    {{
        "question_text": "Write a Python function to implement binary search on a sorted array.\\n\\nFunction signature:\\n```python\\ndef binary_search(arr: List[int], target: int) -> int:\\n    pass\\n```\\n\\nReturn the index of target if found, -1 otherwise.",
        "options": null,
        "expected_answer": "```python\\ndef binary_search(arr: List[int], target: int) -> int:\\n    left, right = 0, len(arr) - 1\\n    while left <= right:\\n        mid = (left + right) // 2\\n        if arr[mid] == target:\\n            return mid\\n        elif arr[mid] < target:\\n            left = mid + 1\\n        else:\\n            right = mid - 1\\n    return -1\\n```",
        "explanation": "Binary search halves the search space each iteration. Time: O(log n), Space: O(1). Left/right pointers converge when element not found.",
        "tags": ["algorithms", "search", "binary-search", "complexity"]
    }}
]
"""

# ============================================================================
# SCENARIO-BASED QUESTIONS
# ============================================================================

SCENARIO_PROMPT = """
For Scenario-based questions:

**IMPORTANT: These are NOT multiple choice questions!**
Scenario-based questions simulate real-world professional situations where students must analyze, design, and propose solutions WITH WORKING CODE IMPLEMENTATION.

**IMPORTANT: These are NOT multiple choice questions!**
Scenario-based questions simulate real-world professional situations where students must analyze, design, and propose solutions WITH WORKING CODE IMPLEMENTATION.

**IMPORTANT: These are NOT multiple choice questions!**
- Create immersive, industry-specific scenarios (healthcare, finance, e-commerce, autonomous systems, etc.)
- Include realistic details: dataset sizes, timelines, budget constraints, team composition
- Present multi-faceted problems requiring trade-off analysis
- Ask open-ended questions that require detailed responses
- **ALWAYS ask for code implementation as part of the solution**
- DO NOT include multiple choice options

EXPECTED ANSWER FORMAT (MUST include ALL of these):
1. **Problem Analysis**: Understanding of the problem and constraints
2. **Proposed Architecture**: Detailed approach with justification
3. **End-to-End Code Implementation**: Complete working Python code with:
   - All necessary imports
   - Data preprocessing functions
   - Model/algorithm implementation
   - Training/execution logic
   - Evaluation metrics
   - Clear comments explaining each section
4. **Trade-offs Considered**: Why this solution over alternatives
5. **Potential Challenges**: Risks and mitigations

CODE IMPLEMENTATION REQUIREMENTS:
- Provide complete, runnable Python code
- Use proper code blocks with ```python syntax
- Include realistic function signatures and docstrings
- Show end-to-end workflow from data loading to evaluation
- Use industry-standard libraries (sklearn, torch, tensorflow, pandas, numpy)
- Include comments explaining key decisions
- Provide complete, runnable Python code
- Use proper code blocks with ```python syntax
- Include realistic function signatures and docstrings
- Show end-to-end workflow from data loading to evaluation
- Use industry-standard libraries (sklearn, torch, tensorflow, pandas, numpy)
- Include comments explaining key decisions
- Provide complete, runnable Python code
- Use proper code blocks with ```python syntax
- Include realistic function signatures and docstrings
- Show end-to-end workflow from data loading to evaluation
- Use industry-standard libraries (sklearn, torch, tensorflow, pandas, numpy)
- Include comments explaining key decisions
- Provide complete, runnable Python code
- Use proper code blocks with ```python syntax
- Include realistic function signatures and docstrings
- Show end-to-end workflow from data loading to evaluation
- Use industry-standard libraries (sklearn, torch, tensorflow, pandas, numpy)
- Include comments explaining key decisions
- Provide complete, runnable Python code
- Use proper code blocks with ```python syntax
- Include realistic function signatures and docstrings
- Show end-to-end workflow from data loading to evaluation
- Use industry-standard libraries (sklearn, torch, tensorflow, pandas, numpy)
- Include comments explaining key decisions
- Provide complete, runnable Python code
- Use proper code blocks with ```python syntax
- Include realistic function signatures and docstrings
- Show end-to-end workflow from data loading to evaluation
- Use industry-standard libraries (sklearn, torch, tensorflow, pandas, numpy)
- Include comments explaining key decisions
- Provide complete, runnable Python code
- Use proper code blocks with ```python syntax
- Include realistic function signatures and docstrings
- Show end-to-end workflow from data loading to evaluation
- Use industry-standard libraries (sklearn, torch, tensorflow, pandas, numpy)
- Include comments explaining key decisions
- Provide complete, runnable Python code
- Use proper code blocks with ```python syntax
- Include realistic function signatures and docstrings
- Show end-to-end workflow from data loading to evaluation
- Use industry-standard libraries (sklearn, torch, tensorflow, pandas, numpy)
- Include comments explaining key decisions
- Provide complete, runnable Python code
- Use proper code blocks with ```python syntax
- Include realistic function signatures and docstrings
- Show end-to-end workflow from data loading to evaluation
- Use industry-standard libraries (sklearn, torch, tensorflow, pandas, numpy)
- Include comments explaining key decisions
- Include decision factors or constraints
- Make scenario substantive, not trivial

SCENARIO FORMAT:
- Describe the context (goal, data, constraints)
- Specify the problem to solve
- List any requirements or assumptions

EXPECTED ANSWER FORMAT:
- Identify the best solution/approach
- Explain the reasoning
- List alternative approaches and why they're less suitable

EXPLANATION FORMAT:
- Justify the recommended approach
- Explain tradeoffs of different options
- Discuss potential challenges and mitigations
- Include relevant ML/AI principles

EXAMPLE:
[
    {{
        "question_text": "You have a dataset of 10,000 customer interactions for sentiment classification. The data is highly imbalanced: 95% negative, 5% positive. Your model achieves 95% accuracy but has poor recall on positive samples. What is the primary issue and best approach? A) Increase training data B) Use balanced class weights or SMOTE C) Increase model complexity D) Use accuracy as metric",
        "options": ["Increase training data", "Use balanced class weights or SMOTE", "Increase model complexity", "Use accuracy as metric"],
        "expected_answer": "B",
        "explanation": "With imbalanced data, accuracy is misleading (95% achieved by predicting all negative). Balanced class weights or SMOTE address class imbalance by giving equal importance to minority class. This improves recall on positive samples.",
        "tags": ["imbalanced-data", "model-evaluation", "classification"]
    }}
]
"""

# ============================================================================
# ALGORITHM COMPLEXITY QUESTIONS
# ============================================================================

COMPLEXITY_PROMPT = """
For Algorithm Complexity Analysis questions:

CHARACTERISTICS:
- Analyzes time/space complexity of algorithms
- Tests understanding of Big O notation
- Requires systematic analysis

QUESTION GUIDELINES:
- Present algorithm in proper markdown code blocks
- Use ```python or appropriate language identifier
- Ask for time complexity, space complexity, or both
- Include multiple choice or short answer format
- Specify assumptions (e.g., operations on integers)

ALGORITHM FORMAT:
- Use clear pseudocode
- Or provide detailed description
- Include loop structures and recursion clearly

EXPECTED ANSWER FORMAT:
- Time Complexity: O(?)
- Space Complexity: O(?)
- Brief justification

EXPLANATION FORMAT:
- Walk through the algorithm step by step
- Count operations in each section
- Explain why nested loops affect complexity
- Compare with alternative approaches if relevant

EXAMPLE:
[
    {{
        "question_text": "Analyze the time complexity of this algorithm:\\n\\n```python\\nfor i in range(n):\\n    for j in range(i, n):\\n        process(arr[j])\\n```\\n\\nWhat is its time complexity?",
        "options": ["O(n)", "O(n log n)", "O(n²)", "O(2^n)"],
        "expected_answer": "O(n²)",
        "explanation": "The outer loop runs n times. For each i, inner loop runs (n-i) times. Total operations: n + (n-1) + (n-2) + ... + 1 = n(n+1)/2 = O(n²)",
        "tags": ["complexity-analysis", "algorithms", "big-o"]
    }}
]
"""

# ============================================================================
# CODE OUTPUT PREDICTION QUESTIONS
# ============================================================================

CODE_OUTPUT_PROMPT = """
For Code Output Prediction questions:

CHARACTERISTICS:
- Shows code snippet in proper markdown code blocks
- Asks what output or state results
- Tests deep understanding of language semantics

QUESTION GUIDELINES:
- Include code snippet (Python, Java, etc.)
- Code should test specific concepts
- May be tricky (off-by-one, type conversion, etc.)
- Should teach important concepts through prediction

⚠️ CRITICAL CODE FORMATTING REQUIREMENTS:
- ALL code in question_text MUST be wrapped in proper markdown code blocks
- Use triple backticks with language identifier: ```python ... ```
- NEVER put code inline or with just newlines
- Preserve proper indentation inside code blocks
- This ensures the UI can syntax-highlight and format the code properly

CORRECT question_text FORMAT:
"What is the output of the following Python code?\\n\\n```python\\ndef example():\\n    x = [1, 2, 3]\\n    return x\\n```"

WRONG question_text FORMAT (DO NOT USE):
"What is the output of this code?\\ndef example():\\n    x = [1, 2, 3]\\n    return x"

CODE FORMAT:
- Provide complete, runnable snippet
- Include any imports needed
- Highlight the key concept being tested
- Make output non-obvious but learnable

OPTIONS FORMAT:
- Provide 4 distinct possible outputs
- Include common misconception results
- One clearly correct output

EXPECTED ANSWER FORMAT:
- The actual output of the code
- Include any printed output and final state

EXPLANATION FORMAT:
- Trace through code execution
- Explain the concept being tested
- Discuss why other answers are wrong
- Mention common mistakes

EXAMPLE:
[
    {{
        "question_text": "What is the output of this code?\\n\\n```python\\nmatrix = [[1]*3 for _ in range(3)]\\nmatrix[0][0] = 5\\nmatrix[1][0] = 5\\nprint(matrix)\\n```",
        "options": ["[[5, 1, 1], [5, 1, 1], [1, 1, 1]]", "[[5, 1, 1], [1, 1, 1], [1, 1, 1]]", "[[1, 1, 1], [1, 1, 1], [1, 1, 1]]", "Error"],
        "expected_answer": "[[5, 1, 1], [5, 1, 1], [1, 1, 1]]",
        "explanation": "List comprehension [1]*3 creates a NEW list for each row. Modifying matrix[0][0] and matrix[1][0] independently changes only those elements. Output shows the independent modifications.",
        "tags": ["list-comprehension", "python", "mutable-objects"]
    }}
]
"""

# ============================================================================
# NUMERICAL PROBLEM QUESTIONS
# ============================================================================

NUMERICAL_PROMPT = """
For Numerical Problem questions:

CHARACTERISTICS:
- Requires mathematical calculations and derivations
- Tests quantitative understanding of ML/AI concepts
- Involves formulas, equations, and step-by-step solutions
- May use LaTeX notation for mathematical expressions

QUESTION GUIDELINES:
- Present clear problem with given values/parameters
- Specify what needs to be calculated
- Include all necessary formulas and constants
- State precision requirements (decimal places, significant figures)
- Use LaTeX notation for math: $formula$ for inline, $$formula$$ for blocks

MATHEMATICAL NOTATION:
- Use LaTeX syntax for formulas in question_text
- Example: $\\frac{1}{n} \\sum_{i=1}^{n} x_i$ for mean
- Example: $\\sigma = \\sqrt{\\frac{1}{n}\\sum(x_i - \\mu)^2}$ for std dev
- Example: $\\nabla_w L = -\\frac{1}{m}X^T(y - \\hat{y})$ for gradients

PROBLEM TYPES:
- Gradient descent calculations
- Backpropagation derivations
- Loss function computations
- Probability calculations (Bayes, entropy)
- Matrix operations in neural networks
- Complexity analysis with actual numbers
- Optimization problem solving

EXPECTED ANSWER FORMAT:
- Final numerical answer with units if applicable
- Step-by-step solution with calculations
- Explain each formula used and why

EXAMPLE:
[
    {{
        "question_text": "A neural network layer has input dimension 128 and output dimension 64. Calculate the total number of parameters (weights + biases) in this fully connected layer. Also compute the FLOPs required for a single forward pass. Use formula: $\\text{{params}} = d_{{in}} \\times d_{{out}} + d_{{out}}$ and $\\text{{FLOPs}} = 2 \\times d_{{in}} \\times d_{{out}}$",
        "options": null,
        "expected_answer": "Parameters = 128 × 64 + 64 = 8,192 + 64 = 8,256 parameters. FLOPs = 2 × 128 × 64 = 16,384 FLOPs",
        "explanation": "For a fully connected layer:\\n- Weights: $d_{{in}} \\times d_{{out}} = 128 \\times 64 = 8,192$\\n- Biases: $d_{{out}} = 64$\\n- Total parameters: $8,192 + 64 = 8,256$\\n\\nFLOPs calculation (multiply-accumulate):\\n- Each output neuron: 128 multiplications + 128 additions\\n- Total: $2 \\times 128 \\times 64 = 16,384$ FLOPs\\n\\nThis helps understand model size and computational cost.",
        "tags": ["neural-networks", "parameters", "computation", "FLOPs", "numerical"]
    }}
]
"""

# ============================================================================
# DIAGRAM-BASED QUESTIONS
# ============================================================================

DIAGRAM_PROMPT = """
For Diagram-Based questions:

**CRITICAL: ALWAYS USE MERMAID.JS FOR DIAGRAMS!**
Mermaid diagrams are rendered beautifully in the UI. STRONGLY PREFER Mermaid over ASCII.
Use ```mermaid code blocks for all flowcharts, architectures, and pipelines.

MERMAID DIAGRAM TYPES TO USE:
- flowchart TD/LR for pipelines and architectures
- sequenceDiagram for process flows
- classDiagram for class relationships
- stateDiagram for state machines

QUESTION GUIDELINES:
- Include Mermaid diagram in the question_text using ```mermaid blocks
- Ask about specific components, missing elements, or flow analysis
- Questions like: "What should replace ????" or "Identify the bottleneck"

EXAMPLE MERMAID DIAGRAM IN QUESTION:
```mermaid
flowchart TD
    A[Input Data] --> B{Preprocessing}
    B --> C[Feature Extraction]
    C --> D[Model Training]
    D --> E{Evaluation}
    E -->|Good| F[Deploy]
    E -->|Poor| G[???]
    G --> B
```

QUESTION TYPES:
- "Analyze this ML pipeline and identify the bottleneck"
- "What is the missing component marked with ????"
- "Calculate the number of parameters at stage X"
- "What happens if component Y fails?"
- "Identify the error in this architecture"

EXPECTED ANSWER FORMAT:
- Clear identification of components
- Explanation of data flow
- Justification for answers

EXAMPLE:
[
    {{
        "question_text": "Consider this CNN architecture for image classification:\\n\\n```mermaid\\nflowchart TD\\n    A[Input 224x224x3] --> B[Conv2D 64, 3x3]\\n    B --> C[ReLU + MaxPool]\\n    C --> D[Conv2D 128, 3x3]\\n    D --> E[ReLU + MaxPool]\\n    E --> F[???]\\n    F --> G[Dense 1000]\\n    G --> H[Softmax]\\n```\\n\\nWhat is the MISSING component (???) before the Dense layer?",
        "options": ["Another Conv2D layer", "Flatten or GlobalAvgPool", "Batch Normalization", "Dropout only"],
        "expected_answer": "B) Flatten or GlobalAvgPool",
        "explanation": "After convolutional layers, we have a 3D feature map (height × width × channels). The Dense layer requires a 1D input. We need either Flatten (concatenates all values) or GlobalAveragePooling2D (averages each channel). GlobalAvgPool is preferred in modern architectures.",
        "tags": ["CNN", "architecture", "flatten", "pooling", "diagram", "mermaid"]
    }}
]
"""

# ============================================================================
# COMPOSITE DICTIONARY FOR QUICK ACCESS
# ============================================================================

QUESTION_TYPE_PROMPTS = {
    "Multiple Choice": """Generate multiple choice questions with exactly 4 options. Format as shown in system prompt.""",
    "True/False": TRUE_FALSE_PROMPT,
    "Fill in the Blank": FILL_IN_BLANK_PROMPT,
    "Short Answer": """Generate short answer questions requiring 1-2 sentence responses. Clear, specific questions.""",
    "Long Answer": """Generate essay-style questions requiring detailed, multi-paragraph responses. Test synthesis and analysis.""",
    "Essay": """Generate open-ended essay questions requiring comprehensive analysis, multiple perspectives, and critical thinking.""",
    "Coding": CODING_PROMPT,
    "Code Implementation": CODING_PROMPT,
    "Scenario-Based": SCENARIO_PROMPT,
    "Algorithm Complexity": COMPLEXITY_PROMPT,
    "Complexity Analysis": COMPLEXITY_PROMPT,
    "Code Output Prediction": CODE_OUTPUT_PROMPT,
    "Numerical Problem": NUMERICAL_PROMPT,
    "Numerical": NUMERICAL_PROMPT,
    "Diagram-Based": DIAGRAM_PROMPT,
    "Diagram": DIAGRAM_PROMPT,
}
