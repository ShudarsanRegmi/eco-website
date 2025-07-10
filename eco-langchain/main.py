from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from dotenv import load_dotenv
import requests
import os

# Load API key from .env
load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")
org_id = os.getenv("OPENAI_ORGANIZATION_ID")
print("-"*100)
print(org_id)
app = FastAPI()

# Allow your React frontend to talk to this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # or your deployed domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chat request model
class Query(BaseModel):
    user_input: str

# Tool: Search items from your Node backend
def search_items(query: str) -> str:
    """Search for items in the donation pool based on user input."""
    try:
        res = requests.get(f"http://localhost:5000/items?q={query}")
        items = res.json()
        if not items:
            return "No matching items found in the donation pool."
        return "Here are some items you might like:\n" + "\n".join(i["name"] for i in items)
    except Exception as e:
        return f"Error while searching items: {str(e)}"

@app.post("/chat")
async def chat(query: Query):
    # Initialize the LLM
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.7,
        openai_api_key=openai_key,
        organization=org_id
    )

    # Create tools
    tools = [
        Tool(
            name="SearchItems",
            func=search_items,
            description="Search for items in the donation pool (listed products) based on user input.",
        ),
    ]

    # Create a prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that can search for items in a donation pool. Use the SearchItems tool when users ask about finding or looking for specific items."),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    # Create the agent
    agent = create_openai_tools_agent(llm, tools, prompt)
    
    # Create agent executor
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    # Run the agent with the new invoke method
    try:
        response = agent_executor.invoke({"input": query.user_input})
        return {"response": response["output"]}
    except Exception as e:
        return {"response": f"Error processing your request: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)