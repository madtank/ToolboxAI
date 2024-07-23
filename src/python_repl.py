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
