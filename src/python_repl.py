import ast
import io
import contextlib

# Execution mode toggle (True for safe mode, False for flexible mode)
SAFE_MODE = False

# Define the whitelist of safe built-in functions
SAFE_BUILTINS = {
    'abs': abs, 'all': all, 'any': any, 'ascii': ascii, 'bin': bin,
    'bool': bool, 'chr': chr, 'dict': dict, 'divmod': divmod, 'enumerate': enumerate,
    'filter': filter, 'float': float, 'format': format, 'frozenset': frozenset,
    'hex': hex, 'int': int, 'isinstance': isinstance, 'issubclass': issubclass,
    'len': len, 'list': list, 'map': map, 'max': max, 'min': min,
    'oct': oct, 'ord': ord, 'pow': pow, 'print': print, 'range': range,
    'repr': repr, 'reversed': reversed, 'round': round, 'set': set,
    'slice': slice, 'sorted': sorted, 'str': str, 'sum': sum, 'tuple': tuple,
    'type': type, 'zip': zip
}

def get_execution_mode():
    return "safe" if SAFE_MODE else "flexible"

def set_execution_mode(mode):
    global SAFE_MODE
    if mode not in ['safe', 'flexible']:
        raise ValueError("Mode must be either 'safe' or 'flexible'")
    SAFE_MODE = (mode == 'safe')

def safe_exec(code):
    try:
        # Parse the code into an AST
        tree = ast.parse(code, mode='exec')

        # Define a visitor to ensure only safe nodes are used
        class SafeVisitor(ast.NodeVisitor):
            SAFE_NODES = (
                ast.Module, ast.Expr, ast.Assign, ast.Load, ast.Store,
                ast.BinOp, ast.UnaryOp, ast.Constant, ast.Name,
                ast.Call, ast.Subscript, ast.Index, ast.Slice,
                ast.List, ast.Tuple, ast.Dict, ast.Set,
                ast.Compare, ast.IfExp, ast.For, ast.While, ast.If,
                ast.BoolOp, ast.And, ast.Or, ast.Not, ast.Eq, ast.NotEq,
                ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.In, ast.NotIn,
                ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod,
                ast.Pow, ast.LShift, ast.RShift, ast.BitOr, ast.BitXor, ast.BitAnd,
                ast.Return, ast.FunctionDef, ast.arguments, ast.arg, ast.With,
                ast.Raise, ast.Try, ast.ExceptHandler, ast.Pass, ast.Break, ast.Continue,
                ast.AugAssign, ast.Lambda, ast.DictComp, ast.ListComp, ast.GeneratorExp,
                ast.JoinedStr, ast.FormattedValue,  # Support for f-strings
            )

            def visit(self, node):
                if not isinstance(node, self.SAFE_NODES):
                    raise ValueError(f"Unsafe node '{type(node).__name__}' detected")
                return super().visit(node)

        # Visit the AST to ensure safety
        SafeVisitor().visit(tree)

        # Execute the code with restricted built-ins
        exec_globals = {'__builtins__': SAFE_BUILTINS}
        exec(code, exec_globals)
    except Exception as e:
        print(f"Error during safe execution: {e}")

def flexible_exec(code):
    try:
        exec(code)
    except Exception as e:
        print(f"Error during flexible execution: {e}")

def execute_python_code(code):
    try:
        # Capture the output of the executed code
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            exec(code, {})
        output = f.getvalue()
        # If there's no output, provide a default success message
        result = output.strip() if output else "Code executed successfully."
    except Exception as e:
        result = f"Error executing code: {str(e)}"
    return result  # Return a simple string

def toggle_execution_mode():
    global SAFE_MODE
    SAFE_MODE = not SAFE_MODE
    print(f"Execution mode changed to: {'safe' if SAFE_MODE else 'flexible'}")

if __name__ == "__main__":
    print("Current mode:", get_execution_mode())

    test_code = """
print("Hello, World!")
result = 5 + 3
print(f"5 + 3 = {result}")
"""

    print("\nExecuting test code:")
    execute_python_code(test_code)

    print("\nToggling mode...")
    toggle_execution_mode()

    print("\nExecuting test code again:")
    execute_python_code(test_code)