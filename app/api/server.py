from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

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
    user_query: str = Field(
        ...,
        min_length=1,
        description="User question or action request.",
    )

    project_name: str = Field(
        default="Project X",
        description="Project name used by the agent.",
    )

    approved: bool = Field(
        default=False,
        description=(
            "Explicit approval for an external "
            "Jira/Gmail action."
        ),
    )


# =========================================================
# ROOT / HEALTH CHECK
# =========================================================

@app.get("/")
def root():
    return {
        "status": "running",
        "message": "MCPPROJECT Agent API is running.",
    }


# =========================================================
# HEALTH ENDPOINT
# =========================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "MCPPROJECT Agent API",
    }


# =========================================================
# AGENT ENDPOINT
# =========================================================

@app.post("/run")
def run_endpoint(request: AgentRequest):
    """
    Main endpoint used by the frontend.

    Normal question:
        approved=False

    Action request:
        approved=False
        -> action is detected
        -> approval is requested

    Approved action:
        approved=True
        -> action can be executed
    """

    try:
        result = run_agent(
            user_query=request.user_query,
            project_name=request.project_name,
            approved=request.approved,
        )

        if result is None:
            raise HTTPException(
                status_code=500,
                detail="Agent returned no result.",
            )

        return result

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(exc)}",
        )


# =========================================================
# BACKWARD COMPATIBILITY
# =========================================================

@app.post("/agent")
def agent_endpoint(request: AgentRequest):
    """
    Backward-compatible endpoint.

    This allows older frontend code that still calls
    /agent to continue working.
    """

    try:
        result = run_agent(
            user_query=request.user_query,
            project_name=request.project_name,
            approved=request.approved,
        )

        if result is None:
            raise HTTPException(
                status_code=500,
                detail="Agent returned no result.",
            )

        return result

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(exc)}",
        )