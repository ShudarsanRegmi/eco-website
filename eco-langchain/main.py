from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.chat_models import ChatOllama
import requests
import re

app = FastAPI()

# Allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    user_input: str

# Tool function
def search_items_from_api(name: str) -> str:
    try:
        res = requests.get(f"http://localhost:5000/items?q={name}")
        res_data = res.json()

        if not res_data.get("success") or not res_data.get("data"):
            return "Hmm, I couldn't find any items that match your search."

        items = res_data["data"]
        response = "Here’s what I found:\n\n"
        for item in items:
            response += f"• **{item['name']}** ({item['category']}): {item['description']} — ₹{item['price']}\n"
        return response

    except Exception as e:
        return f"Oops! Something went wrong while fetching items: {str(e)}"

@app.post("/chat")
async def chat(query: Query):
    user_input = query.user_input
    llm = ChatOllama(model="llama3.2-1b:latest", temperature=0.4)

    # 1. Ask model if tool use is needed and what input to pass
    planning_prompt = f"""
You're a helpful assistant in a donation platform. 

You can either:
- answer directly (action: none)
- search items using our donation search tool (action: search_items)

If the user wants to know about available items, extract the most relevant keyword (like 'laptop', 'chair', or 'electronics').

Respond in this exact format:

action: <none|search_items>
input: <keyword if applicable>
answer: <your message to the user>

Now here's the user query: "{user_input}"
"""

    plan = llm.invoke(planning_prompt).content.strip()

    # Parse structured response
    try:
        action = re.search(r"action:\s*(.*)", plan).group(1).strip()
        tool_input = re.search(r"input:\s*(.*)", plan).group(1).strip()
        final_message = re.search(r"answer:\s*(.*)", plan, re.DOTALL).group(1).strip()
    except Exception as e:
        return {"response": f"Sorry, couldn't understand the response. Debug: {str(e)}"}

    # Route based on action
    if action.lower() == "search_items":
        items_response = search_items_from_api(tool_input)
        # Combine with AI-style response
        return {"response": f"{final_message}\n\n{items_response}"}
    else:
        return {"response": final_message}
