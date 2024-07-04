from flask import Flask, render_template, request, jsonify
from src.interactive_game import game
import threading
import webbrowser
import random

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('game.html')

@app.route('/game_state')
def game_state():
    return jsonify(game.get_game_state())

@app.route('/make_choice', methods=['POST'])
def make_choice():
    choice = request.json['choice']
    return jsonify(game.make_choice(choice))

def run_server():
    port = random.randint(5000, 8000)  # Choose a random port to avoid conflicts
    url = f"http://localhost:{port}"
    threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    app.run(port=port, debug=False)

if __name__ == '__main__':
    run_server()
