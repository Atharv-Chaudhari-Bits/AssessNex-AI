"""
Mermaid diagram prompts - Comprehensive templates for all Mermaid diagram types.

This module provides detailed prompts for generating and validating:
- Flowcharts (TD/TB/BT/LR/RL)
- Sequence diagrams
- Class diagrams (UML)
- State diagrams
- ER diagrams
- Gantt charts
- Pie charts
- Mind maps

Each prompt includes:
- Detailed syntax rules
- Common patterns and examples
- Validation criteria
- Best practices
"""

# =============================================================================
# MERMAID SYSTEM PROMPT - Foundation for all Mermaid generation
# =============================================================================

MERMAID_SYSTEM_PROMPT = """You are an expert Mermaid diagram specialist. Your role is to create perfectly formatted, syntactically correct Mermaid diagrams that render flawlessly in any Mermaid-compatible viewer.

CORE PRINCIPLES:
================

1. SYNTAX PRECISION
   - Every diagram must start with the correct diagram type declaration
   - All node IDs must be valid (alphanumeric, no spaces, no special characters)
   - Connections must use proper arrow syntax
   - Labels must be properly quoted when containing special characters
   - Indentation should be consistent (2 or 4 spaces)

2. READABILITY
   - Use meaningful node IDs that describe purpose
   - Keep labels concise but descriptive
   - Organize nodes logically (top-to-bottom, left-to-right)
   - Group related nodes together
   - Use consistent naming conventions

3. VISUAL CLARITY
   - Avoid crossing lines where possible
   - Balance diagram layout
   - Use appropriate node shapes for different purposes
   - Apply styling judiciously (not every node needs custom styles)
   - Maintain adequate spacing between elements

4. ERROR PREVENTION
   - Escape special characters in labels: ()[]{}"'<>
   - Use quotes for labels with spaces or special chars
   - Verify all referenced nodes exist
   - Check bracket/parenthesis balance
   - Ensure unique node IDs within scope

COMMON MISTAKES TO AVOID:
=========================
- Using spaces in node IDs (use camelCase or underscores)
- Forgetting to quote labels with special characters
- Mixing arrow types inconsistently
- Creating circular references in certain diagram types
- Using invalid characters in node definitions

OUTPUT FORMAT:
==============
Always wrap Mermaid code in proper fenced code blocks:

```mermaid
[diagram code here]
```

Return JSON when requested with:
{
    "formatted_content": "```mermaid\\n...\\n```",
    "diagram_type": "flowchart|sequence|class|etc",
    "node_count": 5,
    "summary": "Brief description"
}"""


# =============================================================================
# FLOWCHART PROMPTS
# =============================================================================

