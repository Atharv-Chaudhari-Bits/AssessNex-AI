"""
Coding and Implementation question prompts.

Specialized prompts for code-based questions with focus on:
- Well-structured, commented code
- Clear algorithm explanation
- Time/space complexity analysis
"""

CODING_BASIC_PROMPT = """
For Coding questions - BASIC LEVEL:

QUESTION FORMAT:
- Implement a simple algorithm or data structure operation
- Clear problem statement
- Specific input/output examples

EXPECTED ANSWER FORMAT:
```python
# Solution with clear comments
def solution_name(param1, param2):
    '''Function description.'''
    # Step 1: Initialize variables
    result = []
    
    # Step 2: Main logic with explanatory comments
    for item in param1:
        # Explain each significant step
        if condition:
            result.append(item)
    
    return result
```

TEST CASES:
- Input: [1, 2, 3], Expected: [result]
- Input: [], Expected: []
- Input: edge_case, Expected: specific_result

EXPLANATION MUST INCLUDE:
- Algorithm approach (iterative/recursive/etc)
- Time Complexity: O(?)
- Space Complexity: O(?)
- Why this approach works
- Alternative approaches considered
"""

CODING_INTERMEDIATE_PROMPT = """
For Coding questions - INTERMEDIATE LEVEL:

QUESTION FORMAT:
- Implement algorithm with multiple steps
- May require data structures (trees, graphs, hash tables)
- Requires optimization thinking

EXPECTED ANSWER FORMAT:
```python
# Comments explaining overall approach
class Solution:
    def solve(self, data):
        '''
        Approach: Use hash map for O(1) lookups
        Time: O(n log n), Space: O(n)
        '''
        # Phase 1: Build hash structure
        hash_map = {}
        for item in data:
            # Detailed explanation of hash building
            hash_map[key] = value
        
        # Phase 2: Query phase
        result = []
        for query in queries:
            # Query execution logic with explanation
            if query in hash_map:
                result.append(hash_map[query])
        
        return result
```

INCLUDE:
- Multiple test cases (normal, edge, large input)
- Complexity analysis
- Alternative solutions discussion
- Common pitfalls to avoid
"""

CODING_ADVANCED_PROMPT = """
For Coding questions - ADVANCED LEVEL:

QUESTION FORMAT:
- Complex algorithm design problems
- Requires advanced data structures or dynamic programming
- Multi-step optimization needed

EXPECTED ANSWER FORMAT:
```python
# Clear description of algorithm choice
class AdvancedSolution:
    def __init__(self):
        '''Initialize any persistent structures.'''
        self.cache = {}
    
    def solve(self, problem_input):
        '''
        Algorithm: Dynamic Programming / Graph Algorithm / etc
        Time: O(n^2 log n)  # With detailed explanation
        Space: O(n^2)
        
        Key insight: [Explain why this approach is optimal]
        '''
        # Step 1: Preprocessing with comments
        processed = self._preprocess(problem_input)
        
        # Step 2: Core algorithm
        dp = [float('inf')] * len(processed)
        # dp[i] represents [clear explanation of state meaning]
        
        for i in range(len(processed)):
            for j in range(i):
                # Explain recurrence relation
                dp[i] = min(dp[i], dp[j] + cost(i, j))
        
        return self._reconstruct_solution(dp)
```

REQUIREMENT:
- Detailed comments at each major section
- Explanation of data structures chosen
- Complexity analysis with reasoning
- Multiple test cases including edge cases
- Discussion of alternative approaches
"""

CODING_WITH_TESTS_PROMPT = """
For Coding questions - INCLUDE TEST CASES:

SOLUTION STRUCTURE:
```python
def solution(input_data):
    \"\"\"
    Solution docstring with:
    - Problem summary
    - Approach explanation
    - Time/Space complexity
    \"\"\"
    # Implementation with comments
    pass

# TEST CASES - Must work for all
test_cases = [
    # (input, expected_output, description)
    ([1, 2, 3], [1, 2, 3], "Normal case"),
    ([], [], "Empty input"),
    ([1], [1], "Single element"),
    ([5, 4, 3, 2, 1], [1, 2, 3, 4, 5], "Reverse sorted"),
]

for inputs, expected, desc in test_cases:
    result = solution(inputs)
    assert result == expected, f"Failed: {desc}"
```
"""

# Quick reference dictionary
CODING_TYPE_PROMPTS = {
    "basic": CODING_BASIC_PROMPT,
    "intermediate": CODING_INTERMEDIATE_PROMPT,
    "advanced": CODING_ADVANCED_PROMPT,
    "with_tests": CODING_WITH_TESTS_PROMPT,
}
