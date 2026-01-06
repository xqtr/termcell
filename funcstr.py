from utils import * 
from typing import Callable, Tuple, Optional


def apply_cell_transform(table, target: str, transform_func: Callable[[str], str]) -> None:
    """
    Unified function to apply string transformations to cells or ranges.
    
    Args:
        table: DataTable widget
        target: Cell reference ("A1") or range ("A1:B10")
        transform_func: Function that transforms a string
    """
    
    if is_cell_area(target):
        y1, x1, y2, x2 = parse_cell_area(target)
        for row in range(y1,y2+1):
            for col in range(x1,x2+1):
                current_value = get_cellvalue_by_index(table, row, col)
                transformed = transform_func(current_value)
                table.update_cell_at((row, col), transformed)

    if is_cell(target):
        col, row = parse_cell_coordinate(target)
        current_value = get_cellvalue_by_index(table, row, col)
        transformed = transform_func(current_value)
        table.update_cell_at((row, col), transformed)


def fillstr(table, target: str, fillstr: str) -> None:
    if is_cell_area(target):
        y1, x1, y2, x2 = parse_cell_area(target)
        for row in range(y1,y2+1):
            for col in range(x1,x2+1):
                table.update_cell_at((row, col), fillstr)

    if is_cell(target):
        col, row = parse_cell_coordinate(target)
        table.update_cell_at((row, col), fillstr)

def calculate_formula(table, target: str):
    target = target[1:].upper() # remove the = sign
    target = target.replace(" ","") # remove all spaces
    parts = target.split("(")
    cmd = parts[0]
    cell = parts[1].split(")")[0]
    
    if cmd == "SUM":
        return calulate_sum(table,cell)
    elif cmd == "AVG":
        return calulate_avg(table,cell)
    elif cmd == "COUNT":
        return calulate_count(table,cell)
    elif cmd == "MIN":
        return calulate_max(table,cell)
    elif cmd == "MAX":
        return calulate_max(table,cell)


def calulate_sum(table,target):
    if is_cell_area(target):
        result = 0
        y1, x1, y2, x2 = parse_cell_area(target)
        for row in range(y1,y2+1):
            for col in range(x1,x2+1):
                value = table.get_cell_at((row, col))
                if value.isdigit():
                    result += int(value)
        return str(result)

    if is_cell(target):
        return str("#ERROR")
        
def calulate_avg(table,target):
    if is_cell_area(target):
        result = 0
        count = 0
        y1, x1, y2, x2 = parse_cell_area(target)
        for row in range(y1,y2+1):
            for col in range(x1,x2+1):
                value = table.get_cell_at((row, col))
                if value.isdigit():
                    count += 1
                    result += int(value)
        return str(result / count) if count > 0 else "0"

    if is_cell(target):
        return str("#ERROR")
        
def calulate_count(table,target):
    if is_cell_area(target):
        count = 0
        y1, x1, y2, x2 = parse_cell_area(target)
        for row in range(y1,y2+1):
            for col in range(x1,x2+1):
                value = table.get_cell_at((row, col))
                if value.isdigit():
                    count += 1
        return str(count)

    if is_cell(target):
        return str("#ERROR")

def calulate_max(table,target):
    if is_cell_area(target):
        values = []
        y1, x1, y2, x2 = parse_cell_area(target)
        for row in range(y1,y2+1):
            for col in range(x1,x2+1):
                value = table.get_cell_at((row, col))
                if value.isdigit():
                    values.append(value)
        return str(max(values))

    if is_cell(target):
        return str("#ERROR")


def calulate_max(table,target):
    if is_cell_area(target):
        values = []
        y1, x1, y2, x2 = parse_cell_area(target)
        for row in range(y1,y2+1):
            for col in range(x1,x2+1):
                value = table.get_cell_at((row, col))
                if value.isdigit():
                    values.append(value)
        return str(min(values))

    if is_cell(target):
        return str("#ERROR")
