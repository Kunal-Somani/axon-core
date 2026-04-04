import google.generativeai as genai
import json
import os

api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)
router_model = genai.GenerativeModel('gemini-2.5-flash')

def route_query(query: str) -> str:
    prompt = f"""
    You are a highly precise semantic router for an AI assistant named Axon. 
    Analyze the user's query and output ONLY a valid JSON object with a "route" key.
    
    Routes available:
    - "tools": If the user wants to execute system commands (uname, ls, terminal tasks), install software, or check system stats.
    - "rag": Use this for ANY personal question. This includes:
        * Queries using 'Kunal', 'my', 'me', 'I', or 'am I'.
        * Questions about roll numbers, student IDs, college, degree, or current studies.
        * Questions about resume, skills, or projects.
    - "general": ONLY for generic jokes, general knowledge (e.g., "What is 2+2?"), or abstract coding help not involving Kunal's system.
    
    User Query: "{query}"
    
    Output format: {{"route": "selected_route"}}
    """
    
    try:
        print(f"\n--- [ROUTER] Analyzing Query: '{query}' ---")
        response = router_model.generate_content(prompt)
        raw_text = response.text.strip()
        print(f"--- [ROUTER] Gemini Raw Output: {raw_text} ---")
        
        # Safely strip Markdown formatting if Gemini adds it
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        elif raw_text.startswith("```"):
            raw_text = raw_text[3:]
            
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
            
        result = json.loads(raw_text.strip())
        route = result.get("route", "general")
        print(f"--- [ROUTER] Successfully Parsed Route: {route} ---\n")
        return route
        
    except Exception as e:
        print(f"\n--- [ROUTER FATAL ERROR] ---")
        print(f"Details: {str(e)}")
        print(f"Fallback triggered to 'general'\n")
        return "general"