import re
import yaml
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.chat_models import ChatOllama
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    user_input: str

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

def add_item_to_api(item: dict) -> str:
    try:
        res = requests.post("http://localhost:5000/items", json=item)
        if res.status_code == 201:
            return "Awesome! The item has been successfully added to the donation pool."
        else:
            return f"Something went wrong. Status: {res.status_code} — {res.text}"
    except Exception as e:
        return f"Oops, couldn't add the item: {str(e)}"

@app.post("/chat")
async def chat(query: Query):
    user_input = query.user_input

    llm = ChatOllama(
        model="llama3.2-1b:latest",
        temperature=0.4,
        tags=["donation_bot", "user_chat"],
        metadata={"source": "fastapi", "feature": "chat_endpoint"},
    )

    planning_prompt = f"""
You're a helpful assistant in a donation platform.

You can take the following actions:
- answer directly (action: none)
- search items (action: search_items)
- add a new item to the donation list (action: add_item)

Your response MUST follow this YAML format exactly:

action: <none|search_items|add_item>
input: <search keyword or 'N/A'>
data:
  name: <item name or 'N/A'>
  category: <category or 'N/A'>
  description: <description or 'N/A'>
  price: <number or 'N/A'>
answer: <your friendly message to the user>

DO NOT use markdown or triple backticks.

Here's the user query: "{user_input}"
"""

    plan = llm.invoke(planning_prompt).content.strip()
    print("Raw plan:", plan)

    cleaned = re.sub(r"```yaml|```", "", plan)

    try:
        parsed = yaml.safe_load(cleaned)
        action = parsed.get("action", "none")
        tool_input = parsed.get("input", "")
        data = parsed.get("data", {})
        final_message = parsed.get("answer", "Let me know how I can assist you.")
    except Exception as e:
        return {"response": f"Sorry, I couldn’t understand the model’s response. Debug: {str(e)}"}

    if action.lower() == "search_items":
        items_response = search_items_from_api(tool_input)
        return {"response": f"{final_message}\n\n{items_response}"}

    elif action.lower() == "add_item":
        required = ["name", "category", "description", "price"]
        if not all(k in data and data[k] not in [None, "", "N/A"] for k in required):
            return {"response": "Sorry, I couldn't get all the details needed to add the item."}

        try:
            data["price"] = float(data["price"])
        except:
            return {"response": "The price value seems invalid. Please enter a number."}

        add_response = add_item_to_api(data)
        return {"response": f"{final_message}\n\n{add_response}"}

    else:
        return {"response": final_message}
