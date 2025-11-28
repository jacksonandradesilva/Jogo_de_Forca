import random
from typing import List

class HangmanGame:
    # Lista de palavras para o jogo
    WORDS = [
        "CARRO", "CASA", "COMPUTADOR", "PYTHON", "PROGRAMACAO",
        "ELEFANTE", "GIRAFA", "MONTANHA", "OCEANO", "FLORESTA",
        "LIVRO", "ESCOLA", "UNIVERSIDADE", "TECLADO", "MONITOR"
    ]
    
    MAX_ATTEMPTS = 6

    @staticmethod
    def select_random_word() -> str:
        return random.choice(HangmanGame.WORDS)

    @staticmethod
    def create_masked_word(word: str) -> str:
        return "_" * len(word)

    @staticmethod
    def update_masked_word(secret_word: str, masked_word: str, letter: str) -> str:
        letter = letter.upper()
        new_masked = list(masked_word)
        
        for i, char in enumerate(secret_word):
            if char == letter:
                new_masked[i] = letter
                
        return "".join(new_masked)

    @staticmethod
    def check_win(masked_word: str) -> bool:
        return "_" not in masked_word

    @staticmethod
    def format_masked_word(masked_word: str) -> str:
        return " ".join(masked_word)