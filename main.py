from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import json
import os

from agent.llm_utils import choose_agent
from agent.run import WebSocketManager
from agent.rabbit import RabbitTaskManager
from config import Config
CFG = Config()

class ResearchRequest(BaseModel):
    task: str
    report_type: str
    agent: str



app = FastAPI()
app.mount("/site", StaticFiles(directory="client"), name="site")
app.mount("/static", StaticFiles(directory="client/static"), name="static")
# Dynamic directory for outputs once first research is run
@app.on_event("startup")
def startup_event():
    if not os.path.isdir("outputs"):
        os.makedirs("outputs")
    app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

templates = Jinja2Templates(directory="client")

manager = WebSocketManager()


@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse('index.html', {"request": request, "report": None})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data.startswith("start"):
                json_data = json.loads(data[6:])
                task = json_data.get("task")
                report_type = json_data.get("report_type")
                agent = json_data.get("agent")
                # temporary so "normal agents" can still be used and not just auto generated, will be removed when we move to auto generated
                if agent == "Auto Agent":
                    agent_dict = choose_agent(task)
                    agent = agent_dict.get("agent")
                    agent_role_prompt = agent_dict.get("agent_role_prompt")
                else:
                    agent_role_prompt = None

                if task and report_type and agent:
                    agent_choice_message = {"type": "logs", "output": f"Initiated an Agent: {agent}"}
                    print(f"CFG.database_url: {CFG.database_url}")
                    rabbit=None
                    if CFG.save_in_db:
                        rabbit = RabbitTaskManager(task, agent, agent_role_prompt)
                        await rabbit.create_channel()
                        rabbit.publish_to_rabbit(json_data)
                        rabbit.publish_to_rabbit(agent_choice_message)
                    await websocket.send_json(agent_choice_message)
                    await manager.start_streaming(task, report_type, agent, agent_role_prompt, websocket, rabbit)
                else:
                    print("Error: not enough parameters provided.")

    except WebSocketDisconnect:
        await manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