MERMAID_FLOWCHART_PROMPT = """Generate a Mermaid flowchart diagram.

FLOWCHART SYNTAX REFERENCE:
============================

1. DIRECTION DECLARATIONS:
   - graph TD / flowchart TD  → Top to Down
   - graph TB / flowchart TB  → Top to Bottom (same as TD)
   - graph BT / flowchart BT  → Bottom to Top
   - graph LR / flowchart LR  → Left to Right
   - graph RL / flowchart RL  → Right to Left

2. NODE SHAPES:
   - A[Square]           → Default rectangular node
   - B(Rounded)          → Rounded corners
   - C((Circle))         → Circle/stadium shape
   - D{Diamond}          → Diamond/decision shape
   - E{{Hexagon}}        → Hexagonal shape
   - F[/Parallelogram/]  → Input/output shape
   - G[\\Parallelogram\\] → Alternate parallelogram
   - H[(Database)]       → Cylindrical database shape
   - I>Asymmetric]       → Asymmetric/flag shape
   - J(((Double Circle))) → Double circle

3. ARROW TYPES:
   - A --> B     → Standard arrow
   - A --- B     → Line without arrow
   - A -.- B     → Dotted line
   - A -.-> B    → Dotted arrow
   - A ==> B     → Thick arrow
   - A === B     → Thick line
   - A --text--> B  → Arrow with label
   - A -->|text| B  → Arrow with label (alternate)

4. SUBGRAPHS:
   subgraph title
       A --> B
   end

5. STYLING:
   style A fill:#f9f,stroke:#333,stroke-width:2px
   classDef className fill:#f9f,stroke:#333
   class A className

BEST PRACTICES:
===============
- Use meaningful node IDs (processData, not A1)
- Group related processes in subgraphs
- Use decision diamonds for conditionals
- Use parallelograms for I/O operations
- Keep flow direction consistent
- Add labels to clarify connections
- Limit nodes per subgraph to 7-10 for readability

EXAMPLE - Complex Process Flow:
```mermaid
flowchart TD
    subgraph Input["Data Input"]
        A[/User Upload/] --> B{Valid Format?}
        B -->|Yes| C[Parse Data]
        B -->|No| D[Error Message]
        D --> A
    end
    
    subgraph Processing["Data Processing"]
        C --> E[Validate Schema]
        E --> F{Schema Valid?}
        F -->|Yes| G[Transform Data]
        F -->|No| H[Log Errors]
        H --> I[Send Notification]
    end
    
    subgraph Output["Results"]
        G --> J[(Store in DB)]
        J --> K[/Generate Report/]
    end
    
    style A fill:#e1f5fe
    style J fill:#c8e6c9
    style D fill:#ffcdd2
```

INPUT TO PROCESS:
{content}

REQUIREMENTS:
- Direction: {direction}
- Include styling: {include_styles}
- Use subgraphs: {use_subgraphs}

Return the formatted Mermaid flowchart diagram."""


# =============================================================================
# SEQUENCE DIAGRAM PROMPTS
# =============================================================================

MERMAID_SEQUENCE_PROMPT = """Generate a Mermaid sequence diagram.

SEQUENCE DIAGRAM SYNTAX REFERENCE:
===================================

1. DIAGRAM DECLARATION:
   sequenceDiagram

2. PARTICIPANTS:
   - participant A           → Declare participant
   - participant A as Alice  → Declare with alias
   - actor User              → Declare as actor (stick figure)

3. MESSAGE TYPES:
   - A->>B: Message    → Solid line with arrowhead
   - A-->>B: Message   → Dotted line with arrowhead
   - A-xB: Message     → Solid line with X (async)
   - A--xB: Message    → Dotted line with X
   - A-)B: Message     → Solid line with open arrow (async)
   - A--)B: Message    → Dotted line with open arrow

4. ACTIVATIONS:
   - activate A        → Start activation
   - deactivate A      → End activation
   - A->>+B: Message   → Message and activate B
   - B-->>-A: Response → Response and deactivate B

5. NOTES:
   - Note right of A: Text
   - Note left of A: Text
   - Note over A: Text
   - Note over A,B: Text spanning participants

6. LOOPS AND CONDITIONS:
   loop Every minute
       A->>B: Check status
   end
   
   alt Success case
       A->>B: Success
   else Failure case
       A->>B: Failure
   end
   
   opt Optional path
       A->>B: Optional action
   end
   
   par Parallel execution
       A->>B: Action 1
   and
       A->>C: Action 2
   end

7. BREAKS AND RECTS:
   break Error condition
       A->>B: Error handling
   end
   
   rect rgb(200, 200, 240)
       A->>B: Highlighted section
   end

8. SEQUENCE NUMBERS:
   autonumber    → Auto-number messages

BEST PRACTICES:
===============
- Declare all participants at the top
- Use meaningful participant names or aliases
- Show activations for long-running operations
- Use notes to explain complex steps
- Group related interactions with loops/alt/opt
- Highlight important sections with rect
- Keep message labels concise
- Show both request and response

EXAMPLE - API Authentication Flow:
```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Client as Web Client
    participant API as API Gateway
    participant Auth as Auth Service
    participant DB as Database
    
    User->>Client: Enter credentials
    activate Client
    Client->>+API: POST /login
    API->>+Auth: Validate credentials
    Auth->>+DB: Query user
    DB-->>-Auth: User data
    
    alt Valid credentials
        Auth->>Auth: Generate JWT
        Auth-->>-API: JWT token
        API-->>-Client: 200 OK + token
        Client->>Client: Store token
        Note over Client: Token stored securely
    else Invalid credentials
        Auth-->>API: Authentication failed
        API-->>Client: 401 Unauthorized
        Client->>User: Show error message
    end
    deactivate Client
    
    rect rgb(200, 255, 200)
        Note over Client,API: Subsequent authenticated requests
        Client->>+API: Request + Bearer token
        API->>API: Validate token
        API-->>-Client: Protected resource
    end
```

INPUT TO PROCESS:
{content}

REQUIREMENTS:
- Include autonumber: {autonumber}
- Show activations: {show_activations}
- Use notes: {use_notes}

Return the formatted Mermaid sequence diagram."""


