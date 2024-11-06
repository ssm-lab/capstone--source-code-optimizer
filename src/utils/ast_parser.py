import ast

def parse_line(file: str, line: int):
    with open(file, "r") as f:
        file_lines = f.readlines()
    try:
        node = ast.parse(file_lines[line - 1].strip())
    except(SyntaxError) as e:
        return None
    
    return node

def parse_file(file: str):
    with open(file, "r") as f:
        source = f.read()
    
    return ast.parse(source)