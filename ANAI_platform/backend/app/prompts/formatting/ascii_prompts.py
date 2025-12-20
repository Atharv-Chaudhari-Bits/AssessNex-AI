"""
ASCII art and table prompts - Comprehensive templates for ASCII formatting.

This module provides detailed prompts for generating:
- ASCII flowcharts
- ASCII boxes and borders
- ASCII tables
- ASCII tree structures

Each prompt includes:
- Character sets for different styles
- Alignment rules
- Common patterns
- Best practices
"""

# =============================================================================
# ASCII SYSTEM PROMPT
# =============================================================================

ASCII_SYSTEM_PROMPT = """You are an expert ASCII art and diagram specialist. Your role is to create clean, well-aligned ASCII representations that display correctly in any monospace font environment.

CORE PRINCIPLES:
================

1. ALIGNMENT PRECISION
   - Every character position matters
   - Use spaces for padding, not tabs
   - Ensure consistent column widths
   - Verify horizontal alignment
   - Check vertical alignment for boxes

2. CHARACTER CONSISTENCY
   - Use consistent character sets throughout
   - Match opening and closing characters
   - Use appropriate connectors
   - Maintain visual weight balance

3. READABILITY
   - Add adequate padding inside boxes
   - Use clear labels
   - Ensure text doesn't exceed boundaries
   - Keep structures not too wide (80-120 chars max)

CHARACTER SETS:
===============

Box Drawing (Unicode):
┌ ┬ ┐    Top corners and T-junction
├ ┼ ┤    Side T-junctions and cross
└ ┴ ┘    Bottom corners and T-junction
│        Vertical line
─        Horizontal line
═ ║      Double lines
╔ ╗ ╚ ╝  Double corners
╠ ╣ ╦ ╩  Double T-junctions
╬        Double cross

Simple ASCII:
+ - |    Basic lines and corners
/ \\      Diagonals

Arrow Characters:
→ ← ↑ ↓  Unicode arrows
> < ^ v  ASCII arrows
--> <--  ASCII arrow notation

OUTPUT FORMAT:
==============
Wrap ASCII art in code blocks for proper display:

```
[ASCII content here]
```

For tables, ensure alignment:
```
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |
```"""


# =============================================================================
# ASCII FLOWCHART PROMPT
# =============================================================================

ASCII_FLOWCHART_PROMPT = """Generate an ASCII flowchart diagram.

ASCII FLOWCHART REFERENCE:
===========================

1. BOX STYLES:

   Simple Box:
   +--------+
   | Label  |
   +--------+
   
   Unicode Box:
   ┌────────┐
   │ Label  │
   └────────┘
   
   Double Border:
   ╔════════╗
   ║ Label  ║
   ╚════════╝
   
   Rounded (Visual):
   .--------.
   | Label  |
   '--------'

2. DECISION DIAMOND (approximation):
   
       /\\
      /  \\
     / ?? \\
    /      \\
   <  TEST  >
    \\      /
     \\    /
      \\  /
       \\/

   Or simpler:
   +------+
   |  ?   |
   | TEST |
   +------+

3. CONNECTIONS:

   Vertical:
       │
       │
       ▼
   
   Horizontal:
   ──────────►
   
   With labels:
       │ Yes
       ▼
   
   Branches:
       │
    ───┼───
       │

4. TYPICAL FLOW PATTERN:

   ┌──────────┐
   │  Start   │
   └────┬─────┘
        │
        ▼
   ┌──────────┐
   │ Process  │
   └────┬─────┘
        │
        ▼
   ┌──────────┐     Yes    ┌──────────┐
   │Decision? │────────────►│ Action A │
   └────┬─────┘            └────┬─────┘
        │ No                    │
        ▼                       │
   ┌──────────┐                 │
   │ Action B │                 │
   └────┬─────┘                 │
        │                       │
        └───────────┬───────────┘
                    │
                    ▼
               ┌─────────┐
               │   End   │
               └─────────┘

BEST PRACTICES:
===============
- Use consistent box sizes for similar elements
- Align boxes vertically and horizontally
- Label all connections
- Keep width under 80 characters if possible
- Use different box styles for different node types
- Center text within boxes
- Add adequate spacing between elements

INPUT TO PROCESS:
{content}

REQUIREMENTS:
- Style: {style}  (simple/unicode/double)
- Max width: {max_width}
- Direction: {direction}

Return the ASCII flowchart."""