# =============================================================================
# CLASS DIAGRAM PROMPTS
# =============================================================================

MERMAID_CLASS_PROMPT = """Generate a Mermaid class diagram (UML).

CLASS DIAGRAM SYNTAX REFERENCE:
================================

1. DIAGRAM DECLARATION:
   classDiagram

2. CLASS DEFINITION:
   class ClassName {
       +publicAttribute : Type
       -privateAttribute : Type
       #protectedAttribute : Type
       ~packageAttribute : Type
       +publicMethod() ReturnType
       -privateMethod(param: Type) ReturnType
       +abstractMethod()* ReturnType
       +staticMethod()$ ReturnType
   }

3. VISIBILITY MODIFIERS:
   - +  → Public
   - -  → Private
   - #  → Protected
   - ~  → Package/Internal

4. ANNOTATIONS/STEREOTYPES:
   class Shape {
       <<abstract>>
       +draw()
   }
   
   class IDrawable {
       <<interface>>
       +draw()
   }
   
   class UserService {
       <<service>>
       +getUser()
   }

5. RELATIONSHIPS:
   - A <|-- B       → Inheritance (B extends A)
   - A *-- B        → Composition (A contains B, strong)
   - A o-- B        → Aggregation (A has B, weak)
   - A --> B        → Association (A uses B)
   - A ..> B        → Dependency (A depends on B)
   - A ..|> B       → Realization (B implements A)
   - A -- B         → Link (bidirectional)

6. CARDINALITY:
   - A "1" --> "0..*" B    → One to many
   - A "1" --> "1" B       → One to one
   - A "0..1" --> "*" B    → Zero-or-one to many

7. LABELS ON RELATIONSHIPS:
   A --> B : uses
   A "1" --> "*" B : contains

8. NAMESPACES:
   namespace Utilities {
       class Logger
       class Config
   }

BEST PRACTICES:
===============
- Use meaningful class names (PascalCase)
- Show visibility for all members
- Include type annotations
- Use stereotypes for interfaces/abstracts
- Show cardinality for associations
- Group related classes visually
- Limit inheritance depth to 3-4 levels
- Prefer composition over inheritance
- Keep diagrams focused (5-10 classes)

EXAMPLE - Design Pattern (Factory):
```mermaid
classDiagram
    class Product {
        <<interface>>
        +operation() String
    }
    
    class ConcreteProductA {
        +operation() String
    }
    
    class ConcreteProductB {
        +operation() String
    }
    
    class Creator {
        <<abstract>>
        +factoryMethod()* Product
        +someOperation() String
    }
    
    class ConcreteCreatorA {
        +factoryMethod() Product
    }
    
    class ConcreteCreatorB {
        +factoryMethod() Product
    }
    
    Product <|.. ConcreteProductA : implements
    Product <|.. ConcreteProductB : implements
    Creator <|-- ConcreteCreatorA : extends
    Creator <|-- ConcreteCreatorB : extends
    Creator --> Product : creates
    ConcreteCreatorA ..> ConcreteProductA : creates
    ConcreteCreatorB ..> ConcreteProductB : creates
```

INPUT TO PROCESS:
{content}

REQUIREMENTS:
- Show visibility: {show_visibility}
- Include methods: {include_methods}
- Show relationships: {show_relationships}

Return the formatted Mermaid class diagram."""


