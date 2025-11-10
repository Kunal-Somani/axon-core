import speech_recognition as sr
import pyttsx3
import requests
import datetime
import time

# --- Configuration ---
AXON_API_URL = "http://127.0.0.1:8000/chat"
OLLAMA_MODEL = "gemma:latest" # The model your API is using
WAKE_WORD = "axon" # Wake word to activate listening

# --- Text-to-Speech (TTS) Setup ---
try:
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id) # [1] is often female
except Exception as e:
    print(f"Warning: Could not initialize pyttsx3. {e}")
    engine = None

def speak(audio_text):
    """Uses pyttsx3 to speak the given text."""
    print(f"Axon: {audio_text}")
    if engine:
        engine.say(audio_text)
        engine.runAndWait()
    else:
        print("(TTS not available)")

# --- Speech-to-Text (STT) Setup ---
recognizer = sr.Recognizer()

def take_command():
    """Listens for user voice input and returns it as text."""
    with sr.Microphone() as source:
        print("\nListening...")
        recognizer.pause_threshold = 1
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        print("Recognizing...")
        query = recognizer.recognize_google(audio, language='en-in')
        print(f"User said: {query}\n")
        return query.lower()
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
        return "none"
    except sr.RequestError as e:
        print(f"Could not request results from Google service; {e}")
        return "none"
    except Exception as e:
        print(f"Error during recognition: {e}")
        return "none"

# --- Main Loop ---
def main():
    """Main execution loop for the voice client."""
    speak("Axon voice client activated. Say the wake word to begin.")
    
    while True:
        query = take_command()
        
        if WAKE_WORD in query:
            speak("Yes?")
            # We got the wake word, now listen for the actual command
            command = take_command()
            
            if command == "none":
                speak("I'm listening, please repeat your command.")
                continue

            # --- Exit Conditions ---
            if 'exit' in command or 'goodbye' in command or 'stop' in command:
                speak("Goodbye! Deactivating Axon.")
                break
            
            # --- Send to API ---
            if command:
                try:
                    # Send the query to our FastAPI backend
                    response = requests.post(AXON_API_URL, json={
                        "query": command,
                        "model": OLLAMA_MODEL
                    })
                    response.raise_for_status() # Raise an error for bad responses
                    
                    data = response.json()
                    
                    if "response" in data:
                        speak(data["response"])
                    else:
                        speak("Sorry, I received an unknown error from the server.")

                except requests.exceptions.RequestException as e:
                    print(f"API Error: {e}")
                    speak("I'm having trouble connecting to my brain. Please check the API server.")
        
        elif query == "none":
            # Don't do anything if recognition failed
            pass
        else:
            # Heard something, but not the wake word
            print(f"(Heard: {query}) - Waiting for wake word '{WAKE_WORD}'...")
            
        time.sleep(0.5)

if __name__ == "__main__":
    main()