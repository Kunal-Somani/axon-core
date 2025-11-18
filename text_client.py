import requests
import time
import os

# --- Configuration ---
# These endpoints MUST match your axon_main.py server
API_BASE_URL = "http://127.0.0.1:8000"
ENDPOINT_OLLAMA = "/chat/ollama"
ENDPOINT_TOOLS = "/chat/tools"
ENDPOINT_RAG = "/chat/rag"

def choose_endpoint(query):
    """
    Decides which API endpoint to use based on keywords.
    (This is the exact same routing logic as your voice client)
    """
    query_lower = query.lower()
    
    # 1. TOOLS/ACTIONS (Highest priority for specific commands)
    if "time" in query_lower or "open" in query_lower or "what's the date" in query_lower:
        print("(Routing to: Tools/Gemini)")
        return ENDPOINT_TOOLS

    # 2. RAG (Personal Knowledge)
    if "resume" in query_lower or "kunal" in query_lower or "skills" in query_lower or "project" in query_lower or "contact" in query_lower:
        print("(Routing to: RAG/Ollama)")
        return ENDPOINT_RAG
        
    # 3. DEFAULT (General Chat)
    print("(Routing to: General/Ollama)")
    return ENDPOINT_OLLAMA

# --- Main Loop ---
def main():
    """Main execution loop for the text client."""
    print("--- Axon Text Client Activated ---")
    print("Your unified server (axon_main.py) must be running.")
    print("Type 'exit' or 'quit' to end the session.\n")
    
    while True:
        try:
            # 1. Get query from text input
            command = input("You: ")
        except EOFError:
            # Handle Ctrl+D or other EOF
            break

        if command.lower() in ["exit", "quit"]:
            print("Axon: Goodbye!")
            break
        
        if command:
            # 2. Choose the correct "brain"
            endpoint = choose_endpoint(command)
            api_url = API_BASE_URL + endpoint
            
            payload = {"query": command}

            try:
                # 3. Send request to the server
                response = requests.post(api_url, json=payload)
                response.raise_for_status() 
                
                data = response.json()
                
                # 4. Print the response
                if "response" in data:
                    print(f"Axon: {data['response']}")
                elif "error" in data:
                    print(f"Axon Server Error: {data['error']}")
                else:
                    print("Axon: Received an unknown response.")

            except requests.exceptions.RequestException as e:
                print(f"Connection Error: I'm having trouble connecting to my brain. Is the 'axon_main.py' server running?")
        
        print("") # Add a newline for spacing

if __name__ == "__main__":
    main()