# =============================================================================
# STATE DIAGRAM PROMPTS
# =============================================================================

MERMAID_STATE_PROMPT = """Generate a Mermaid state diagram.

STATE DIAGRAM SYNTAX REFERENCE:
================================

1. DIAGRAM DECLARATION:
   stateDiagram-v2

2. STATE DEFINITIONS:
   - state "State Name" as stateId
   - state stateId
   - [*] → Initial/Final state

3. TRANSITIONS:
   - stateA --> stateB           → Simple transition
   - stateA --> stateB : event   → Labeled transition
   - stateA --> stateB : event [guard] / action

4. COMPOSITE STATES:
   state CompositeState {
       [*] --> SubStateA
       SubStateA --> SubStateB
       SubStateB --> [*]
   }

5. FORK AND JOIN (Concurrency):
   state fork_state <<fork>>
   state join_state <<join>>
   
   [*] --> fork_state
   fork_state --> State1
   fork_state --> State2
   State1 --> join_state
   State2 --> join_state
   join_state --> [*]

6. CHOICE (Decision):
   state if_state <<choice>>
   
   [*] --> if_state
   if_state --> StateA : condition1
   if_state --> StateB : condition2

7. NOTES:
   note right of StateA : This is a note
   note left of StateB
       Multi-line note
       continues here
   end note

BEST PRACTICES:
===============
- Always include initial state [*]
- Use descriptive state names
- Label all transitions with events
- Group related states in composites
- Use choice for decision points
- Use fork/join for parallel states
- Add notes for complex states
- Keep transitions unambiguous
- Show final states where applicable

EXAMPLE - Order Processing State Machine:
```mermaid
stateDiagram-v2
    [*] --> Pending : order_created
    
    state Pending {
        [*] --> AwaitingPayment
        AwaitingPayment --> PaymentReceived : payment_received
        AwaitingPayment --> [*] : timeout
    }
    
    Pending --> Processing : payment_confirmed
    
    state Processing {
        [*] --> Validating
        Validating --> Preparing : valid
        Validating --> Rejected : invalid
        Preparing --> ReadyToShip : prepared
    }
    
    Processing --> Shipped : dispatch
    
    state Shipped {
        [*] --> InTransit
        InTransit --> OutForDelivery : arrived_local
        OutForDelivery --> Delivered : delivered
    }
    
    Shipped --> Delivered : delivery_confirmed
    Delivered --> [*]
    
    state Rejected {
        [*] --> RefundPending
        RefundPending --> Refunded : refund_processed
        Refunded --> [*]
    }
    
    note right of Processing
        Warehouse operations
        typically take 1-3 days
    end note
```

INPUT TO PROCESS:
{content}

REQUIREMENTS:
- Include composite states: {use_composites}
- Show initial/final: {show_terminals}
- Add notes: {add_notes}

Return the formatted Mermaid state diagram."""


# =============================================================================
# ER DIAGRAM PROMPTS
# =============================================================================

