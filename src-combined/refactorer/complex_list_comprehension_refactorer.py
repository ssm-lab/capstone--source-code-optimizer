import ast
import astor
from .base_refactorer import BaseRefactorer

class ComplexListComprehensionRefactorer(BaseRefactorer):
    """
    Refactorer for complex list comprehensions to improve readability.
    """

    def __init__(self, code: str):
        """
        Initializes the refactorer.

        :param code: The source code to refactor.
        """
        super().__init__(code)

    def refactor(self):
        """
        Refactor the code by transforming complex list comprehensions into for-loops.

        :return: The refactored code.
        """
        # Parse the code to get the AST
        tree = ast.parse(self.code)

        # Walk through the AST and refactor complex list comprehensions
        for node in ast.walk(tree):
            if isinstance(node, ast.ListComp):
                # Check if the list comprehension is complex
                if self.is_complex(node):
                    # Create a for-loop equivalent
                    for_loop = self.create_for_loop(node)
                    # Replace the list comprehension with the for-loop in the AST
                    self.replace_node(node, for_loop)

        # Convert the AST back to code
        return self.ast_to_code(tree)

    def create_for_loop(self, list_comp: ast.ListComp) -> ast.For:
        """
        Create a for-loop that represents the list comprehension.

        :param list_comp: The ListComp node to convert.
        :return: An ast.For node representing the for-loop.
        """
        # Create the variable to hold results
        result_var = ast.Name(id='result', ctx=ast.Store())

        # Create the for-loop
        for_loop = ast.For(
            target=ast.Name(id='item', ctx=ast.Store()),
            iter=list_comp.generators[0].iter,
            body=[
                ast.Expr(value=ast.Call(
                    func=ast.Name(id='append', ctx=ast.Load()),
                    args=[self.transform_value(list_comp.elt)],
                    keywords=[]
                ))
            ],
            orelse=[]
        )

        # Create a list to hold results
        result_list = ast.List(elts=[], ctx=ast.Store())
        return ast.With(
            context_expr=ast.Name(id='result', ctx=ast.Load()),
            body=[for_loop],
            lineno=list_comp.lineno,
            col_offset=list_comp.col_offset
        )

    def transform_value(self, value_node: ast.AST) -> ast.AST:
        """
        Transform the value in the list comprehension into a form usable in a for-loop.

        :param value_node: The value node to transform.
        :return: The transformed value node.
        """
        return value_node

    def replace_node(self, old_node: ast.AST, new_node: ast.AST):
        """
        Replace an old node in the AST with a new node.

        :param old_node: The node to replace.
        :param new_node: The node to insert in its place.
        """
        parent = self.find_parent(old_node)
        if parent:
            for index, child in enumerate(ast.iter_child_nodes(parent)):
                if child is old_node:
                    parent.body[index] = new_node
                    break

    def find_parent(self, node: ast.AST) -> ast.AST:
        """
        Find the parent node of a given AST node.

        :param node: The node to find the parent for.
        :return: The parent node, or None if not found.
        """
        for parent in ast.walk(node):
            for child in ast.iter_child_nodes(parent):
                if child is node:
                    return parent
        return None

    def ast_to_code(self, tree: ast.AST) -> str:
        """
        Convert AST back to source code.

        :param tree: The AST to convert.
        :return: The source code as a string.
        """
        return astor.to_source(tree)
