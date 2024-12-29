from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import random
import json

app = FastAPI()

# List to store active connections
active_connections = []

# Load words from a file
word_list = []
try:
    with open("word_list.txt", "r") as file:
        word_list = [word.strip().upper() for word in file.readlines() if len(word.strip()) >= 5]
except FileNotFoundError:
    print("word_list.txt not found. Please ensure the file exists and contains words.")

# Game state
game_state = {
    "word_to_guess": "",
    "guessed_players": [],
    "scores": {},
    "time_left": 60,  # Default time in seconds
    "used_words": []  # Track words already used in the match
}

# Broadcast message to all clients
async def broadcast_message(message: str):
    for connection in active_connections:
        await connection.send_text(message)

# Select a new word, avoiding repeats
def select_new_word():
    available_words = [word for word in word_list if word not in game_state["used_words"]]
    if not available_words:  # All words have been used
        return None
    selected_word = random.choice(available_words)
    game_state["used_words"].append(selected_word)
    return selected_word

# WebSocket connection handling
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message['action'] == "create_game":
                game_state['used_words'] = []  # Reset used words for a new game
                new_word = select_new_word()
                if new_word:
                    game_state['word_to_guess'] = new_word
                    game_state['guessed_players'] = []
                    game_state['scores'] = {}
                    game_state['time_left'] = 60  # Reset timer
                    await broadcast_message(f"New game started! Word: {'_ ' * len(game_state['word_to_guess'])}")
                else:
                    await websocket.send_text("Error: No more words available in the word list.")
            
            elif message['action'] == "join_game":
                player_name = message['player_name']
                if player_name not in game_state['scores']:
                    game_state['scores'][player_name] = 0
                await websocket.send_text(f"Welcome {player_name}! Your score is 0.")
            
            elif message['action'] == "guess_word":
                player_name = message['player_name']
                guess = message['guess']
                if guess.upper() == game_state['word_to_guess']:
                    game_state['scores'][player_name] += 10  # Correct guess
                    game_state['guessed_players'].append(player_name)
                    await broadcast_message(f"{player_name} guessed the word correctly! The word was {game_state['word_to_guess']}")
                    await broadcast_message(f"Scores: {game_state['scores']}")
                    new_word = select_new_word()
                    if new_word:
                        game_state['word_to_guess'] = new_word
                        await broadcast_message(f"Next word: {'_ ' * len(game_state['word_to_guess'])}")
                    else:
                        await broadcast_message("No more words available in the word list. The match is over.")
                else:
                    await websocket.send_text("Incorrect guess, try again!")
                    
    except WebSocketDisconnect:
        active_connections.remove(websocket)