MERMAID_ER_PROMPT = """Generate a Mermaid Entity-Relationship diagram.

ER DIAGRAM SYNTAX REFERENCE:
=============================

1. DIAGRAM DECLARATION:
   erDiagram

2. ENTITY DEFINITION:
   ENTITY_NAME {
       type attribute_name PK "comment"
       type attribute_name FK "comment"
       type attribute_name UK "unique"
       type attribute_name
   }

3. DATA TYPES (Common):
   - string, varchar, text, char
   - int, integer, bigint, smallint
   - float, double, decimal, numeric
   - date, datetime, timestamp, time
   - boolean, bool
   - uuid, binary, blob

4. CONSTRAINTS:
   - PK → Primary Key
   - FK → Foreign Key
   - UK → Unique Key

5. RELATIONSHIPS:
   - |o--o|  → Zero or one to zero or one
   - ||--o|  → Exactly one to zero or one
   - |o--|{  → Zero or one to one or more
   - ||--|{  → Exactly one to one or more
   - }o--o{  → Zero or more to zero or more
   - }|--|{  → One or more to one or more

6. RELATIONSHIP CARDINALITY SYMBOLS:
   - |  → One (exactly)
   - o  → Zero
   - {  → Many
   - }  → Many

7. LABELED RELATIONSHIPS:
   CUSTOMER ||--o{ ORDER : places
   ORDER ||--|{ LINE_ITEM : contains
   PRODUCT ||--o{ LINE_ITEM : "is part of"

BEST PRACTICES:
===============
- Use UPPERCASE for entity names
- Use snake_case for attributes
- Always define primary keys
- Show foreign keys explicitly
- Use meaningful relationship labels
- Include data types for all attributes
- Add comments for complex attributes
- Group related entities visually
- Normalize to 3NF minimum

EXAMPLE - E-Commerce Database Schema:
```mermaid
erDiagram
    CUSTOMER {
        uuid customer_id PK "Primary identifier"
        string email UK "Unique email"
        string first_name
        string last_name
        string password_hash
        datetime created_at
        datetime updated_at
        boolean is_active
    }
    
    ADDRESS {
        uuid address_id PK
        uuid customer_id FK "References CUSTOMER"
        string street_line1
        string street_line2
        string city
        string state
        string postal_code
        string country
        string address_type "billing/shipping"
    }
    
    ORDER {
        uuid order_id PK
        uuid customer_id FK
        uuid shipping_address_id FK
        uuid billing_address_id FK
        decimal total_amount
        string status "pending/confirmed/shipped/delivered"
        datetime order_date
        datetime shipped_date
    }
    
    ORDER_ITEM {
        uuid item_id PK
        uuid order_id FK
        uuid product_id FK
        int quantity
        decimal unit_price
        decimal discount
    }
    
    PRODUCT {
        uuid product_id PK
        string sku UK
        string name
        text description
        decimal price
        int stock_quantity
        uuid category_id FK
        boolean is_available
    }
    
    CATEGORY {
        uuid category_id PK
        string name UK
        string slug UK
        uuid parent_category_id FK "Self-reference for hierarchy"
        int display_order
    }
    
    CUSTOMER ||--o{ ADDRESS : "has"
    CUSTOMER ||--o{ ORDER : "places"
    ORDER ||--|{ ORDER_ITEM : "contains"
    PRODUCT ||--o{ ORDER_ITEM : "included in"
    CATEGORY ||--o{ PRODUCT : "categorizes"
    CATEGORY ||--o{ CATEGORY : "parent of"
    ADDRESS ||--o{ ORDER : "ships to"
```

INPUT TO PROCESS:
{content}

REQUIREMENTS:
- Include data types: {include_types}
- Show constraints: {show_constraints}
- Add comments: {add_comments}

Return the formatted Mermaid ER diagram."""


# =============================================================================
# GANTT CHART PROMPTS
# =============================================================================