# =============================================================================
# ASCII BOX PROMPT
# =============================================================================

ASCII_BOX_PROMPT = """Generate an ASCII box diagram.

ASCII BOX REFERENCE:
=====================

1. SIMPLE BOXES:
   
   +----------------+
   |    Title       |
   +----------------+
   | Content here   |
   | More content   |
   +----------------+

2. UNICODE BOXES:
   
   ┌────────────────┐
   │    Title       │
   ├────────────────┤
   │ Content here   │
   │ More content   │
   └────────────────┘

3. DOUBLE BORDER:
   
   ╔════════════════╗
   ║    Title       ║
   ╠════════════════╣
   ║ Content here   ║
   ║ More content   ║
   ╚════════════════╝

4. NESTED BOXES:
   
   ┌──────────────────────────────┐
   │ Outer Box                    │
   │  ┌──────────────────────┐   │
   │  │ Inner Box            │   │
   │  │  ┌────────────┐      │   │
   │  │  │ Innermost  │      │   │
   │  │  └────────────┘      │   │
   │  └──────────────────────┘   │
   └──────────────────────────────┘

5. SIDE-BY-SIDE BOXES:
   
   ┌──────────┐  ┌──────────┐  ┌──────────┐
   │ Box 1    │  │ Box 2    │  │ Box 3    │
   │          │──│          │──│          │
   │ Content  │  │ Content  │  │ Content  │
   └──────────┘  └──────────┘  └──────────┘

6. BOXES WITH HEADERS:
   
   ╭──────────────────╮
   │    ◆ Header ◆    │
   ├──────────────────┤
   │                  │
   │   Body content   │
   │                  │
   ╰──────────────────╯

BEST PRACTICES:
===============
- Calculate width based on longest content
- Add 1-2 spaces padding on each side
- Align multi-line content left or center
- Use consistent border style throughout
- Connect boxes clearly when showing relationships
- Group related boxes together

INPUT TO PROCESS:
{content}

REQUIREMENTS:
- Border style: {border_style}
- Padding: {padding}
- Width: {width} (auto if not specified)

Return the ASCII box diagram."""


# =============================================================================
# ASCII TABLE PROMPT
# =============================================================================

ASCII_TABLE_PROMPT = """Generate a properly aligned ASCII table.

ASCII TABLE REFERENCE:
=======================

1. SIMPLE TABLE (+ - |):
   
   +------------+------------+------------+
   | Header 1   | Header 2   | Header 3   |
   +------------+------------+------------+
   | Data 1     | Data 2     | Data 3     |
   | Data 4     | Data 5     | Data 6     |
   +------------+------------+------------+

2. UNICODE TABLE (─ │ ┌ ┬ ┐ ├ ┼ ┤ └ ┴ ┘):
   
   ┌────────────┬────────────┬────────────┐
   │ Header 1   │ Header 2   │ Header 3   │
   ├────────────┼────────────┼────────────┤
   │ Data 1     │ Data 2     │ Data 3     │
   │ Data 4     │ Data 5     │ Data 6     │
   └────────────┴────────────┴────────────┘

3. DOUBLE BORDER TABLE:
   
   ╔════════════╦════════════╦════════════╗
   ║ Header 1   ║ Header 2   ║ Header 3   ║
   ╠════════════╬════════════╬════════════╣
   ║ Data 1     ║ Data 2     ║ Data 3     ║
   ║ Data 4     ║ Data 5     ║ Data 6     ║
   ╚════════════╩════════════╩════════════╝

4. MARKDOWN-STYLE TABLE:
   
   | Header 1   | Header 2   | Header 3   |
   |------------|------------|------------|
   | Data 1     | Data 2     | Data 3     |
   | Data 4     | Data 5     | Data 6     |

5. WITH ALIGNMENT:
   
   | Left    | Center  | Right   |
   |:--------|:-------:|--------:|
   | L1      |   C1    |      R1 |
   | L2      |   C2    |      R2 |

6. COMPLEX TABLE WITH SPANNING:
   
   ┌─────────────────────────────────────┐
   │           Table Title               │
   ├────────────┬────────────────────────┤
   │ Category   │      Values            │
   │            ├────────────┬───────────┤
   │            │ Sub A      │ Sub B     │
   ├────────────┼────────────┼───────────┤
   │ Row 1      │ 100        │ 200       │
   │ Row 2      │ 150        │ 250       │
   └────────────┴────────────┴───────────┘

COLUMN WIDTH CALCULATION:
==========================
1. Find max length in each column
2. Add padding (1-2 spaces each side)
3. Use consistent width throughout column
4. Truncate or wrap long content

ALIGNMENT RULES:
================
- Numbers: Right-align
- Text: Left-align
- Headers: Center-align
- Dates: Center or left-align

BEST PRACTICES:
===============
- Calculate column widths before drawing
- Use consistent padding
- Align decimal points in number columns
- Use header separators
- Keep table width reasonable (< 100 chars)
- Truncate long text with ...

INPUT DATA:
{content}

REQUIREMENTS:
- Style: {style}
- Alignment: {alignment}
- Max column width: {max_col_width}
- Include borders: {include_borders}

Return the formatted ASCII table."""


