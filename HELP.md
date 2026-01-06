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
