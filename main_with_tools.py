import google.generativeai as genai
import webbrowser
import datetime
import os
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# --- Load Environment Variables ---
# This line loads the GOOGLE_API_KEY from your .env file
load_dotenv()

# --- Tool Definitions ---
# These are the Python functions our model will be able to call.

def get_current_time() -> str:
    """
    Returns the current date and time in a clear string format.
    Use this for any questions about the current time or date.
    """
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def open_url(url: str) -> str:
    """
    Opens a specified URL in the default web browser.
    Use this for any requests to open a website like Google, YouTube, etc.
    """
    try:
        webbrowser.open(url, new=2)
        return f"Successfully opened {url}"
    except Exception as e:
        return f"Error opening {url}: {e}"

# --- GenAI Setup ---
try:
    # 1. READ THE KEY FROM THE ENVIRONMENT
    #    (dotenv loaded this for os.getenv to find)
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not found. Make sure it's in your .env file.")
    
    # 2. Configure the library
    genai.configure(api_key=GOOGLE_API_KEY)
except ValueError as e:
    print(e)
    exit()

# 3. Define the tools for the model
gemini_tools = [
    {
        "name": "get_current_time",
        "description": "Get the current time and date.",
        "parameters": {}
    },
    {
        "name": "open_url",
        "description": "Open a given URL in a new browser tab.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "url": {
                    "type": "STRING",
                    "description": "The URL to open (e.g., https://www.google.com)"
                }
            },
            "required": ["url"]
        }
    }
]

# 4. Map tool names (strings) to the actual Python functions
available_tools = {
    "get_current_time": get_current_time,
    "open_url": open_url
}

# 5. Initialize the Gemini model with the tools
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",  # <-- UPDATED TO 2.5 PRO
    tools=gemini_tools
)

# --- FastAPI Server ---
app = FastAPI(
    title="Axon Core API (with Tools)",
    description="Assistant using Gemini 2.5 Pro for function calling (Phase 3).",
    version="3.0.0"
)

# --- Pydantic Models ---
class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    response: str

class ErrorResponse(BaseModel):
    error: str

# --- API Endpoints ---
@app.get("/", tags=["Status"])
def read_root():
    return {"status": "Axon Core (with Tools) is online"}

@app.post("/chat_tools",
          response_model=ChatResponse,
          tags=["Chat"],
          responses={500: {"model": ErrorResponse}, 400: {"model": ErrorResponse}})
async def chat_with_tools(request: ChatRequest):
    """
    Receives a query, lets Gemini decide to use a tool,
    executes the tool, and returns the final response.
    """
    try:
        chat = model.start_chat(enable_automatic_function_calling=False)
        response = chat.send_message(request.query)
        
        if not response.candidates[0].content.parts or not response.candidates[0].content.parts[0].function_call:
            return ChatResponse(response=response.candidates[0].content.parts[0].text)

        function_call = response.candidates[0].content.parts[0].function_call
        tool_name = function_call.name
        tool_args = dict(function_call.args)

        if tool_name not in available_tools:
            return {"error": f"Tool '{tool_name}' not found."}, 400

        function_to_call = available_tools[tool_name]
        print(f"Axon is executing tool: {tool_name} with args: {tool_args}")
        
        if tool_args:
            tool_response_string = function_to_call(**tool_args)
        else:
            tool_response_string = function_to_call()

        # 5. Send the tool's output back to the model
        #    THIS IS THE FIX for the 'FunctionResponse' error
        response = chat.send_message(
            {
                "function_response": {
                    "name": tool_name,
                    "response": {"result": tool_response_string}
                }
            },
        )
        
        final_response = response.candidates[0].content.parts[0].text
        return ChatResponse(response=final_response)

    except Exception as e:
        print(f"Error in /chat_tools: {e}")
        return {"error": str(e)}, 500

# --- Server Start ---
if __name__ == "__main__":
    print("Run the server with Uvicorn:")
    print("python -m uvicorn main_with_tools:app --reload")