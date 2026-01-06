import re
from typing import Union, Dict, List

class FormulaEvaluator:
    """Simple formula evaluator for spreadsheet-like functions."""
    
    @staticmethod
    def evaluate(formula: str, table, get_cell_value_func) -> Union[str, float, int]:
        """Evaluate a formula string."""
        formula = formula.strip()
        
        # Check if it's a formula (starts with =)
        if not formula.startswith("="):
            return formula
        
        # Remove the = sign
        formula = formula[1:].strip().lower()
        
        # Try to parse as a function
        match = re.match(r'(\w+)\((.+)\)', formula)
        if match:
            func_name = match.group(1)
            args_str = match.group(2)
            return FormulaEvaluator._execute_function(func_name, args_str, table, get_cell_value_func)
        
        # Try to parse as a simple expression (like =A1+B2)
        try:
            return FormulaEvaluator._evaluate_expression(formula, table, get_cell_value_func)
        except:
            return f"#ERROR: Invalid formula: {formula}"
    
    @staticmethod
    def _execute_function(func_name: str, args_str: str, table, get_cell_value_func) -> Union[str, float, int]:
        """Execute a spreadsheet function."""
        # Parse arguments
        args = []
        current_arg = ""
        paren_depth = 0
        
        for char in args_str:
            if char == ',' and paren_depth == 0:
                args.append(current_arg.strip())
                current_arg = ""
            else:
                if char == '(':
                    paren_depth += 1
                elif char == ')':
                    paren_depth -= 1
                current_arg += char
        
        if current_arg:
            args.append(current_arg.strip())
        
        # Execute the function
        func_name = func_name.lower()
        
        if func_name == "sum":
            return FormulaEvaluator._sum(args, table, get_cell_value_func)
        elif func_name == "average" or func_name == "avg":
            return FormulaEvaluator._average(args, table, get_cell_value_func)
        elif func_name == "count":
            return FormulaEvaluator._count(args, table, get_cell_value_func)
        elif func_name == "max":
            return FormulaEvaluator._max(args, table, get_cell_value_func)
        elif func_name == "min":
            return FormulaEvaluator._min(args, table, get_cell_value_func)
        elif func_name == "concat":
            return FormulaEvaluator._concat(args, table, get_cell_value_func)
        elif func_name == "len" or func_name == "length":
            return FormulaEvaluator._len(args, table, get_cell_value_func)
        elif func_name == "upper":
            return FormulaEvaluator._upper(args, table, get_cell_value_func)
        elif func_name == "lower":
            return FormulaEvaluator._lower(args, table, get_cell_value_func)
        elif func_name == "trim":
            return FormulaEvaluator._trim(args, table, get_cell_value_func)
        elif func_name == "if":
            return FormulaEvaluator._if(args, table, get_cell_value_func)
        else:
            return f"#ERROR: Unknown function: {func_name}"
    
    @staticmethod
    def _parse_cell_reference(ref: str) -> tuple:
        """Parse cell reference like A1 or A1:B2."""
        # Check if it's a range
        if ':' in ref:
            start, end = ref.split(':')
            return FormulaEvaluator._parse_single_cell(start), FormulaEvaluator._parse_single_cell(end)
        else:
            return FormulaEvaluator._parse_single_cell(ref), None
    
    @staticmethod
    def _parse_single_cell(ref: str) -> tuple:
        """Parse single cell reference like A1 to (row, col)."""
        # Extract column letters and row number
        match = re.match(r'([a-z]+)(\d+)', ref.lower())
        if not match:
            raise ValueError(f"Invalid cell reference: {ref}")
        
        col_letters = match.group(1)
        row_num = int(match.group(2)) - 1  # Convert to 0-indexed
        
        # Convert column letters to number (A=0, B=1, ..., AA=26, etc.)
        col_num = 0
        for i, char in enumerate(reversed(col_letters)):
            col_num += (ord(char) - 96) * (26 ** i)  # 'a' is 97 in ASCII
        col_num -= 1  # A should be 0
        
        return (row_num, col_num)
    
    @staticmethod
    def _get_cell_range_values(start: tuple, end: tuple, table, get_cell_value_func) -> List:
        """Get all values in a cell range."""
        values = []
        start_row, start_col = start
        end_row, end_col = end
        
        for row in range(min(start_row, end_row), max(start_row, end_row) + 1):
            for col in range(min(start_col, end_col), max(start_col, end_col) + 1):
                try:
                    value = get_cell_value_func(row, col)
                    if value != "":
                        values.append(value)
                except:
                    pass
        
        return values
    
    @staticmethod
    def _sum(args: List[str], table, get_cell_value_func) -> Union[float, str]:
        """Calculate sum of values."""
        total = 0
        for arg in args:
            # Check if it's a cell range
            if ':' in arg:
                start, end = FormulaEvaluator._parse_cell_reference(arg)
                values = FormulaEvaluator._get_cell_range_values(start, end, table, get_cell_value_func)
                for value in values:
                    try:
                        total += float(value)
                    except:
                        pass
            else:
                # Try to parse as number or cell reference
                try:
                    # Check if it's a cell reference
                    if re.match(r'[a-z]+\d+', arg.lower()):
                        row, col = FormulaEvaluator._parse_single_cell(arg)
                        value = get_cell_value_func(row, col)
                        if value:
                            total += float(value)
                    else:
                        # It's a direct number
                        total += float(arg)
                except:
                    pass
        
        return total
    
    @staticmethod
    def _average(args: List[str], table, get_cell_value_func) -> Union[float, str]:
        """Calculate average of values."""
        values = []
        for arg in args:
            if ':' in arg:
                start, end = FormulaEvaluator._parse_cell_reference(arg)
                values.extend(FormulaEvaluator._get_cell_range_values(start, end, table, get_cell_value_func))
            else:
                if re.match(r'[a-z]+\d+', arg.lower()):
                    row, col = FormulaEvaluator._parse_single_cell(arg)
                    value = get_cell_value_func(row, col)
                    if value:
                        values.append(value)
                else:
                    values.append(arg)
        
        # Convert to numbers
        numbers = []
        for value in values:
            try:
                numbers.append(float(value))
            except:
                pass
        
        if not numbers:
            return 0
        
        return sum(numbers) / len(numbers)
    
    @staticmethod
    def _count(args: List[str], table, get_cell_value_func) -> int:
        """Count non-empty cells."""
        count = 0
        for arg in args:
            if ':' in arg:
                start, end = FormulaEvaluator._parse_cell_reference(arg)
                values = FormulaEvaluator._get_cell_range_values(start, end, table, get_cell_value_func)
                count += len([v for v in values if v != ""])
            else:
                if re.match(r'[a-z]+\d+', arg.lower()):
                    row, col = FormulaEvaluator._parse_single_cell(arg)
                    value = get_cell_value_func(row, col)
                    if value != "":
                        count += 1
        
        return count
    
    @staticmethod
    def _max(args: List[str], table, get_cell_value_func) -> Union[float, str]:
        """Find maximum value."""
        numbers = []
        for arg in args:
            if ':' in arg:
                start, end = FormulaEvaluator._parse_cell_reference(arg)
                values = FormulaEvaluator._get_cell_range_values(start, end, table, get_cell_value_func)
                for value in values:
                    try:
                        numbers.append(float(value))
                    except:
                        pass
            else:
                try:
                    if re.match(r'[a-z]+\d+', arg.lower()):
                        row, col = FormulaEvaluator._parse_single_cell(arg)
                        value = get_cell_value_func(row, col)
                        if value:
                            numbers.append(float(value))
                    else:
                        numbers.append(float(arg))
                except:
                    pass
        
        return max(numbers) if numbers else 0
    
    @staticmethod
    def _min(args: List[str], table, get_cell_value_func) -> Union[float, str]:
        """Find minimum value."""
        numbers = []
        for arg in args:
            if ':' in arg:
                start, end = FormulaEvaluator._parse_cell_reference(arg)
                values = FormulaEvaluator._get_cell_range_values(start, end, table, get_cell_value_func)
                for value in values:
                    try:
                        numbers.append(float(value))
                    except:
                        pass
            else:
                try:
                    if re.match(r'[a-z]+\d+', arg.lower()):
                        row, col = FormulaEvaluator._parse_single_cell(arg)
                        value = get_cell_value_func(row, col)
                        if value:
                            numbers.append(float(value))
                    else:
                        numbers.append(float(arg))
                except:
                    pass
        
        return min(numbers) if numbers else 0
    
    @staticmethod
    def _concat(args: List[str], table, get_cell_value_func) -> str:
        """Concatenate strings."""
        result = ""
        for arg in args:
            if ':' in arg:
                start, end = FormulaEvaluator._parse_cell_reference(arg)
                values = FormulaEvaluator._get_cell_range_values(start, end, table, get_cell_value_func)
                for value in values:
                    result += str(value)
            else:
                if re.match(r'[a-z]+\d+', arg.lower()):
                    row, col = FormulaEvaluator._parse_single_cell(arg)
                    value = get_cell_value_func(row, col)
                    result += str(value) if value else ""
                else:
                    # Remove quotes if present
                    if arg.startswith('"') and arg.endswith('"'):
                        arg = arg[1:-1]
                    result += arg
        
        return result
    
    @staticmethod
    def _len(args: List[str], table, get_cell_value_func) -> int:
        """Get length of string or count cells."""
        if len(args) != 1:
            return "#ERROR: LEN requires exactly 1 argument"
        
        arg = args[0]
        if ':' in arg:
            # Count cells in range
            start, end = FormulaEvaluator._parse_cell_reference(arg)
            values = FormulaEvaluator._get_cell_range_values(start, end, table, get_cell_value_func)
            return len([v for v in values if v != ""])
        else:
            if re.match(r'[a-z]+\d+', arg.lower()):
                row, col = FormulaEvaluator._parse_single_cell(arg)
                value = get_cell_value_func(row, col)
                return len(str(value)) if value else 0
            else:
                if arg.startswith('"') and arg.endswith('"'):
                    arg = arg[1:-1]
                return len(arg)
    
    @staticmethod
    def _upper(args: List[str], table, get_cell_value_func) -> str:
        """Convert to uppercase."""
        if len(args) != 1:
            return "#ERROR: UPPER requires exactly 1 argument"
        
        arg = args[0]
        if re.match(r'[a-z]+\d+', arg.lower()):
            row, col = FormulaEvaluator._parse_single_cell(arg)
            value = get_cell_value_func(row, col)
            return str(value).upper() if value else ""
        else:
            if arg.startswith('"') and arg.endswith('"'):
                arg = arg[1:-1]
            return arg.upper()
    
    @staticmethod
    def _lower(args: List[str], table, get_cell_value_func) -> str:
        """Convert to lowercase."""
        if len(args) != 1:
            return "#ERROR: LOWER requires exactly 1 argument"
        
        arg = args[0]
        if re.match(r'[a-z]+\d+', arg.lower()):
            row, col = FormulaEvaluator._parse_single_cell(arg)
            value = get_cell_value_func(row, col)
            return str(value).lower() if value else ""
        else:
            if arg.startswith('"') and arg.endswith('"'):
                arg = arg[1:-1]
            return arg.lower()
    
    @staticmethod
    def _trim(args: List[str], table, get_cell_value_func) -> str:
        """Trim whitespace."""
        if len(args) != 1:
            return "#ERROR: TRIM requires exactly 1 argument"
        
        arg = args[0]
        if re.match(r'[a-z]+\d+', arg.lower()):
            row, col = FormulaEvaluator._parse_single_cell(arg)
            value = get_cell_value_func(row, col)
            return str(value).strip() if value else ""
        else:
            if arg.startswith('"') and arg.endswith('"'):
                arg = arg[1:-1]
            return arg.strip()
    
    @staticmethod
    def _if(args: List[str], table, get_cell_value_func) -> Union[str, float]:
        """IF(condition, value_if_true, value_if_false)."""
        if len(args) != 3:
            return "#ERROR: IF requires 3 arguments"
        
        condition = args[0]
        true_value = args[1]
        false_value = args[2]
        
        # Simple condition evaluation (can be expanded)
        # For now, just check if condition is non-empty/non-zero
        if condition.lower() in ["true", "1"]:
            return FormulaEvaluator._parse_value(true_value, table, get_cell_value_func)
        elif condition.lower() in ["false", "0"]:
            return FormulaEvaluator._parse_value(false_value, table, get_cell_value_func)
        else:
            # Try to evaluate as expression
            try:
                # Simple numeric comparison
                if "=" in condition:
                    left, right = condition.split("=")
                    left_val = FormulaEvaluator._parse_value(left.strip(), table, get_cell_value_func)
                    right_val = FormulaEvaluator._parse_value(right.strip(), table, get_cell_value_func)
                    if left_val == right_val:
                        return FormulaEvaluator._parse_value(true_value, table, get_cell_value_func)
                    else:
                        return FormulaEvaluator._parse_value(false_value, table, get_cell_value_func)
                elif ">" in condition:
                    left, right = condition.split(">")
                    left_val = float(FormulaEvaluator._parse_value(left.strip(), table, get_cell_value_func))
                    right_val = float(FormulaEvaluator._parse_value(right.strip(), table, get_cell_value_func))
                    if left_val > right_val:
                        return FormulaEvaluator._parse_value(true_value, table, get_cell_value_func)
                    else:
                        return FormulaEvaluator._parse_value(false_value, table, get_cell_value_func)
                elif "<" in condition:
                    left, right = condition.split("<")
                    left_val = float(FormulaEvaluator._parse_value(left.strip(), table, get_cell_value_func))
                    right_val = float(FormulaEvaluator._parse_value(right.strip(), table, get_cell_value_func))
                    if left_val < right_val:
                        return FormulaEvaluator._parse_value(true_value, table, get_cell_value_func)
                    else:
                        return FormulaEvaluator._parse_value(false_value, table, get_cell_value_func)
            except:
                pass
            
            # Default: if condition is non-empty/non-zero, it's true
            cond_val = FormulaEvaluator._parse_value(condition, table, get_cell_value_func)
            if cond_val and str(cond_val).lower() not in ["0", "false", "no"]:
                return FormulaEvaluator._parse_value(true_value, table, get_cell_value_func)
            else:
                return FormulaEvaluator._parse_value(false_value, table, get_cell_value_func)
    
    @staticmethod
    def _parse_value(value_str: str, table, get_cell_value_func) -> Union[str, float]:
        """Parse a value string (could be cell reference, number, or string)."""
        # Check if it's a cell reference
        if re.match(r'[a-z]+\d+', value_str.lower()):
            row, col = FormulaEvaluator._parse_single_cell(value_str)
            return get_cell_value_func(row, col) or ""
        # Check if it's a string literal
        elif value_str.startswith('"') and value_str.endswith('"'):
            return value_str[1:-1]
        # Try as number
        else:
            try:
                return float(value_str)
            except:
                return value_str
    
    @staticmethod
    def _evaluate_expression(expr: str, table, get_cell_value_func) -> Union[float, str]:
        """Evaluate simple arithmetic expression."""
        # Replace cell references with their values
        def replace_cell_ref(match):
            cell_ref = match.group(0).upper()
            try:
                row, col = FormulaEvaluator._parse_single_cell(cell_ref)
                value = get_cell_value_func(row, col)
                return str(float(value)) if value else "0"
            except:
                return "0"
        
        # Find and replace cell references
        expr = re.sub(r'[A-Z]+\d+', replace_cell_ref, expr.upper())
        
        # Evaluate the expression safely
        try:
            # Use eval with limited builtins for safety
            result = eval(expr, {"__builtins__": {}}, {})
            return result
        except Exception as e:
            return f"#ERROR: {str(e)}"
