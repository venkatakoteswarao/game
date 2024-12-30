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
    allow_origins=[""],  # Replace "" with specific domains in production
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
            logging.error("Error sending message, removing connection.")
            active_connections.remove(connection)

# Timer logic
async def start_timer():
    while game_state["time_left"] > 0:
        await asyncio.sleep(1)
        game_state["time_left"] -= 1
        await broadcast_message(f"Time left: {game_state['time_left']} seconds")
    await broadcast_message("Time is up!")

# Reset game state
def reset_game():
    game_state.update({
        "word_to_guess": "",
        "guessed_players": [],
        "scores": {},
        "used_words": set(),
        "time_left": 60,
        "passcode": None,
    })

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
                    host_name = message["host_name"]
                    passcode = message["passcode"]
                    reset_game()
                    game_state["word_to_guess"] = random.choice(word_list)
                    game_state["scores"] = {host_name: 0}
                    game_state["passcode"] = passcode
                    await websocket.send_text(f"Game created! Passcode: {passcode}")

                elif action == "join_game":
                    player_name = message["player_name"]
                    passcode = message["passcode"]
                    if passcode != game_state["passcode"]:
                        await websocket.send_text("Invalid passcode!")
                    else:
                        game_state["scores"][player_name] = 0
                        await websocket.send_text(f"Welcome {player_name}! Your score is 0.")
                        await broadcast_message(f"{player_name} joined the game!")

                elif action == "start_game":
                    if not game_state["word_to_guess"]:
                        await websocket.send_text("No word set for the game. Create the game first!")
                    else:
                        asyncio.create_task(start_timer())
                        await broadcast_message(
                            f"Game started! Word to guess: {'_ ' * len(game_state['word_to_guess'])}"
                        )

                elif action == "guess_word":
                    player_name = message["player_name"]
                    guess = message["guess"]
                    if guess.upper() == game_state["word_to_guess"].upper():
                        game_state["scores"][player_name] += 10
                        game_state["guessed_players"].append(player_name)
                        await broadcast_message(f"{player_name} guessed the word! The word was {game_state['word_to_guess']}")
                        next_word = random.choice(
                            [w for w in word_list if w not in game_state["used_words"]]
                        )
                        game_state["used_words"].add(next_word)
                        game_state["word_to_guess"] = next_word
                        await broadcast_message(f"Next word: {'_ ' * len(next_word)}")
                    else:
                        await websocket.send_text("Incorrect guess, try again!")

                elif action == "leaderboard":
                    leaderboard = sorted(game_state["scores"].items(), key=lambda x: x[1], reverse=True)
                    await websocket.send_text(json.dumps({"leaderboard": leaderboard}))

                else:
                    await websocket.send_text("Unknown action.")

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
