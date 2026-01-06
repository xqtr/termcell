from datetime import datetime, timedelta
import random
import uuid
import os
import re
from utils import *

def scanvariable(value) -> str:
    # Get current date/time once
    now = datetime.now()
    # Define all special variables
    special_vars = {
        # Date/Time
        "$date": now.strftime("%Y-%m-%d"),
        "$time": now.strftime("%H:%M:%S"),
        "$now": now.strftime("%Y-%m-%d %H:%M:%S"),
        "$timestamp": now.isoformat(),
        "$today": now.strftime("%Y-%m-%d"),
        "$tomorrow": (now + timedelta(days=1)).strftime("%Y-%m-%d"),
        "$yesterday": (now - timedelta(days=1)).strftime("%Y-%m-%d"),
        "$weekday": now.strftime("%A"),
        "$month": now.strftime("%B"),
        "$year": str(now.year),
        "$hour": str(now.hour),
        "$minute": str(now.minute),
        "$second": str(now.second),
        "$datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
        # Random
        "$random": str(random.randint(1, 100)),
        "$randomint": str(random.randint(1, 100)),
        "$randomfloat": str(random.random()),
        "$randombool": random.choice(["TRUE", "FALSE"]),
        # UUID/GUID
        "$uuid": str(uuid.uuid4()),
        # System
        "$cwd": str(os.getcwd()),
        "$home": str(os.path.expanduser("~")),
        # Constants
        "$pi": str(3.141592653589793),
        "$e": str(2.718281828459045),
        
        # Text/Formatting
        "$tab": "\t",
        "$newline": "\n",
        "$comma": ",",
        "$pipe": "|",
        "$quote": '"',
        "$space": " ",
        "$dash": "-",
    }
    found = False
    for var, calc in special_vars.items():
        if var in value:
            replacement = value.replace(var, calc)
            found = True
                        
    if found:
        return replacement
    else:
        return None

def replace_cell_references(table,coords) -> str:
    """
    Replace cell references like $A8 with actual cell values.
    
    Args:
        text: Input string that may contain cell references like $A8, $B2, etc.
    
    Returns:
        String with cell references replaced by their values.
    """
    # Pattern to match $A1, $B2, $AA10, etc.
    # \$ matches the dollar sign
    # [A-Za-z]+ matches one or more letters (column)
    # \d+ matches one or more digits (row)
    pattern = r'\$([A-Za-z]+)(\d+)'
    cell_value = table.get_cell_at(coords)
    
    def replace_match(match):
        """Callback function to replace each match with cell value."""
        col_letters = match.group(1).upper()  # Column letters (A, B, AA, etc.)
        row_num = int(match.group(2))  # Row number (1-based)
        
        try:
            # Convert column letters to 0-based index
            col_num = 0
            col_num = aa2number(col_letters)
            #for i, char in enumerate(reversed(col_letters)):
            #    col_num += (ord(char) - 64) * (26 ** i)  # 'A' is 65 in ASCII
            
            col_num -= 1  # Convert to 0-based (A=0, B=1, etc.)
            
            # Adjust for row number column if your table has it
            # If column 0 is row_number, then add 1 to col_num
            #col_num += 1  # Assuming column 0 is row number
            
            # Convert row to 0-based
            row_num -= 1
            
            # Get the cell value
            #table = self.query_one(DataTable)
            #coord = type(self.current_cell)(row_num, col_num)
            #cellv = table.get_cell_at(coords)
            cellv = utils.get_cellvalue_by_index(table, row_num, col_num)
            
            if cell_value is None:
                return ""  # Empty cell
            else:
                return str(cellv)
                
        except Exception as e:
            # If anything goes wrong, return the original reference
            return match.group(0)  # Returns $A8 unchanged
    
    # Replace all matches in the text
    result = re.sub(pattern, replace_match, cell_value)
    return result

