import google.generativeai as genai
import json
import os

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
router_model = genai.GenerativeModel('gemini-2.5-flash')

def route_query(query: str) -> str:
    """
    Returns the designated endpoint route based on semantic intent.
    """
    prompt = f"""
    You are a highly precise semantic router for an AI assistant. 
    Analyze the user's query and output ONLY a JSON object with a "route" key.
    
    Routes available:
    - "tools": If the user wants to execute a system command, install software, check time, or open a URL.
    - "rag": If the user is asking about Kunal's resume, skills, personal projects, or background.
    - "general": For all other general knowledge, chit-chat, or coding questions.
    
    User Query: "{query}"
    
    Output format: {{"route": "selected_route"}}
    """
    
    try:
        response = router_model.generate_content(prompt)
        # Parse the JSON safely (assuming the model follows instructions)
        result = json.loads(response.text.strip('```json\n').strip('```'))
        return result.get("route", "general")
    except Exception as e:
        print(f"Routing error: {e}. Defaulting to general.")
        return "general"