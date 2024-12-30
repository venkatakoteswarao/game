from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import random
import json
import asyncio
import os
import logging

# Initialize app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with specific domains in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enable logging
logging.basicConfig(level=logging.INFO)

# Active WebSocket connections
active_connections = []

# Game state
game_state = {
    "word_to_guess": "",
    "guessed_players": [],
    "scores": {},
    "used_words": set(),
    "time_left": 60,
    "passcode": None,
}

# Path to word list file
WORD_FILE_PATH = os.path.join(os.path.dirname(__file__), "word_list.txt")

# Load words
def load_words(file_path):
    try:
        with open(file_path, "r") as file:
            return [line.strip() for line in file if len(line.strip()) >= 5]
    except FileNotFoundError:
        logging.error("Word list file not found.")
        return []

word_list = load_words(WORD_FILE_PATH)

# Broadcast message
async def broadcast_message(message: str):
    for connection in active_connections:
        try:
            await connection.send_text(message)
        except Exception:
            active_connections.remove(connection)

# Timer logic
async def start_timer():
    while game_state["time_left"] > 0:
        await asyncio.sleep(1)
        game_state["time_left"] -= 1
        await broadcast_message(f"Time left: {game_state['time_left']} seconds")
    await broadcast_message("Time is up!")

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the Guess the Word WebSocket server!"}

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    logging.info("New WebSocket connection established.")

    try:
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                action = message.get("action")
                if not action:
                    await websocket.send_text("Invalid message format.")
                    continue

                # Process actions
                if action == "create_game":
                    # Logic for creating the game
                    ...
                elif action == "join_game":
                    # Logic for joining the game
                    ...
                elif action == "start_game":
                    asyncio.create_task(start_timer())
                    ...
                elif action == "guess_word":
                    # Logic for guessing words
                    ...
                elif action == "leaderboard":
                    # Logic for leaderboard
                    ...
            except json.JSONDecodeError:
                await websocket.send_text("Invalid JSON format.")
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logging.info("WebSocket connection closed.")

# Graceful shutdown
@app.on_event("shutdown")
async def shutdown():
    for connection in active_connections:
        await connection.close()
    active_connections.clear()

