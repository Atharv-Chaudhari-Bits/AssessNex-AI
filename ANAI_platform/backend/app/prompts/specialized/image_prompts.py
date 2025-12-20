"""
Image-based and diagram questions prompts.

For questions that reference visual diagrams, algorithms flows, network graphs,
or visual representations. Questions can include ASCII diagrams or references
to well-known visual patterns.
"""

IMAGE_BASED_PROMPT = """
For Image/Diagram-based questions:

QUESTION FORMAT:
Include ASCII representation or detailed description of the diagram.
Can test understanding of:
- Algorithm visualization (sorting steps, tree traversal)
- Network/Graph structures
- Neural network architectures
- Data flow diagrams
- State machines

EXAMPLE - Algorithm Visualization:
\"\"\"
Given this array and the step-by-step swap sequence for a sorting algorithm:
Initial: [5, 2, 8, 1, 9]
Step 1:  [2, 5, 8, 1, 9]  (swap 5 and 2)
Step 2:  [2, 5, 1, 8, 9]  (swap 8 and 1)
Step 3:  [2, 1, 5, 8, 9]  (swap 5 and 1)

Which sorting algorithm is this?
A) Bubble Sort
B) Selection Sort
C) Insertion Sort
D) Quick Sort
\"\"\"

EXAMPLE - Graph/Tree Visualization:
\"\"\"
Given this tree structure:
        A
       / \\
      B   C
     / \\
    D   E

What is the In-order traversal?
A) A B D E C
B) D B E A C
C) D E B A C
D) B D A C E
\"\"\"

EXAMPLE - Neural Network Diagram:
\"\"\"
Given this CNN architecture:
Input(28x28x1) -> Conv(32, 3x3) -> ReLU -> MaxPool(2x2) -> FC(128) -> ReLU -> FC(10)

After each Conv layer, what is the spatial dimension if 'same' padding is used?
A) 26x26
B) 28x28
C) 32x32
D) 14x14
\"\"\"

VISUAL REPRESENTATION IN JSON:
{
    "question_text": "Question text with ASCII or description",
    "diagram_description": "ASCII art or detailed description of diagram",
    "diagram_ascii": "
        Visual representation
        in ASCII if applicable
    ",
    "requires_visualization": true,
    "visual_hint": "What algorithm/concept this visualizes"
}
"""

ALGORITHM_FLOW_PROMPT = """
For Algorithm Flow / Step-by-step visualization:

QUESTION FORMAT:
Show algorithm execution steps visually and ask about the process.

EXAMPLE - BFS Traversal:
\"\"\"
Starting from node A, trace BFS on this graph:
    A --- B --- D
    |     |
    C --- E

Queue states:
Initial: [A]
After process A: [B, C], visited: {A}
After process B: [C, E, D], visited: {A, B}
... continue ...

What is the BFS order?
\"\"\"

EXAMPLE - Dynamic Programming Table:
\"\"\"
Fill the DP table for Fibonacci(5):
n:    0  1  2  3  4  5
dp:  [_][_][_][_][_][_]

After computation, what is dp[5]?
\"\"\"

EXPECTED ANSWER:
Clear step-by-step trace showing:
- Current state of data structure
- What operation is being performed
- What the result of that operation is
- Final answer with explanation
"""

ANT_COLONY_VISUALIZATION = """
For Ant Colony Optimization or Similar Visual Problems:

QUESTION FORMAT:
\"\"\"
Ant Colony traveling on a grid with pheromone trails:

Grid (5x5) with paths:
Start: (0,0) -> Goal: (4,4)

Initial pheromone:
[0.5][0.5][0.5][0.5][0.5]
[0.5][ S ][0.3][0.3][0.5]
[0.5][0.3][ P ][0.3][0.5]
[0.5][0.3][0.3][ P ][0.5]
[0.5][0.5][0.5][0.5][ G ]

Ants take paths based on pheromone * distance heuristic.
After one iteration, which path had most ants?

ASCII Path visualization:
S . . . .
. . P . .
. P . P .
. . . . P
. . . . G
\"\"\"

KEY ELEMENTS:
- Show grid/network structure
- Mark special nodes (start, goal, obstacles)
- Show pheromone levels or weights
- Trace one or two ant paths
- Ask about prediction or outcome
"""

GRAPH_ALGORITHM_VISUALIZATION = """
For Graph Algorithm visualization:

EXAMPLES:
1. Dijkstra's Algorithm:
   Show graph with nodes and edge weights
   Show distance table after each iteration
   Ask for shortest path

2. DFS/BFS Traversal:
   Show tree/graph structure
   Show traversal order with step numbers
   Ask for traversal sequence

3. Minimum Spanning Tree:
   Show weighted graph
   Show edges added in order (Kruskal's/Prim's)
   Show final MST

VISUALIZATION REQUIREMENTS:
- Clear node labels
- Edge weights shown
- Path or tree structure clear
- Step numbers or colors to show sequence
"""

# Dictionary for quick access
IMAGE_QUESTION_TYPES = {
    "algorithm_flow": ALGORITHM_FLOW_PROMPT,
    "graph_visualization": GRAPH_ALGORITHM_VISUALIZATION,
    "ant_colony": ANT_COLONY_VISUALIZATION,
    "general_diagram": IMAGE_BASED_PROMPT,
}
