import subprocess
import shlex
import os
import sys

def execute_safe_command(command_string: str) -> str:
    """
    Executes a shell command safely by bypassing shell=True and tokenizing the input.
    """
    try:
        # shlex.split safely tokenizes the string into a list for Popen/run
        args = shlex.split(command_string)
        
        # Execute without the shell
        result = subprocess.run(args, shell=False, capture_output=True, text=True, check=True)
        return f"Success:\n{result.stdout}"
        
    except subprocess.CalledProcessError as e:
        return f"Command failed with error code {e.returncode}:\n{e.stderr}"
    except Exception as e:
        return f"System error executing command: {str(e)}"