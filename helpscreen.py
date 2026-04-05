from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.containers import Center, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static, Markdown, Footer, MarkdownViewer


HELP_MARKDOWN = """
A CSV editor with minimal spreadsheet capabilities for the terminal.

Built with [Textual](https://www.textualize.io/)

Repository: 
  
  https://github.com/xqtr/termcell

Author:
  
  XQTR // https://cp737.net

--- 

### Command Mode (press `:`)

Press `.` (period) to repeat last command

#### File Operations
- `:w` or `:write` - Save file
- `:w filename` - Save as filename
- `:wd` - Open Save File Dialog
- `:q` or `:quit` - Quit
- `:q!` or `:quit!` - Force quit without saving
- `:wq` - Save and quit
- `:e filename` - Edit file
- `:ed` - Open File Dialog
- `:new` - New file
- `:r` or `:reload` - Reload File
- `:r!` - Force Reload File
- `:f` or `:file` - File Information


#### Navigation
- `:n` or `:next` - Next row
- `:prev` or `:previous` - Previous row
- `:first` - First row
- `:last` - Last row

#### Config
- `:set number_width=<number_width>` - Sets the width of the numbering column
- `:set delimiter=<char> - Sets the delimiter character. `:set delimiter=;`


#### Display
- `:tt` - Toggle Theme (may not work in older Textual version)
- `ctrl+\` - Theme Selector (may not work in newer Textual version)


#### Functions

- `:calc` - Perform formula calculations and variable substitutions
- `:fill` <cell|area> <string> - Fills the cell(s) with the given string

- `:lower` <cell|area> - Convert text of cell to lower case
- `:upper` <cell|area> - Convert text of cell to upper case
- `:title` <cell|area> - Convert text of cell to title case
- `:strip` <cell|area> - Strip text of cells
- `:capitalize` <cell|area> - Capitalize text of cells
- `:isalpha` <cell|area> - Returns True if cell value is text only
- `:swapcase` <cell|area> - Toggles the case of cells
- `:isalnum` <cell|area> - Returns True if cell value is alphanumeric
- `:isascii` <cell|area> - Returns True if cell value is ascii chars.
- `:isdecimal` <cell|area> - Returns True if cell value is numerical
- `:isdigit` <cell|area> - Returns True if cell value is numerical
- `:islower` <cell|area> - Returns True if cell value is lower case
- `:isnumeric` <cell|area> - Returns True if cell value is numeric
- `:isprintable` <cell|area> - Returns True if cell value is printable characters
- `:isspace` <cell|area> - Returns True if cell value is only space
- `:istitle` <cell|area> - Returns True if cell text is in Title case
- `:isupper` <cell|area> - Returns True if cell text is in Upper case
- `:lstrip' <cell|area> | Left strips text of cells

---

## Data

### Sort Column
| Keys | Action |
|------|--------|
| `sa`  | Sort Asceding |
| `sd`  | Sort Descending |

---

## Navigation

### Basic Movement
| Keys | Action |
|------|--------|
| `h` / `l` | Move left / right |
| `j` / `k` | Move down / up |
| `2h` / `3l` | Move 2 left / 3 right (with count prefix) |
| `H` / `L` | Go to first/last column |
| `J` / `K` | Go to first/last row |

### Advanced Navigation
| Keys | Action |
|------|--------|
| `gr` | Go to specific row (prompt) |
| `gc` | Go to specific column (prompt) |
| `gg` | Go to first cell |
| `G` | Go to last cell |

---

## Editing
### Cell Operations
| Keys | Action |
|------|--------|
| `Enter` on cell | Edit cell value |
| `Esc` | Cancel edit / Clear key buffer |
| `.` (period) | Repeat last command |

### Insert/Append
| Keys | Action |
|------|--------|
| `ir` / `ic` | Insert row/column at cursor |
| `ar` / `ac` | Append row/column at end |
| `2ir` | Insert 2 rows (with count prefix) |

### Delete/Remove
| Keys | Action |
|------|--------|
| `dr` / `dc` | Delete current row/column |
| `3dr` | Delete 3 rows (with count prefix) |
| `dd` | Cut selection (copy + clear) |

---

## Selection & Modes
### Cursor Modes
| Keys | Action |
|------|--------|
| `cl` | Cell mode (select single cell) |
| `cr` | Row mode (select entire row) |
| `cc` | Column mode (select entire column) |

### Copy/Paste
| Keys | Action |
|------|--------|
| `yy` | Yank (copy) selection |
| `pp` | Paste from clipboard |
| `dd` | Cut (delete + copy) |
| `P` | Paste with overwrite |

---

## Search & Find
| Keys | Action |
|------|--------|
| `/` | Search forward |
| `?` | Search backward |
| `n` | Next match |
| `N` | Previous match |
| `Enter` in search | Execute search |
| `Esc` in search | Cancel search |

---

## View & Display
### Table Display
| Keys | Action |
|------|--------|
| `sh` | Toggle header visibility |
| `sz` | Toggle zebra stripes |
| `sc` | Toggle cursor visibility |
| `wa` | Auto-adjust column widths |
| `wr` | Reset all column widths |
| `wc` | Set column width |
| `fr` / `fc` | Set fixed rows/columns |

### Themes
| Keys | Action |
|------|--------|
| `tt` | Toggle theme (light/dark) |

---

## Formula Support

### Basic Formulas

```
=SUM(A1:A10) # Sum range
=AVG(B1:B5) # Average range
=MAX(C1:C20) # Maximum value
=MIN(D1:D15) # Minimum value
=COUNT(E1:E100) # Count non-empty cells
```

### Cell References
- `$A1`- Single cell
- `$A1:B10` or `A1:B10` - Range

---

## Search

- `/` - Search forward
- `?` - Search backward
- `n` - Next match (while in search mode)
- `N` - Previous match (Shift+N while in search mode)

#### Search Usage:
1. Press `/` or `?` to start search
2. Type search pattern
3. Press Enter to search
4. Use `n`/`N` to navigate matches
5. Press Esc to cancel search


## Cell Variables

Insert these variables in any cell and run `:calc` to replace them with actual values:

#### Date & Time Variables:
- `$date` / `$today` - Current date (YYYY-MM-DD)
- `$time` - Current time (HH:MM:SS)
- `$now` / `$datetime` - Current date & time (YYYY-MM-DD HH:MM:SS)
- `$timestamp` - ISO format timestamp
- `$tomorrow` - Date tomorrow (YYYY-MM-DD)
- `$yesterday` - Date yesterday (YYYY-MM-DD)
- `$weekday` - Day of week (e.g., "Monday")
- `$month` - Month name (e.g., "January")
- `$year` - Current year
- `$hour` - Current hour (0-23)
- `$minute` - Current minute (0-59)
- `$second` - Current second (0-59)

#### Random & Generated Data:
- `$random` / `$randomint` - Random integer between 1-100
- `$randomfloat` - Random decimal between 0-1
- `$randombool` - Random TRUE or FALSE
- `$uuid` - Universally Unique Identifier (UUID v4)

#### System & Environment:
- `$cwd` - Current working directory
- `$home` - User home directory

#### Mathematical Constants:
- `$pi` - π (pi, approximately 3.141592653589793)
- `$e` - Euler's number (approximately 2.718281828459045)

#### Formatting Characters:
- `$tab` - Tab character
- `$newline` - Newline character
- `$comma` - Comma character
- `$pipe` - Pipe character (|)
- `$quote` - Double quote character (")
- `$space` - Space character
- `$dash` - Dash/hyphen character

#### Usage Examples:
1. Type `Report generated on $date at $time` in a cell
2. Run `:calc` command
3. Becomes: `Report generated on 2024-01-15 at 14:30:45`

#### Notes:
- Variables are case-sensitive (`$date` works, `$DATE` doesn't)
- Use `:calc` to replace ALL variables in the entire table
- Variables work in any cell, including within text
- After replacement, values become static text

### Quick Reference: Special Variables

**Date:** `$date`, `$time`, `$now`, `$timestamp`
**Random:** `$random`, `$randomfloat`, `$randombool`, `$uuid`
**System:** `$cwd`, `$home`
**Constants:** `$pi`, `$e`
**Formatting:** `$tab`, `$newline`, `$comma`, `$pipe`, `$quote`

Use `:calc` to replace all variables with values.

## Command Line Options

CSV delimiter character (default: ,)
`-d DELIMITER, --delimiter DELIMITER`

Use tab as delimiter (overrides -d)
`-t, --tab`
  
Examples:
```
termcell --delimiter=";" data.csv
termcell --tab data.tsv
```

---


# Math Expression Syntax

Below described the **supported syntax** for the AST-based math
expression evaluator. 

The evaluator implements a **strict mathematical expression language**.
Anything outside this language is rejected.

---

To enter a mathematical expression in a cell, use this syntax:

`=(expression)`

For the program to recognize the string as a math.expression to calculate,
it must start with `=(` and end with `)`. Inside you can input any of the
functions mentioned below, as well cell references like `$A10` or program
variables.

### Examples

`=($A1 + $A2 + $A3)`
`=(sin($B1)*pi)`

---

## Overview

The expression parser supports:

- Numeric literals (integers and floats)
- Mathematical operators
- Parentheses for grouping
- A curated set of mathematical functions
- A curated set of mathematical constants
- Power operator using `^` (instead of Python’s `**`)

It **does not** support:

- Variables (e.g. `x`, `y`)
- Attribute access (e.g. `obj.attr`)
- Indexing (e.g. `a[0]`)
- Assignments
- Imports or any Python-specific syntax

---

## Numbers

Both integers and floating-point numbers are supported.

Examples:

```text
42
3.14159
0.5
-12
```

Scientific notation is supported if Python accepts it:

```text
1e3
2.5e-4
```

---

## Operators

The following operators are supported:

| Operator | Description |
|--------|-------------|
| `+` | Addition |
| `-` | Subtraction |
| `*` | Multiplication |
| `/` | Division |
| `%` | Modulo |
| `^` | Power |

> **Note**: `^` is interpreted as exponentiation, not bitwise XOR.

Operator precedence follows standard mathematical rules.

---

## Parentheses

Parentheses can be used freely to group expressions.

Example:

```text
(3 + 2) * (4 + 1)
```

---

## Supported Functions

Only the following functions are available. Function names are **case-sensitive**.

### Trigonometric

- `sin(x)`
- `cos(x)`
- `tan(x)`
- `asin(x)`
- `acos(x)`
- `atan(x)`
- `sinh(x)`
- `cosh(x)`
- `tanh(x)`

(All angles are in **radians**.)

### Logarithmic & Exponential

- `log(x)` (natural logarithm)
- `ln(x)` (alias for natural logarithm)
- `log10(x)`
- `exp(x)`
- `sqrt(x)`
- `pow(x, y)`

### Miscellaneous

- `abs(x)`
- `floor(x)`
- `ceil(x)`
- `round(x [, ndigits])`

---

## Supported Constants

The following constants are predefined:

| Name | Description |
|----|-------------|
| `pi` | π |
| `e` | Euler’s number |
| `tau` | 2π |
| `inf` | Positive infinity |
| `nan` | Not-a-Number |

---

## Examples

Below are **non-trivial examples** that demonstrate realistic usage.

### Nested functions with power

```text
sin(pi / 4)^2 + cos(pi / 4)^2
```

### Combined logarithmic and exponential math

```text
log(exp(3) + sqrt(16)) / log(10)
```

### Deeply nested expression

```text
round(
  (3 + sqrt(5))^2 / (2 * log(e + 1)),
  5
)
```

### Hyperbolic and trigonometric mix

```text
sinh(1) + cosh(1) - tan(pi / 6)^2
```

---

## Invalid Expressions (Rejected)

The following examples are **not allowed** and will be rejected:

```text
x + 1              # variables are not supported
(1).__class__      # attribute access
import math        # imports
open("file.txt")   # I/O
```

--- 

## Notes

- All calculations use Python’s built-in floating-point behavior
- Errors such as division by zero propagate naturally
- The evaluator does not perform symbolic math; all expressions are numeric


"""

