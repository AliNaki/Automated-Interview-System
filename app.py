from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.base import TaskResult
from autogen_core.models import ModelInfo
from dotenv import load_dotenv
import os
import uvicorn 

from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


load_dotenv()

app = FastAPI()


# 1. Mount Static Files and Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")



GROQ_API_KEY = os.getenv("GROQ_API_KEY")
model_client = OpenAIChatCompletionClient(
    model="llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
    model_info=ModelInfo(
        vision=False,
        function_calling=True,
        json_output=True,
        family="unknown",
        structured_output=True,
    ),
)



# --- WebSocket Handler ---
class WebSocketInputHandler:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket

    async def get_input(self, prompt: str, cancellation_token: Optional[object] = None) -> str:
        try:
            # Signal frontend that it's user's turn
            await self.websocket.send_text("SYSTEM_TURN:USER")
            data = await self.websocket.receive_text()
            return data
        except WebSocketDisconnect:
            print("Client disconnected during input wait.")
            return "TERMINATE"
        


async def create_interview_team(websocket: WebSocket, job_position: str, rounds: int):
    handler = WebSocketInputHandler(websocket)

    interviewer = AssistantAgent(
        name="Interviewer",
        model_client=model_client,
        description=f"Interviewer for {job_position}",
        system_message=f'''
        You are a professional interviewer for a {job_position} position.
        Ask one clear question at a time.
        Ask {rounds} questions total (Technical, Problem Solving, Culture).
        After {rounds} questions, say 'TERMINATE'.
        Keep questions under 50 words.
        '''
    )

    candidate = UserProxyAgent(
        name="Candidate",
        description="The candidate",
        input_func=handler.get_input 
    )

    evaluator = AssistantAgent(
        name="Evaluator",
        model_client=model_client,
        description="Career Coach",
        system_message=f'''
        You are a career coach. Give very brief feedback (max 40 words) on the candidate's answer.
        '''
    )

    terminate_condition = TextMentionTermination(text="TERMINATE")

    return RoundRobinGroupChat(
        participants=[interviewer, candidate, evaluator],
        termination_condition=terminate_condition,
        max_turns=rounds * 5 # Allow enough turns for dialogue per question
    )


# --- Routes ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # Render the index.html template
    return templates.TemplateResponse("index.html", {"request": request})


@app.websocket("/ws/interview")
async def websocket_endpoint(websocket: WebSocket, pos: str = Query("AI Engineer"), rounds: int = Query(3)):
    await websocket.accept()
    try:
        team = await create_interview_team(websocket, pos, rounds)
        
        await websocket.send_text(f"SYSTEM_INFO:Starting interview for {pos} ({rounds} rounds)...")

        async for message in team.run_stream(task='Start the interview.'):
            if isinstance(message, TaskResult):
                await websocket.send_text(f"SYSTEM_END:{message.stop_reason}")
            else:
                await websocket.send_text(f"{message.source}:{message.content}")

    except WebSocketDisconnect:
        print("WebSocket disconnected.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)