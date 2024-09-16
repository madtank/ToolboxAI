import ast
import json
import math
import sys
import io
import string

def execute_python_code(code: str = None) -> str:
    """
    Execute pre-approved Python code and return the input code and output.
    If no code is provided, it runs a built-in example.
    """
    if code is None:
        # Built-in example/test
        code = """
word = 'strawberry'
count_r = word.count('r')
print(f"The word '{word}' has {count_r} 'r's.")
"""

    try:
        # Prepare allowed names (modules and built-in functions)
        allowed_names = {
            'math': math,
            'string': string,
            'print': print,
            'len': len,
            'str': str,
            'int': int,
            'float': float,
            'list': list,
            'dict': dict,
            'set': set,
            'tuple': tuple,
            'enumerate': enumerate,
            'range': range,
            # Add other allowed built-in functions here
        }

        # Add allowed methods for string objects
        allowed_attributes = {
            'str': [
                'lower', 'upper', 'count', 'find', 'replace', 'split', 'strip', 'startswith', 'endswith',
            ],
            # You can add allowed methods for other types here
        }

        # Parse the code into an AST
        tree = ast.parse(code, mode='exec')

        # Define a visitor to ensure only allowed nodes and names are used
        class SafeVisitor(ast.NodeVisitor):
            SAFE_NODES = (
                ast.Module, ast.Expr, ast.Assign, ast.Load, ast.Store,
                ast.BinOp, ast.UnaryOp, ast.Constant, ast.Name,
                ast.Call, ast.Attribute, ast.Subscript, ast.Index, ast.Slice,
                ast.List, ast.Tuple, ast.Dict, ast.Set,
                ast.Compare, ast.IfExp, ast.For, ast.While, ast.If,
                ast.BoolOp, ast.And, ast.Or, ast.Not, ast.Eq, ast.NotEq,
                ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.In, ast.NotIn,
                ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod,
                ast.Pow, ast.LShift, ast.RShift, ast.BitOr, ast.BitXor, ast.BitAnd,
                ast.Return, ast.FunctionDef, ast.arguments, ast.arg, ast.With,
                ast.Raise, ast.Try, ast.ExceptHandler, ast.Pass, ast.Break, ast.Continue,
                ast.AugAssign, ast.Lambda, ast.DictComp, ast.ListComp, ast.GeneratorExp,
                ast.JoinedStr, ast.FormattedValue,  # Add support for f-strings
            )

            def visit(self, node):
                if not isinstance(node, self.SAFE_NODES):
                    raise ValueError(f"Unsafe node '{type(node).__name__}' detected")
                return super().visit(node)

            def visit_Name(self, node):
                if node.id.startswith('_'):
                    raise NameError(f"Use of name '{node.id}' is not allowed")
                return self.generic_visit(node)

            def visit_Call(self, node):
                self.visit(node.func)
                for arg in node.args:
                    self.visit(arg)
                for keyword in node.keywords:
                    self.visit(keyword.value)

            def visit_Attribute(self, node):
                self.visit(node.value)
                if isinstance(node.value, ast.Name):
                    if node.value.id not in allowed_names:
                        # Allow attributes on variables, which will be checked at runtime
                        return
                elif isinstance(node.value, ast.Constant):
                    obj_type = type(node.value.value).__name__
                    if obj_type == 'str':
                        if node.attr not in allowed_attributes.get('str', []):
                            raise AttributeError(f"Attribute '{node.attr}' is not allowed on str objects")
                    elif obj_type not in allowed_names:
                        raise AttributeError(f"Attributes on object type '{obj_type}' are not allowed")
                else:
                    raise AttributeError(f"Attributes on complex expressions are not allowed")

        # Visit the AST to ensure safety
        SafeVisitor().visit(tree)

        # Prepare the namespace for execution
        exec_globals = {'__builtins__': None}
        exec_globals.update(allowed_names)
        exec_locals = {}

        # Capture output
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        try:
            # Compile the AST
            compiled_code = compile(tree, filename='<ast>', mode='exec')
            # Execute the code
            exec(compiled_code, exec_globals, exec_locals)
            # Get the output
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        return json.dumps({
            "code": code,
            "output": output.strip()
        })
    except Exception as e:
        return json.dumps({
            "code": code,
            "output": f"Error: {str(e)}"
        })

# Add this at the end of the file to automatically run the test when the module is imported
if __name__ == "__main__":
    print("Running built-in test:")
    print(execute_python_code())