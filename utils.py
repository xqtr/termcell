import re


regx_area = r'^(\$?[A-Za-z]{1,3}\$?\d{1,7}:\$?[A-Za-z]{1,3}\$?\d{1,7})$'
regx_cell = r'^(\$?[A-Za-z]{1,3}\$?\d{1,7})$'


def is_cell_area(input_str: str) -> bool:
    if not isinstance(input_str, str):
        return False
    input_str = input_str.strip()
    return bool(re.match(regx_area, input_str))


def is_cell(input_str: str) -> bool:
    if not isinstance(input_str, str):
        return False
    input_str = input_str.strip()
    return bool(re.match(regx_cell, input_str))


def col2num(col: str) -> int:
    """
    Converts a string of uppercase letters (A-Z) representing a base-26 column identifier
    to its decimal (base-10) equivalent. A=1, B=2, ..., Z=26, AA=27, AB=28, etc.
    
    Args:
        col (str): The column identifier (e.g., 'Z', 'AA').
    
    Returns:
        int: The decimal number.
    
    Raises:
        ValueError: If the input contains invalid characters.
    """
    if not col:
        raise ValueError("Input string cannot be empty.")
    
    result = 0
    for char in col.upper():
        if not ('A' <= char <= 'Z'):
            raise ValueError(f"Invalid character '{char}' in input. Only A-Z allowed.")
        value = ord(char) - ord('A') + 1
        result = result * 26 + value
    
    return result
    
def parse_cell_coordinate(cell: str) -> tuple[int, int]:
    """
    Parses a spreadsheet cell coordinate (e.g., 'AA12', 'ghd204') into a tuple of (column_number, row_number).
    Columns are base-26 (A=1, B=2, ..., Z=26, AA=27, etc.), case-insensitive.
    Rows are 1-based integers.
    
    Args:
        cell (str): The cell coordinate.
    
    Returns:
        tuple[int, int]: (column, row)
    
    Raises:
        ValueError: If the input is invalid (e.g., no letters, no digits, invalid chars).
    """
    if not cell:
        raise ValueError("Cell coordinate cannot be empty.")
    
    cell = cell.strip().upper()
    if cell.startswith('$'):
        cell = cell[1:]
    
    # Separate letters (column) from digits (row)
    import re
    match = re.match(r'([A-Z]+)(\d+)', cell)
    if not match:
        raise ValueError(f"Invalid cell coordinate '{cell}'. Must be letters followed by digits.")
    
    col_str, row_str = match.groups()
    
    # Convert column to number
    column = col2num(col_str)
        
    # Convert row to int
    try:
        row = int(row_str)
        if row < 1:
            raise ValueError("Row must be a positive integer >= 1.")
    except ValueError:
        raise ValueError(f"Invalid row '{row_str}'. Must be a positive integer.")
    
    return (column, row-1)
    
def parse_cell_area(area: str) -> tuple[int, int, int, int]:
    """
    Parses a spreadsheet cell area (e.g., 'AA22:BB33', 'A3:D6') into a tuple of (row1, col1, row2, col2).
    Uses base-26 for columns (A=1, ..., AA=27, etc.), case-insensitive.
    Ensures the second cell is after the first (row2 >= row1 and col2 >= col1).
    
    Args:
        area (str): The cell area (e.g., 'A3:D6').
    
    Returns:
        tuple[int, int, int, int]: (row_start, col_start, row_end, col_end)
    
    Raises:
        ValueError: If the input is invalid or the range is inverted.
    """
    if not area:
        raise ValueError("Cell area cannot be empty.")
    
    area = area.strip().upper()
    
    # Split by colon
    parts = area.split(':')
    if len(parts) != 2:
        raise ValueError(f"Invalid cell area '{area}'. Must be in format 'CELL1:CELL2'.")
    
    left_cell, right_cell = parts
    
    # Parse both cells
    try:
        col1, row1 = parse_cell_coordinate(left_cell)
        col2, row2 = parse_cell_coordinate(right_cell)
    except ValueError as e:
        raise ValueError(f"Error parsing cells in '{area}': {e}")
    
    # Check if range is valid (not inverted)
    if row2 < row1 or col2 < col1:
        raise ValueError(f"Invalid range '{area}': Second cell must be after the first (row2 >= row1 and col2 >= col1).")
    
    return (row1, col1, row2, col2)
    
def get_cellvalue_by_index(datatable, row_idx, col_idx):
    """
    Get cell value using numeric indices.
    
    Parameters:
    -----------
    datatable: textual.widgets.DataTable
        The DataTable widget instance
    row_idx: int
        Zero-based row index
    col_idx: int
        Zero-based column index
    
    Returns:
    --------
    str: The cell value as a string, or None if not found
    """
    try:
        # Get row key from index
        row_keys = list(datatable.rows.keys())
        if row_idx < 0 or row_idx >= len(row_keys):
            return "#INVROW"
        
        # Get column key from index
        col_keys = list(datatable.columns.keys())
        if col_idx < 0 or col_idx >= len(col_keys):
            return "#INVCOL"
        
        return datatable.get_cell(row_keys[row_idx], col_keys[col_idx])
    except (KeyError, IndexError, AttributeError):
        return "#ERROR"

def list_cell_references(text):
    """
    Extract Excel-style cell references from a string.
    
    Pattern matches: $A1, AA$12, $AA$12, A1, etc.
    Supports absolute references ($), relative references, and cell ranges.
    
    Parameters:
    -----------
    text : str
        String containing potential cell references
    
    Returns:
    --------
    list: List of matched cell references
    
    Examples:
    ---------
    >>> extract_cell_references("$AA12 to the $B32")
    ['$AA12', '$B32']
    
    >>> extract_cell_references("Sum(A1:B10, C$5)")
    ['A1', 'B10', 'C$5']
    
    >>> extract_cell_references("Invalid references: AA, 12, $123")
    []
    """
    # Pattern explanation:
    # (\$?[A-Z]{1,3}) - Optional $ followed by 1-3 letters (column)
    # (\$?\d{1,7})    - Optional $ followed by 1-7 digits (row)
    # No $ at all also matches (relative references)
    pattern = r'\$?[A-Za-z]{1,3}\d{1,7}'
    
    # Find all matches in the text
    matches = re.findall(pattern, text)
    
    return matches
