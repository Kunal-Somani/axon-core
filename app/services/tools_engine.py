import subprocess
import os
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://172.17.0.1:11434")
llm = ChatOllama(model="gemma:latest", base_url=OLLAMA_HOST)

# Strict prompt to force Gemma to output ONLY a bash command
template = """You are a senior system administrator running on a Linux machine.
Translate the user's request into a single, valid bash command.
OUTPUT ONLY THE RAW COMMAND. Do not include markdown formatting, backticks, or explanations. 

User Request: {request}
Command:"""

prompt = PromptTemplate.from_template(template)

def execute_system_command(user_request: str) -> str:
    """Uses Gemma to generate a bash command, executes it, and returns the output."""
    try:
        # 1. Generate the command using our local LLM
        chain = prompt | llm | StrOutputParser()
        raw_command = chain.invoke({"request": user_request}).strip()
        
        # Clean up Markdown if the LLM gets chatty
        if raw_command.startswith("```bash"): 
            raw_command = raw_command[7:]
        elif raw_command.startswith("```"): 
            raw_command = raw_command[3:]
            
        if raw_command.endswith("```"): 
            raw_command = raw_command[:-3]
            
        command = raw_command.strip()

        print(f"--- [TOOLS] Attempting to execute: {command} ---")
        
        # 2. Execute the command securely via Python subprocess
        # NOTE: This executes inside the Docker container environment
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=15 # Prevent infinite hanging commands
        )
        
        if result.returncode == 0:
            output = result.stdout.strip() if result.stdout else "Command executed successfully with no output."
            return f"Executed: `{command}`\n\nResult:\n{output}"
        else:
            return f"Command Failed: `{command}`\n\nError:\n{result.stderr.strip()}"
            
    except Exception as e:
        return f"Failed to execute tool pipeline: {str(e)}"