from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_community.tools import TavilySearchResults
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import add_messages, StateGraph, END
from langchain_core.messages import ToolMessage,SystemMessage
from dotenv import load_dotenv
from typing import TypedDict, Annotated
import os
from datetime import datetime


load_dotenv()
model1= "mistralai/mistral-7b-instruct:free"
model2= "mistralai/mistral-small-3.2-24b-instruct:free"
g_model1= "gemini-2.0-flash-001"
g_model2 = "gemini-2.5-flash"
llm = ChatGoogleGenerativeAI(model=g_model2)
# llm = ChatOpenAI(model=model2, api_key=os.environ["open_router_api_key"], base_url="https://openrouter.ai/api/v1")
# llm = ChatOpenAI( model="gpt-4o")

# llm = ChatGroq(model="meta-llama/llama-4-scout-17b-16e-instruct", api_key=os.getenv("GROQ_API_KEY"))

search_tool = TavilySearchResults(max_results=4)
tools = [search_tool]
memory = MemorySaver()

llm_with_tools = llm.bind_tools(tools=tools)

class State(TypedDict):   
    """
    Graph state schema
    """
    messages: Annotated[list, add_messages]

async def model(state: State):
    """
    model node function
    """
    today = datetime.now()
    formatted = today.strftime("%Y-%m-%d")
    
    print("✅✅✅✅:",today, formatted)
    system_prompt = f"You are a well trained research assistant with a search tool at your disposal, the tool should be used only when necessary. While using the tool, results might point to different dates, in other to avoid confusion, todays date is {today}, in formatted string - {formatted}"


    result = await llm_with_tools.ainvoke([SystemMessage(content=system_prompt)] + state["messages"])
    return {"messages": [result]}

async def router(state: State):
    """
    router  function for control flow
    """
    last_message = state['messages'][-1]

    if (hasattr(last_message, "tool_calls") and len(last_message.tool_calls) > 0):
        return "tool_node"
    return "end"

async def tool_node(state):
    """Custom tool node that handles tool calls from LLM."""
    tool_calls = state["messages"][-1].tool_calls

    tool_messages = []

    for tool_call in tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_id = tool_call["id"]

        if tool_name == "tavily_search_results_json":
            search_results = await search_tool.ainvoke(tool_args) 
            tool_message = ToolMessage(content=str(search_results),tool_call_id = tool_id, name=tool_name)
            tool_messages.append(tool_message)
    
    return {"messages": tool_messages}

graph_form = StateGraph(State)
graph_form.add_node("model", model)
graph_form.add_node("tool_node", tool_node)

graph_form.set_entry_point("model")
graph_form.add_conditional_edges("model", router, {"tool_node":"tool_node", "end":END})
graph_form.add_edge("tool_node", "model")

graph = graph_form.compile(checkpointer=memory)