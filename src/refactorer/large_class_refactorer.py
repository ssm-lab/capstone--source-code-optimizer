import ast

class LargeClassRefactorer:
    """
    Refactorer for large classes that have too many methods.
    """

    def __init__(self, code: str, method_threshold: int = 5):
        """
        Initializes the refactorer.

        :param code: The source code of the class to refactor.
        :param method_threshold: The number of methods above which a class is considered large.
        """
        self.code = code
        self.method_threshold = method_threshold

    def refactor(self):
        """
        Refactor the class by splitting it into smaller classes if it exceeds the method threshold.

        :return: The refactored code.
        """
        # Parse the code to get the class definition
        tree = ast.parse(self.code)
        class_definitions = [node for node in tree.body if isinstance(node, ast.ClassDef)]

        refactored_code = []

        for class_def in class_definitions:
            methods = [n for n in class_def.body if isinstance(n, ast.FunctionDef)]
            if len(methods) > self.method_threshold:
                # If the class is large, split it
                new_classes = self.split_class(class_def, methods)
                refactored_code.extend(new_classes)
            else:
                # Keep the class as is
                refactored_code.append(class_def)

        # Convert the AST back to code
        return self.ast_to_code(refactored_code)

    def split_class(self, class_def, methods):
        """
        Split the large class into smaller classes based on methods.

        :param class_def: The class definition node.
        :param methods: The list of methods in the class.
        :return: A list of new class definitions.
        """
        # For demonstration, we'll simply create two classes based on the method count
        half_index = len(methods) // 2
        new_class1 = self.create_new_class(class_def.name + "Part1", methods[:half_index])
        new_class2 = self.create_new_class(class_def.name + "Part2", methods[half_index:])

        return [new_class1, new_class2]

    def create_new_class(self, new_class_name, methods):
        """
        Create a new class definition with the specified methods.

        :param new_class_name: Name of the new class.
        :param methods: List of methods to include in the new class.
        :return: A new class definition node.
        """
        # Create the class definition with methods
        class_def = ast.ClassDef(
            name=new_class_name,
            bases=[],
            body=methods,
            decorator_list=[]
        )
        return class_def

    def ast_to_code(self, nodes):
        """
        Convert AST nodes back to source code.

        :param nodes: The AST nodes to convert.
        :return: The source code as a string.
        """
        import astor
        return astor.to_source(nodes)
