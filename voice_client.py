import speech_recognition as sr
import pyttsx3
import requests
import datetime
import time

# --- Configuration ---
API_BASE_URL = "http://127.0.0.1:8000"
ENDPOINT_OLLAMA = "/chat/ollama"
ENDPOINT_TOOLS = "/chat/tools"
ENDPOINT_RAG = "/chat/rag"
WAKE_WORD = "axon" # Activation keyword

# --- TTS and STT Setup ---
try:
    # Initialize Text-to-Speech engine
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)
except Exception as e:
    print(f"Warning: Could not initialize pyttsx3. {e}")
    engine = None

def speak(audio_text):
    """Uses pyttsx3 to speak the given text."""
    print(f"Axon: {audio_text}")
    if engine:
        engine.say(audio_text)
        engine.runAndWait()

recognizer = sr.Recognizer()

def take_command():
    """Listens for user voice input and returns it as text."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("\nListening...")
        r.pause_threshold = 1
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source)
    try:
        query = r.recognize_google(audio, language='en-in')
        print(f"User said: {query}\n")
        return query.lower()
    except Exception:
        print("Google Speech Recognition could not understand audio")
        return "none"

def choose_endpoint(query):
    """Decides which API endpoint to use based on keywords."""
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
    speak("Axon unified client activated. Say the wake word to begin.")
    
    while True:
        query = take_command()
        
        if WAKE_WORD in query:
            speak("Yes?")
            command = take_command()
            
            if command == "none":
                speak("I'm listening, please repeat your command.")
                continue

            if 'exit' in command or 'goodbye' in command or 'stop' in command:
                speak("Goodbye! Deactivating Axon.")
                break
            
            if command:
                endpoint = choose_endpoint(command)
                api_url = API_BASE_URL + endpoint
                
                payload = {"query": command}

                try:
                    response = requests.post(api_url, json=payload)
                    response.raise_for_status() 
                    
                    data = response.json()
                    
                    if "response" in data:
                        speak(data["response"])
                    elif "error" in data:
                        # Reports errors from the server (e.g., "Ollama not found")
                        speak(f"Sorry, an error occurred on the server: {data['error']}")
                    else:
                        speak("Sorry, I received an unknown response.")

                except requests.exceptions.RequestException as e:
                    # Reports connection errors (e.g., server is offline)
                    speak(f"Connection failed. Please ensure the Axon server is running.")
        
        elif query != "none":
            print(f"(Heard: {query}) - Waiting for wake word '{WAKE_WORD}'...")
            
        time.sleep(0.5)

if __name__ == "__main__":
    main()