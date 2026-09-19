from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import R2D2


app = FastAPI(title="R2D2 AI Backend")


# --------------------------------
# CORS
# --------------------------------

app.add_middleware(
    CORSMiddleware,

    # We will replace this with your actual
    # Squarespace domain later.
    allow_origins=[
        "*"
    ],

    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["Content-Type", "Authorization"],
)


# --------------------------------
# Request format
# --------------------------------

class ChatRequest(BaseModel):
    message: str


# --------------------------------
# Test endpoint
# --------------------------------

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "R2D2 backend is running"
    }


# --------------------------------
# Chat endpoint
# --------------------------------

@app.post("/chat")
async def chat(request: ChatRequest):

    if not request.message.strip():
        return {
            "error": "Message is empty"
        }

    try:

        response = R2D2.sendToGemini(
            request.message
        )

        return {
            "response": response
        }

    except Exception as e:

        print("R2D2 ERROR:")
        print(e)

        return {
            "error": "R2D2 failed to process the request"
        }