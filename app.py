from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import random
import json
import asyncio

app = FastAPI()

# Active WebSocket connections
active_connections = []

# Game state
game_state = {
    "word_to_guess": "",
    "guessed_players": [],
    "scores": {},
    "used_words": set(),  # Track used words to avoid repetition
    "time_left": 60,  # Default time for each word
    "passcode": None  # Passcode for joining the game
}

# Path to the word list file
WORD_FILE_PATH = "word_list.txt"

# Function to load words from the text file
def load_words(file_path):
    with open(file_path, "r") as file:
        return [line.strip() for line in file if len(line.strip()) >= 5]

# Load words at startup
word_list = load_words(WORD_FILE_PATH)

# Broadcast message to all clients
async def broadcast_message(message: str):
    for connection in active_connections:
        await connection.send_text(message)

# Add a root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the Guess the Word WebSocket server!"}

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["action"] == "create_game":
                host_name = message["host_name"]
                passcode = message["passcode"]
                game_state["passcode"] = passcode
                game_state["scores"] = {host_name: 0}
                game_state["guessed_players"] = []
                game_state["used_words"] = set()
                game_state["time_left"] = 60
                game_state["word_to_guess"] = random.choice(word_list)
                await websocket.send_text(f"Game created! Passcode: {passcode}")

            elif message["action"] == "join_game":
                player_name = message["player_name"]
                passcode = message["passcode"]
                if passcode != game_state["passcode"]:
                    await websocket.send_text("Invalid passcode!")
                else:
                    game_state["scores"][player_name] = 0
                    await websocket.send_text(f"Welcome {player_name}! Your score is 0.")
                    await broadcast_message(f"{player_name} joined the game!")

            elif message["action"] == "start_game":
                await broadcast_message(f"Game started! First word to guess: {'_ ' * len(game_state['word_to_guess'])}")

            elif message["action"] == "guess_word":
                player_name = message["player_name"]
                guess = message["guess"]
                if guess.upper() == game_state["word_to_guess"]:
                    game_state["scores"][player_name] += 10
                    game_state["guessed_players"].append(player_name)
                    await broadcast_message(f"{player_name} guessed correctly! The word was {game_state['word_to_guess']}")
                    await broadcast_message(f"Scores: {game_state['scores']}")
                    next_word = random.choice([w for w in word_list if w not in game_state["used_words"]])
                    game_state["used_words"].add(next_word)
                    game_state["word_to_guess"] = next_word
                    await broadcast_message(f"Next word to guess: {'_ ' * len(next_word)}")
                else:
                    await websocket.send_text("Incorrect guess. Try again!")

            elif message["action"] == "leaderboard":
                leaderboard = sorted(game_state["scores"].items(), key=lambda x: x[1], reverse=True)
                await websocket.send_text(json.dumps({"leaderboard": leaderboard}))

    except WebSocketDisconnect:
        active_connections.remove(websocket)
