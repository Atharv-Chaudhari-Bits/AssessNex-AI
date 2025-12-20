"""
Assignment and Project-based question prompts.

Multi-part assignments, mini-projects, and comprehensive tasks
that require multiple hours of work and test integrated knowledge.
"""

ASSIGNMENT_BASIC_PROMPT = """
For Basic Assignment Questions:

STRUCTURE:
Multi-part assignment with 3-5 subtasks
Builds progressively in complexity
Tests integrated knowledge

EXAMPLE ASSIGNMENT:
\"\"\"
ASSIGNMENT: Implement a Student Management System

Part A (20%): Data Structure Design
- Design a Student class with properties: name, id, courses, gpa
- Implement methods: add_course(), remove_course(), calculate_gpa()

Part B (30%): Collection Management
- Create a StudentDatabase class
- Implement: add_student(), remove_student(), find_by_id(), list_by_gpa()
- Use appropriate data structures (dict for O(1) lookup)

Part C (30%): Analysis and Reporting
- Write query functions: find_top_students(n), find_by_major(major)
- Implement sorting by different criteria
- Generate summary statistics

Part D (20%): Error Handling and Edge Cases
- Handle duplicate IDs
- Validate input data
- Write unit tests for all functions

REQUIREMENTS:
- Code must be well-documented with comments
- Follow PEP 8 style guide
- Include time/space complexity analysis
- Provide example usage

EXPECTED DELIVERABLES:
1. Well-structured code files
2. Documentation/comments
3. Example test cases
4. Complexity analysis document
\"\"\"

EVALUATION CRITERIA:
- Correctness (does it work?)
- Code quality (readability, style)
- Efficiency (algorithm choice)
- Documentation (comments, docstrings)
- Testing (edge cases covered)
- Design (appropriate data structures)
"""

ASSIGNMENT_INTERMEDIATE_PROMPT = """
For Intermediate Assignment Questions:

STRUCTURE:
5-7 interconnected subtasks
Requires algorithm design and optimization
5-10 hours of work

EXAMPLE ASSIGNMENT:
\"\"\"
ASSIGNMENT: Build a File Search Engine

Part 1 (15%): File Indexing
- Create FileIndex class
- Index files by name, size, date, content keywords
- Use inverted index for keyword search

Part 2 (20%): Search Functionality
- Implement exact match search
- Implement fuzzy search (typo tolerance)
- Support wildcard patterns
- Optimize search with indexing

Part 3 (20%): Query Optimization
- Profile query performance
- Implement caching for frequent queries
- Use appropriate data structures (B-tree concepts)

Part 4 (20%): Ranking and Scoring
- Implement relevance scoring
- Support different search types with scores
- Sort results by multiple criteria

Part 5 (15%): Advanced Features
- Implement regex-based search
- Multi-field search combining results
- Boolean operators (AND, OR, NOT)

Part 6 (10%): Testing and Documentation
- Unit tests for each component
- Integration tests
- Performance benchmarks
- Comprehensive documentation

TECHNICAL REQUIREMENTS:
- Use efficient data structures (hash tables, trees)
- Time complexity analysis for each operation
- Space optimization strategies
- Caching/memoization where applicable
- Proper error handling and validation

DELIVERABLES:
1. Complete source code
2. Unit tests with >80% coverage
3. Performance analysis report
4. Usage documentation
5. Design decisions document
\"\"\"
"""

ASSIGNMENT_ADVANCED_PROMPT = """
For Advanced Assignment Questions (Mini Project):

STRUCTURE:
8-12 comprehensive subtasks
Requires system design and optimization
20-40 hours of work
Tests advanced concepts

EXAMPLE ASSIGNMENT:
\"\"\"
ASSIGNMENT: Design and Implement a Distributed Cache System

Part 1 (10%): Core Cache Implementation
- Implement LRU/LFU cache eviction policies
- Support multiple data types
- Thread-safe operations

Part 2 (15%): Consistency Mechanisms
- Implement cache invalidation strategies
- TTL (Time To Live) support
- Cache coherence between replicas

Part 3 (15%): Distributed Architecture
- Design multi-node cache cluster
- Implement consistent hashing for key distribution
- Handle node failures and recovery

Part 4 (15%): Persistence Layer
- Design backup mechanism
- Implement Write-Through and Write-Back policies
- Durability guarantees

Part 5 (15%): Monitoring and Optimization
- Implement metrics collection (hit rate, throughput)
- Implement cache warming strategies
- Performance optimization

Part 6 (15%): Advanced Features
- Implement Bloom filters for existence checking
- Support for transactions
- Pub/sub notification system

Part 7 (10%): Testing and Documentation
- Load testing with concurrent requests
- Failure scenario testing
- Complete API documentation
- Architecture documentation

TECHNICAL REQUIREMENTS:
- Advanced data structures (skip lists, bloom filters, etc.)
- Concurrency/parallelism
- System design principles
- Performance analysis
- Scalability considerations
- Fault tolerance

DELIVERABLES:
1. Complete working system
2. Comprehensive test suite
3. Performance benchmarks
4. Architecture and design documents
5. Deployment guide
6. API documentation
7. Optimization analysis
\"\"\"
"""

PROJECT_SETUP_TEMPLATE = """
ASSIGNMENT PROJECT SETUP REQUIREMENTS:

For each assignment, provide:

1. PROJECT DESCRIPTION
   - Clear problem statement
   - Real-world context
   - Learning objectives

2. REQUIREMENTS BREAKDOWN
   - Functional requirements (what it should do)
   - Non-functional requirements (performance, scalability)
   - Technical constraints

3. PART BREAKDOWN
   - Each subtask with clear description
   - Estimated time and difficulty
   - Dependencies between parts
   - Percentage weight for grading

4. ACCEPTANCE CRITERIA
   - Specific conditions for "correct" solution
   - Test cases to pass
   - Code quality metrics
   - Documentation requirements

5. RESOURCES PROVIDED
   - Starter code (if any)
   - Data files or format specifications
   - Library/tool recommendations
   - Reference materials

6. EVALUATION RUBRIC
   - Correctness scoring
   - Code quality metrics
   - Performance benchmarks
   - Documentation assessment
   - Testing coverage

7. DELIVERABLES CHECKLIST
   - Code files to submit
   - Documentation to provide
   - Tests to include
   - Performance reports needed
"""

# Dictionary for assignment types
ASSIGNMENT_TYPES = {
    "basic": ASSIGNMENT_BASIC_PROMPT,
    "intermediate": ASSIGNMENT_INTERMEDIATE_PROMPT,
    "advanced": ASSIGNMENT_ADVANCED_PROMPT,
    "template": PROJECT_SETUP_TEMPLATE,
}