MERMAID_GANTT_PROMPT = """Generate a Mermaid Gantt chart.

GANTT CHART SYNTAX REFERENCE:
==============================

1. DIAGRAM DECLARATION:
   gantt
       title Project Timeline
       dateFormat YYYY-MM-DD

2. DATE FORMATS:
   - dateFormat YYYY-MM-DD    → 2024-01-15
   - dateFormat DD-MM-YYYY    → 15-01-2024
   - dateFormat YYYY-MM-DD HH:mm → With time

3. AXIS FORMAT:
   axisFormat %m/%d    → Month/Day
   axisFormat %Y-%m    → Year-Month
   axisFormat %d       → Day only

4. SECTIONS:
   section Section Name
       Task 1 : a1, 2024-01-01, 30d
       Task 2 : a2, after a1, 20d

5. TASK DEFINITION:
   Task Name : taskId, startDate, duration
   Task Name : taskId, startDate, endDate
   Task Name : taskId, after otherId, duration

6. TASK MODIFIERS:
   - done      → Completed task
   - active    → Currently active
   - crit      → Critical path
   - milestone → Zero-duration milestone

7. DEPENDENCIES:
   Task B : b1, after a1, 10d        → After single task
   Task C : c1, after a1 b1, 5d      → After multiple tasks

8. EXCLUDES:
   excludes weekends
   excludes 2024-12-25, 2024-12-26

BEST PRACTICES:
===============
- Always include title and dateFormat
- Group related tasks in sections
- Use meaningful task IDs
- Show dependencies explicitly
- Mark critical path tasks
- Include milestones for key dates
- Exclude holidays/weekends if relevant
- Keep duration realistic
- Show parallel tracks where applicable

EXAMPLE - Software Development Sprint:
```mermaid
gantt
    title Sprint 23 - User Authentication Feature
    dateFormat YYYY-MM-DD
    axisFormat %m/%d
    excludes weekends
    
    section Planning
        Sprint Planning       : done, plan1, 2024-01-15, 1d
        Technical Design      : done, design1, 2024-01-16, 2d
        Design Review         : milestone, m1, after design1, 0d
    
    section Backend Development
        API Design            : done, api1, after design1, 2d
        Auth Service          : active, auth1, after api1, 4d
        Database Schema       : done, db1, after api1, 2d
        JWT Implementation    : crit, jwt1, after auth1, 3d
        Unit Tests            : test1, after jwt1, 2d
    
    section Frontend Development
        UI Components         : ui1, after design1, 4d
        Login Form            : login1, after ui1, 3d
        Registration Flow     : reg1, after login1, 3d
        Integration           : crit, int1, after test1 reg1, 2d
    
    section Quality Assurance
        Integration Testing   : qa1, after int1, 3d
        Security Audit        : crit, sec1, after qa1, 2d
        Bug Fixes             : fix1, after sec1, 2d
        Final Review          : milestone, m2, after fix1, 0d
    
    section Deployment
        Staging Deploy        : stage1, after m2, 1d
        Production Deploy     : crit, prod1, after stage1, 1d
        Release               : milestone, m3, after prod1, 0d
```

INPUT TO PROCESS:
{content}

REQUIREMENTS:
- Date format: {date_format}
- Include milestones: {include_milestones}
- Show critical path: {show_critical}

Return the formatted Mermaid Gantt chart."""


# =============================================================================
# PIE CHART PROMPTS
# =============================================================================

MERMAID_PIE_PROMPT = """Generate a Mermaid pie chart.

PIE CHART SYNTAX REFERENCE:
============================

1. BASIC DECLARATION:
   pie title Chart Title
       "Label 1" : value1
       "Label 2" : value2

2. WITH DATA VALUES:
   pie showData
       title Chart Title
       "Label 1" : 45
       "Label 2" : 30

3. OPTIONS:
   - showData → Display percentage/values on chart

4. VALUE FORMATTING:
   - Values can be integers or decimals
   - Values are automatically converted to percentages
   - Total doesn't need to equal 100

BEST PRACTICES:
===============
- Always include a descriptive title
- Use clear, concise labels
- Limit to 5-7 slices maximum
- Order slices by size (largest first)
- Use "Other" for small categories
- Include showData for clarity
- Ensure labels are readable
- Values should be meaningful

EXAMPLE - Budget Allocation:
```mermaid
pie showData
    title Q4 2024 Budget Distribution
    "Engineering" : 42
    "Marketing" : 25
    "Operations" : 18
    "Research" : 10
    "Other" : 5
```

EXAMPLE - Survey Results:
```mermaid
pie showData
    title Customer Satisfaction Survey
    "Very Satisfied" : 45
    "Satisfied" : 30
    "Neutral" : 15
    "Dissatisfied" : 7
    "Very Dissatisfied" : 3
```

INPUT TO PROCESS:
{content}

REQUIREMENTS:
- Show data values: {show_data}
- Include title: {include_title}

Return the formatted Mermaid pie chart."""


