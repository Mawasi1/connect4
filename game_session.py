import uuid
import game_logic  # Make sure this import works based on your project structure
import game_ai  # Importing the game AI logic

class GameSession:
    def __init__(self, player1, player2=None, ai_difficulty=None):
        self.session_id = str(uuid.uuid4())
        self.board = game_logic.create_board()
        self.players = {player1: game_logic.PLAYER1}
        self.ai_difficulty = ai_difficulty  # Specify AI difficulty here
        if player2 is None and ai_difficulty:
            # AI game setup
            self.players["AI"] = game_logic.PLAYER2
        elif player2:
            # Two-player game setup
            self.players[player2] = game_logic.PLAYER2
        self.turn = game_logic.PLAYER1  # Player1 starts by default
        self.winner = None
        self.draw = False

    def make_move(self, column, player_id):
        """Attempt to make a move on the board and handle AI response if applicable."""
        player_token = self.players.get(player_id)
        # Check if it's the correct player's turn and if the move is valid
        if player_token == self.turn and 0 <= column < len(self.board[0]):
            move_made = game_logic.make_move(self.board, column, player_token)
            if move_made:
                # After making a move, check for win or draw
                if game_logic.check_win(self.board, player_token):
                    self.winner = player_id
                elif game_logic.is_draw(self.board):
                    self.draw = True
                else:
                    # Switch turns
                    self.switch_turns()
                
                # If it's now the AI's turn, make AI move
                if self.turn == game_logic.PLAYER2 and "AI" in self.players:
                    self.make_ai_move()
                return True
        return False

    def switch_turns(self):
        """Switch turns between PLAYER1 and PLAYER2."""
        self.turn = game_logic.PLAYER2 if self.turn == game_logic.PLAYER1 else game_logic.PLAYER1

    # Inside the GameSession class in game_session.py
    def make_ai_move(self):
        """Makes a move for the AI based on the specified difficulty."""
        if self.ai_difficulty and "AI" in self.players and self.turn == game_logic.PLAYER2:
            ai_column = game_ai.ai_move(self.board, self.ai_difficulty)
            print(f"AI chose column {ai_column} for its move.")

            if ai_column is not None:
                game_logic.make_move(self.board, ai_column, game_logic.PLAYER2)
                # Check for win or draw after AI's move
                if game_logic.check_win(self.board, game_logic.PLAYER2):
                    self.winner = "AI"
                elif game_logic.is_draw(self.board):
                    self.draw = True
                else:
                    self.switch_turns()  # It's now the human player's turn
                return ai_column  # Return the column where AI made its move for server notification
        return None  # AI did not make a move (should not happen in practice, included for completeness)




    def get_board_state(self):
        """Return the current game board."""
        return self.board

    def get_game_status(self):
        """Return the current game status (ongoing, win, or draw)."""
        if self.winner:
            return f"WIN {self.winner}"
        elif self.draw:
            return "DRAW"
        else:
            return "ONGOING"
    
    def serialize_board(self):
        return '\n'.join(['|'.join(row) for row in self.board])

