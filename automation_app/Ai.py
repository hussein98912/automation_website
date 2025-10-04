import json
import openai
import os
from dotenv import load_dotenv

load_dotenv() 

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You are a helpful AI assistant for an Automation Services company.
Use the company's Knowledge Base when possible to answer questions accurately.
Talk to customers in a friendly, interactive way.
You can suggest workflow names and workflow details for the user if they ask.
"""

# تحميل Knowledge Base
with open("Knlowagebase.json", "r", encoding="utf-8") as f:
    KNOWLEDGE_BASE = json.load(f)

def find_in_knowledge_base(user_message):
    msg = user_message.lower()
    if "hosting" in msg or "plan" in msg:
        return KNOWLEDGE_BASE.get("hosting")
    if "real estate" in msg or "property" in msg:
        return KNOWLEDGE_BASE["automation"].get("real_estate")
    if "ecommerce" in msg or "store" in msg:
        return KNOWLEDGE_BASE["automation"].get("ecommerce")
    if "restaurant" in msg or "cafe" in msg:
        return KNOWLEDGE_BASE["automation"].get("restaurants")
    if "hotel" in msg:
        return KNOWLEDGE_BASE["automation"].get("hotels")
    if "camera" in msg or "surveillance" in msg:
        return KNOWLEDGE_BASE["security"].get("cameras")
    if "access" in msg or "door" in msg:
        return KNOWLEDGE_BASE["security"].get("access_control")
    for service in KNOWLEDGE_BASE.get("services", []):
        if service["title"].lower() in msg or any(f.lower() in msg for f in service["features"]):
            return service
    return None

def ai_chat_response(user_message, conversation_history=[]):
    kb_info = find_in_knowledge_base(user_message)
    kb_text = ""
    if kb_info:
        kb_text = "Use this information to answer the customer:\n" + json.dumps(kb_info, indent=2)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for entry in conversation_history:
        messages.append({"role": "user", "content": entry["q"]})
        messages.append({"role": "assistant", "content": entry["a"]})
    messages.append({"role": "user", "content": kb_text + "\nCustomer: " + user_message})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    return response.choices[0].message["content"]

# وظائف إضافية لتوليد اقتراحات للوركفلو
def suggest_workflow_name(user_message):
    prompt = f"Suggest a short creative workflow name for: {user_message}"
    return ai_chat_response(prompt)

def suggest_workflow_details(user_message):
    prompt = f"Suggest detailed steps and tasks for a workflow about: {user_message}"
    return ai_chat_response(prompt)
