from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.chat_models import ChatOllama
import requests

app = FastAPI()

# CORS for React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    user_input: str

# API tool to call Node backend
def search_items_from_api(name: str) -> str:
    try:
        res = requests.get(f"http://localhost:5000/items?q={name}")
        res_data = res.json()
        if not res_data.get("success") or not res_data.get("data"):
            return "Sorry, no items found that match your search."

        items = res_data["data"]
        response = "Here are the items I found:\n\n"
        for item in items:
            response += f"- **{item['name']}** ({item['category']}): {item['description']} — ₹{item['price']}\n"
        return response

    except Exception as e:
        return f"Error while searching: {str(e)}"

@app.post("/chat")
async def chat(query: Query):
    user_input = query.user_input
    llm = ChatOllama(model="llama3.2-1b:latest", temperature=0.3)

    # Step 1: System-guided prompt to check if tool needed
    classification_prompt = f"""
You are an assistant that helps users with donation-related queries.

If the user's question is about searching for an item (like "Do you have shoes?" or "I need a laptop"), respond ONLY with:

USE_SEARCH_TOOL
tool_input: <exact keyword to search>

If the query is general (not about items), just answer conversationally.

Now here's the user input:
"{user_input}"
"""
    decision = llm.invoke(classification_prompt).content.strip()

    if decision.startswith("USE_SEARCH_TOOL"):
        # Step 2: Extract tool input
        try:
            search_term = decision.split("tool_input:")[1].strip().strip('"')
            items_response = search_items_from_api(search_term)
            return {"response": items_response}
        except Exception as e:
            return {"response": f"Error parsing tool input: {str(e)}"}

    else:
        # No tool needed, respond normally
        chat_response = llm.invoke(user_input).content
        return {"response": chat_response}
