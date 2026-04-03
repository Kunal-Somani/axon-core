import requests
import time
import os
import subprocess # Import subprocess for the execution step

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
    
    # 1. TOOLS/ACTIONS (Highest priority)
    tool_keywords = ["time", "open", "what's the date", "install", "package", "software"]
    if any(keyword in query_lower for keyword in tool_keywords):
        print("(Routing to: Tools/Gemini)")
        return ENDPOINT_TOOLS

    # 2. RAG (Personal Knowledge)
    rag_keywords = ["resume", "kunal", "skills", "project", "contact"]
    if any(keyword in query_lower for keyword in rag_keywords):
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
                    server_response = data["response"]
                    
                    # --- NEW: Confirmation Logic ---
                    if server_response.startswith("EXECUTE_CMD:"):
                        command_to_run = server_response.split(":", 1)[1]
                        
                        print(f"Axon wants to run: {command_to_run}")
                        confirmation = input("Is this okay? (y/n): ")
                        
                        if confirmation.lower().strip() == 'y':
                            print("Okay, running the command...")
                            try:
                                # Run the command safely
                                subprocess.run(command_to_run, shell=True, check=True)
                                print("Axon: The command finished successfully.")
                            except subprocess.CalledProcessError as e:
                                print(f"Axon: The command failed with an error: {e}")
                            except Exception as e:
                                print(f"Axon: An error occurred while running the command: {e}")
                        else:
                            print("Axon: Okay, I will not run the command.")
                    # --- End Confirmation Logic ---
                    
                    else:
                        # Not a command, just a normal answer
                        print(f"Axon: {server_response}")
                        
                elif "error" in data:
                    print(f"Axon Server Error: {data['error']}")
                else:
                    print("Axon: Received an unknown response.")

            except requests.exceptions.RequestException as e:
                print(f"Connection Error: I'm having trouble connecting to my brain. Is the 'axon_main.py' server running?")
        
        print("") # Add a newline for spacing

if __name__ == "__main__":
    main()