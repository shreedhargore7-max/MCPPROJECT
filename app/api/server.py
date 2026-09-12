from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.agent.graph import run_agent


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="MCPPROJECT Agent API",
    description="Multi-source project management AI agent",
    version="1.0.0",
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# REQUEST MODEL
# =========================================================

class AgentRequest(BaseModel):
    user_query: str


# =========================================================
# ROOT / HEALTH CHECK
# =========================================================

@app.get("/")
def root():
    return {
        "status": "running",
        "message": "MCPPROJECT Agent API is running."
    }


# =========================================================
# AGENT ENDPOINT
# =========================================================

@app.post("/agent")
def agent_endpoint(request: AgentRequest):

    result = run_agent(
        request.user_query
    )

    return result