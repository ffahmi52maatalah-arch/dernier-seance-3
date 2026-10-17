import uvicorn
from fastapi import FastAPI
from langserve import add_routes

from agent import agent

app = FastAPI(title="LangChain Agent Server")

# Exposes /agent/invoke, /agent/stream, /agent/playground, ...
add_routes(app, agent, path="/agent")


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
