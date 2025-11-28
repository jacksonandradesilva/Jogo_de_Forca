from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import json

from models import *
from database import Database
from game_logic import HangmanGame

app = FastAPI(title="JOGO DE FORCA API", version="1.0.0")

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar banco de dados
db = Database()

# Dicionário para armazenar jogos em andamento (em produção, use Redis ou DB)
active_games = {}

@app.post("/players", response_model=PlayerResponse)
async def create_player(player: PlayerCreate):
    """Cria um novo jogador"""
    try:
        player_id = db.execute_query(
            "INSERT INTO players (name) VALUES (?)",
            (player.name,)
        )
        return PlayerResponse(player_id=player_id, name=player.name)
    except sqlite3.IntegrityError:
        # Se o jogador já existe, retorna seus dados
        result = db.fetch_one(
            "SELECT player_id, name FROM players WHERE name = ?",
            (player.name,)
        )
        if result:
            return PlayerResponse(player_id=result[0], name=result[1])
        raise HTTPException(status_code=400, detail="Erro ao criar jogador")

@app.get("/players/{player_id}", response_model=PlayerResponse)
async def get_player(player_id: int):
    """Obtém dados de um jogador"""
    result = db.fetch_one(
        "SELECT player_id, name FROM players WHERE player_id = ?",
        (player_id,)
    )
    if not result:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")
    return PlayerResponse(player_id=result[0], name=result[1])

@app.post("/hangman/start", response_model=GameResponse)
async def start_game(game_start: GameStart):
    """Inicia uma nova partida de forca"""
    
    # Verifica se o jogador existe
    player = db.fetch_one(
        "SELECT player_id FROM players WHERE player_id = ?",
        (game_start.player_id,)
    )
    if not player:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")
    
    # Seleciona palavra secreta
    if game_start.word:
        secret_word = game_start.word.upper()
    else:
        secret_word = HangmanGame.select_random_word()
    
    masked_word = HangmanGame.create_masked_word(secret_word)
    
    # Insere o jogo no banco de dados
    game_id = db.execute_query(
        """INSERT INTO games 
           (player_id, secret_word, masked_word, attempts_left, status) 
           VALUES (?, ?, ?, ?, ?)""",
        (game_start.player_id, secret_word, masked_word, HangmanGame.MAX_ATTEMPTS, "IN_PROGRESS")
    )
    
    return GameResponse(
        game_id=game_id,
        masked_word=HangmanGame.format_masked_word(masked_word),
        attempts_left=HangmanGame.MAX_ATTEMPTS,
        status="IN_PROGRESS",
        tried_letters=[]
    )

@app.post("/hangman/guess", response_model=GameResponse)
async def make_guess(guess: GuessRequest):
    """Faz uma tentativa de letra"""
    
    # Busca o jogo
    game = db.fetch_one(
        """SELECT game_id, player_id, secret_word, masked_word, 
                  attempts_left, tried_letters, status 
           FROM games WHERE game_id = ?""",
        (guess.game_id,)
    )
    
    if not game:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    
    game_id, player_id, secret_word, masked_word, attempts_left, tried_letters_str, status = game
    
    # Verifica se o jogo ainda está em andamento
    if status != "IN_PROGRESS":
        raise HTTPException(status_code=400, detail="Jogo já finalizado")
    
    letter = guess.letter.upper()
    
    # Converte tried_letters de string para lista
    tried_letters = tried_letters_str.split(",") if tried_letters_str else []
    
    # Verifica se a letra já foi tentada
    if letter in tried_letters:
        raise HTTPException(status_code=400, detail="Letra já tentada")
    
    # Adiciona a letra às tentadas
    tried_letters.append(letter)
    tried_letters_str = ",".join(tried_letters)
    
    hit = letter in secret_word
    
    if hit:
        # Atualiza a palavra mascarada
        new_masked_word = HangmanGame.update_masked_word(secret_word, masked_word, letter)
        masked_word = new_masked_word
        
        # Verifica se ganhou
        if HangmanGame.check_win(new_masked_word):
            status = "WIN"
    else:
        # Diminui tentativas restantes
        attempts_left -= 1
        # Verifica se perdeu
        if attempts_left == 0:
            status = "LOSE"
    
    # Atualiza o jogo no banco
    db.execute_query(
        """UPDATE games 
           SET masked_word = ?, attempts_left = ?, tried_letters = ?, status = ?
           WHERE game_id = ?""",
        (masked_word, attempts_left, tried_letters_str, status, game_id)
    )
    
    return GameResponse(
        game_id=game_id,
        masked_word=HangmanGame.format_masked_word(masked_word),
        attempts_left=attempts_left,
        hit=hit,
        status=status,
        tried_letters=tried_letters
    )

@app.get("/hangman/status/{game_id}", response_model=GameResponse)
async def get_game_status(game_id: int):
    """Retorna o status atual do jogo"""
    
    game = db.fetch_one(
        """SELECT game_id, secret_word, masked_word, attempts_left, 
                  tried_letters, status 
           FROM games WHERE game_id = ?""",
        (game_id,)
    )
    
    if not game:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    
    _, secret_word, masked_word, attempts_left, tried_letters_str, status = game
    
    tried_letters = tried_letters_str.split(",") if tried_letters_str else []
    
    return GameResponse(
        game_id=game_id,
        masked_word=HangmanGame.format_masked_word(masked_word),
        attempts_left=attempts_left,
        status=status,
        tried_letters=tried_letters
    )

@app.get("/hangman/scoreboard", response_model=List[ScoreboardEntry])
async def get_scoreboard():
    """Retorna o ranking de jogadores"""
    
    results = db.fetch_all('''
        SELECT 
            p.name,
            COUNT(g.game_id) as games_played,
            SUM(CASE WHEN g.status = 'WIN' THEN 1 ELSE 0 END) as games_won
        FROM players p
        LEFT JOIN games g ON p.player_id = g.player_id
        GROUP BY p.player_id, p.name
        ORDER BY games_won DESC, games_played DESC
    ''')
    
    scoreboard = []
    for name, games_played, games_won in results:
        win_rate = (games_won / games_played * 100) if games_played > 0 else 0
        scoreboard.append(
            ScoreboardEntry(
                player_name=name,
                games_played=games_played,
                games_won=games_won,
                win_rate=round(win_rate, 2)
            )
        )
    
    return scoreboard

@app.get("/")
async def root():
    return {"message": "Hangman Game API - Use /docs para ver a documentação"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)