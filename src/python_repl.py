import io
import sys
import traceback
from contextlib import redirect_stdout, redirect_stderr
from typing import Dict, Any

def execute_python_code(code: str) -> Dict[str, Any]:
    """
    Execute Python code and return the result, output, and any errors.

    This function creates a sandboxed environment to run Python code,
    capturing the output, errors, and an optional result value.

    Args:
        code (str): The Python code to execute.

    Returns:
        dict: A dictionary containing the execution result, output, and any errors.
    """
    output = io.StringIO()
    error = io.StringIO()
    result = None

    try:
        with redirect_stdout(output), redirect_stderr(error):
            exec_globals = {}
            exec(code, exec_globals)
            if 'result' in exec_globals:
                result = exec_globals['result']
    except Exception:
        error.write(traceback.format_exc())

    return {
        "result": result,
        "output": output.getvalue(),
        "error": error.getvalue()
    }

# Example usage
if __name__ == "__main__":
    # Example 1: Basic calculation
    code1 = """
print("Calculating the sum of squares from 1 to 5")
sum_of_squares = sum(x**2 for x in range(1, 6))
print(f"The sum of squares from 1 to 5 is: {sum_of_squares}")
result = sum_of_squares  # Set the result
"""
    result1 = execute_python_code(code1)
    print("Example 1 Result:", result1)

    # Example 2: Code with an error
    code2 = """
print("Attempting to divide by zero")
result = 1 / 0
"""
    result2 = execute_python_code(code2)
    print("Example 2 Result:", result2)

    # Example 3: More complex code
    code3 = """
def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b

print("Generating the first 10 Fibonacci numbers:")
fib_list = list(fibonacci(10))
print(fib_list)
result = sum(fib_list)  # Set the result to the sum of the first 10 Fibonacci numbers
"""
    result3 = execute_python_code(code3)
    print("Example 3 Result:", result3)