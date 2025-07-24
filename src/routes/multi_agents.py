import json
from fastapi import APIRouter, Depends, HTTPException, Request, Query, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ..database.db import (create_challenge_quota, get_challenge_quota, reset_quota_if_needed, )
from ..database.models import get_db
from typing import Optional
from langchain_core.messages import HumanMessage, AIMessageChunk
from uuid import uuid4
from ..agents.researcher import graph
from ..utils import authenticate_and_get_user_details
from .auth import db_dependency, active_user_dependnecy



router = APIRouter()


def serialise_ai_message_chunk(chunk):
    """Serialization func"""
    if(isinstance(chunk, AIMessageChunk)):
        return chunk.content
    raise TypeError(f"Object of type {type(chunk).__name__} is not in the correct format for serialization")

async def generate_chat_response(message: str, checkpoint_id: Optional[str] = None):
    """Func for generate ai response"""
    is_new_conversation = checkpoint_id is None

    if is_new_conversation:
        # Checkpoint_id generation
        new_checkpoint_id = str(uuid4())

        config = {
            "configurable": {"thread_id": new_checkpoint_id}
        }

        # first message initialization
        events = graph.astream_events({"messages": [HumanMessage(content=message)]}, version="v2", config=config)

        #Sending checkpoint ID
        yield  f'data: {{"type":"checkpoint","checkpoint_id":"{new_checkpoint_id}"}}\n\n'
            
    else:
        config = {"configurable": {"thread_id": checkpoint_id}}
        # Existing message continuation
        events = graph.astream_events({"messages": [HumanMessage(content=message)]}, version="v2", config=config)
    
    async for event in events:
        event_type = event["event"]
# payload = {"type": "content", "content": chunk_content}
# yield f"data: {json.dumps(payload)}\n\n"
        # For content stream
        if event_type == "on_chat_model_stream":
            chunk_content = serialise_ai_message_chunk(event["data"]["chunk"])
            # Escaping single quotes and newlines for JSON parsing
            # safe_content = chunk_content.replace('"', '\\"').replace("\n","\\n" )
            safe_content = {"type": "content", "content": chunk_content}
            yield f'data: {json.dumps(safe_content)}\n\n'

        # For retrieving query args and indicating the start of a search
        elif event_type == "on_chat_model_end":
            tool_calls = event["data"]["output"].tool_calls if hasattr(event["data"]["output"], "tool_calls") else []
            search_calls = [call for call in tool_calls if call["name"] == "tavily_search_results_json"]

            if search_calls:
                # Signalling the start of a search in the frontend
                search_query = search_calls[0]["args"].get("query", "")
                # Escaping quotes and special characters
                safe_query = search_query.replace('"', '\\"').replace("\n", "\\n")
                yield f'data: {{"type":"search_start","query":"{safe_query}"}}\n\n'
        
        # For retrieving research urls
        elif event_type == "on_tool_end" and event["name"] == "tavily_search_results_json":
            # Search completed - send results or error
            # -------------********------------
            # output = event["data"]["output"]
            output = event["data"]["output"]

            # Check if output is list
            if isinstance(output, list):
                # Extracting URLs from list of search results
                urls = []
                for item in output:
                    if isinstance(item, dict) and "url" in item:
                        urls.append(item["url"])
                
                # Url conversion to JSON and yileding
                urls_to_json = json.dumps(urls)
                yield f'data: {{"type": "search_results", "urls": {urls_to_json}}}\n\n'

    yield f'data: {{"type": "end"}}\n\n'



@router.get("/researcher")
async def researcher(message:str, request_obj: Request, db: db_dependency, user_details: active_user_dependnecy, checkpoint_id: Optional[str] = Query(None) ):


    try:
        user_id = user_details.id
        quota = get_challenge_quota(db, user_id)
        # print("🐳🐳🐳🐳1:", quota.user_id)

        if not quota:
            quota = create_challenge_quota(db, user_id)
        quota = reset_quota_if_needed(db, quota)
        # print("🐳🐳🐳🐳2:", quota.quota_remaining)

        if quota.quota_remaining <= 0:
            raise HTTPException(status_code=429, detail="Insufficient Quota")
        
        quota.quota_remaining -= 1
        db.commit()

        return StreamingResponse(generate_chat_response(message, checkpoint_id), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=429, detail="Insufficient Quota")