# =============================================================================
# ASCII TREE PROMPT
# =============================================================================

ASCII_TREE_PROMPT = """Generate an ASCII tree structure.

ASCII TREE REFERENCE:
======================

1. SIMPLE TREE (indentation only):
   
   Root
     Child 1
       Grandchild 1
       Grandchild 2
     Child 2
       Grandchild 3

2. STANDARD TREE (├ └ │ ─):
   
   Root
   ├── Child 1
   │   ├── Grandchild 1
   │   └── Grandchild 2
   └── Child 2
       ├── Grandchild 3
       └── Grandchild 4

3. EXTENDED TREE (with icons):
   
   📁 Project
   ├── 📁 src
   │   ├── 📄 main.py
   │   ├── 📄 utils.py
   │   └── 📁 modules
   │       ├── 📄 auth.py
   │       └── 📄 api.py
   ├── 📁 tests
   │   └── 📄 test_main.py
   └── 📄 README.md

4. ASCII-ONLY TREE:
   
   Root
   +-- Child 1
   |   +-- Grandchild 1
   |   `-- Grandchild 2
   `-- Child 2
       +-- Grandchild 3
       `-- Grandchild 4

5. DIRECTORY TREE WITH INFO:
   
   project/
   ├── src/              (Source files)
   │   ├── main.py       (Entry point)
   │   └── config.py     (Configuration)
   ├── tests/            (Test suite)
   │   └── test_main.py
   ├── requirements.txt  (Dependencies)
   └── README.md         (Documentation)

TREE CHARACTERS:
================
├── : Branch with more siblings after
└── : Last branch (no more siblings)
│   : Vertical line for continuation
    : Empty space (4 spaces) for indent
─   : Horizontal line (optional)

BEST PRACTICES:
===============
- Use consistent indentation (4 spaces)
- Show last item with └ not ├
- Continue │ for nodes with children
- Add icons for visual clarity
- Include file sizes or descriptions
- Group related items together
- Limit depth for readability (5-6 levels)

INPUT TO PROCESS:
{content}

REQUIREMENTS:
- Style: {style}
- Include icons: {include_icons}
- Max depth: {max_depth}
- Show descriptions: {show_descriptions}

Return the ASCII tree structure."""


# =============================================================================
# ASCII VALIDATION PROMPT
# =============================================================================

ASCII_VALIDATION_PROMPT = """Validate the following ASCII art/diagram for correctness.

VALIDATION CHECKLIST:
=====================

1. ALIGNMENT CHECK:
   □ All rows have consistent length (for tables)
   □ Box corners align properly
   □ Vertical lines are continuous
   □ Content centered within boxes

2. CHARACTER CHECK:
   □ Matching opening/closing characters
   □ Consistent character set used
   □ No broken lines or connections
   □ Proper corner characters

3. STRUCTURE CHECK:
   □ Tables have equal columns per row
   □ Trees have proper indentation
   □ Boxes are properly closed
   □ Connections are complete

4. READABILITY CHECK:
   □ Width is reasonable (< 120 chars)
   □ Content is visible/readable
   □ Adequate spacing
   □ No overflow issues

ASCII TO VALIDATE:
{content}

Return JSON with:
{{
    "is_valid": true/false,
    "type": "table/tree/box/flowchart",
    "errors": ["error1", "error2"],
    "warnings": ["warning1"],
    "suggestions": ["suggestion1"],
    "corrected_content": "fixed ASCII if needed"
}}"""