# =============================================================================
# MINDMAP PROMPTS
# =============================================================================

MERMAID_MINDMAP_PROMPT = """Generate a Mermaid mind map.

MINDMAP SYNTAX REFERENCE:
==========================

1. BASIC DECLARATION:
   mindmap
       root((Central Topic))

2. NODE SHAPES:
   - ((Circle))      → Circle/rounded
   - [Square]        → Square
   - (Rounded)       → Rounded rectangle
   - ))Cloud((       → Cloud shape
   - {{Hexagon}}     → Hexagon

3. HIERARCHY:
   - Indentation defines levels
   - 2 spaces per level recommended
   - Maximum 6-7 levels for readability

4. ICONS (FontAwesome):
   - ::icon(fa fa-book)
   - ::icon(fa fa-user)

BEST PRACTICES:
===============
- Start with clear central topic
- Limit to 3-5 main branches
- Use 2-4 sub-branches per branch
- Keep labels concise (1-3 words)
- Use consistent indentation
- Order branches logically
- Use shapes to differentiate levels
- Add icons for visual appeal
- Balance branch sizes

EXAMPLE - Machine Learning Concepts:
```mermaid
mindmap
    root((Machine Learning))
        Supervised Learning
            Classification
                Binary
                Multi-class
                Multi-label
            Regression
                Linear
                Polynomial
                Logistic
        Unsupervised Learning
            Clustering
                K-Means
                Hierarchical
                DBSCAN
            Dimensionality Reduction
                PCA
                t-SNE
                UMAP
        Reinforcement Learning
            Model-Based
                Dynamic Programming
                Monte Carlo
            Model-Free
                Q-Learning
                Policy Gradient
                Actor-Critic
        Deep Learning
            Neural Networks
                CNN
                RNN
                Transformer
            Applications
                NLP
                Computer Vision
                Speech
```

INPUT TO PROCESS:
{content}

REQUIREMENTS:
- Max depth: {max_depth}
- Use icons: {use_icons}
- Node shapes: {node_shapes}

Return the formatted Mermaid mind map."""


# =============================================================================
# VALIDATION PROMPT
# =============================================================================

MERMAID_VALIDATION_PROMPT = """Validate the following Mermaid diagram for correctness.

VALIDATION CHECKLIST:
=====================

1. STRUCTURE VALIDATION:
   □ Diagram type declared correctly
   □ Proper code block formatting
   □ Consistent indentation
   □ No orphan elements

2. SYNTAX VALIDATION:
   □ Valid node IDs (no spaces, special chars)
   □ Balanced brackets and quotes
   □ Proper arrow syntax
   □ Valid keywords used

3. LOGIC VALIDATION:
   □ All referenced nodes exist
   □ No circular dependencies (where invalid)
   □ Relationships make sense
   □ Labels are complete

4. RENDERING VALIDATION:
   □ Will render without errors
   □ Readable layout expected
   □ No overlapping elements expected

DIAGRAM TO VALIDATE:
{content}

Return JSON with:
{
    "is_valid": true/false,
    "diagram_type": "detected type",
    "errors": ["error1", "error2"],
    "warnings": ["warning1"],
    "suggestions": ["suggestion1"],
    "corrected_content": "fixed diagram if needed"
}"""
