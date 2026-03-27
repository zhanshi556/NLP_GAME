from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from game_logic import generate_event

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class PlayRequest(BaseModel):
    playerState: dict
    action: str

@app.post("/api/play")
async def play(request: PlayRequest):
    event = await generate_event(request.playerState, request.action)
    return event

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)