TITLE = rf"""
  ______                    ______     ____
 /_  __/__  _________ ___  / ____/__  / / /
  / / / _ \/ ___/ __ `__ \/ /   / _ \/ / /
 / / /  __/ /  / / / / / / /___/  __/ / /
/_/  \___/_/  /_/ /_/ /_/\____/\___/_/_/
-----------------------------------------
CSV Editor / Spreadsheet for the terminal

"""


COLORS = [
    "#ffffff",
    "#dddddd",
    "#aaaaaa",
    "#888888",
    "#777777",
    "#666666",
    "#555555",
    "#444444",
    "#5D5D5D",
    "#4D4D4D",
    "#3D3D3D",
    "#2D2D2D",
]


def get_title() -> Text:
    """Get the title, with a rainbow effect."""
    lines = TITLE.splitlines(keepends=True)
    return Text.assemble(*zip(lines, COLORS))


class HelpScreen(ModalScreen):
    """Simple Help screen with Markdown and a few links."""

    CSS = """
    /* Center the modal */
    HelpScreen {
        align: center middle;
    }
    
    /* Modal container */
    HelpScreen > VerticalScroll {
        background: $surface;
        border: heavy $accent;
        border-title-color: $text;
        border-subtitle-color: $text-muted;
        width: 95%;
        height: 80%;
        max-width: 100;
        max-height: 40;
        padding: 1;
        margin: 0;
    }
    
    /* Title inside modal */
    HelpScreen > VerticalScroll > .title {
        text-align: center;
        margin-bottom: 1;
    }
    
    /* Content */
    HelpScreen > VerticalScroll > Markdown {
        margin: 0;
    }
    
    #help-content {
        width: 100%;
        height: 1fr;
        margin: 0;
        overflow-y: auto;
        /* border: solid $accent; */
    }
    
    #help-content:focus {
        /* border: double $accent; */
    }
    
    """

    BINDINGS = [
        ("escape", "dismiss", "Dismiss"),
    ]

    def compose(self) -> ComposeResult:
        with VerticalScroll() as vertical_scroll:
            with Center():
                yield Static(get_title(), classes="title")
            yield Markdown(HELP_MARKDOWN)
            
        
        # Set border title - this will appear around the scroll container
        vertical_scroll.border_title = "CSV Editor Help"
        vertical_scroll.border_subtitle = "Press ESCAPE to close"
    
    def action_dismiss(self) -> None:
        """Dismiss the help screen."""
        self.dismiss()
