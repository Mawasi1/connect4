import uuid
import game_logic  # Make sure this import works based on your project structure
import game_ai  # Importing the game AI logic

class GameSession:
    def __init__(self, player1, ai_difficulty=None, is_ai_game=False,num_wins=1):
        self.session_id = str(uuid.uuid4())
        self.board = game_logic.create_board()
        self.players = {player1: game_logic.PLAYER1}
        self.ai_difficulty = ai_difficulty
        self.is_ai_game = is_ai_game  # Now correctly set based on the constructor parameter
        if is_ai_game:
            self.players["AI"] = game_logic.PLAYER2
        self.turn = game_logic.PLAYER1
        self.winner = None
        self.draw = False
        self.state = "waiting"
        self.player_wins = 0
        self.ai_wins = 0
        self.num_wins = num_wins
        self.player_moves = 0
        self.ai_moves = 0
        print(f"GameSession initialized. AI game: {self.is_ai_game}, AI difficulty: {self.ai_difficulty}")





    def update_state(self, new_state):
        """Update the session's state."""
        self.state = new_state
    

    def make_move(self, column, player_id):
        """Attempt to make a move on the board and handle AI response if applicable."""
        player_token = self.players.get(player_id)
        # Check if it's the correct player's turn and if the move is valid
        if player_token == self.turn and 0 <= column < len(self.board[0]):
            move_made = game_logic.make_move(self.board, column, player_token)
            if move_made:
                # Increment the move count based on the player making the move
                if player_token == game_logic.PLAYER1:
                    self.player_moves += 1
                elif player_token == game_logic.PLAYER2 and self.is_ai_game:
                    self.ai_moves += 1

                # After making a move, check for win or draw
                if game_logic.check_win(self.board, player_token):
                    self.winner = player_id
                elif game_logic.is_draw(self.board):
                    self.draw = True
                else:
                    # Switch turns
                    self.switch_turns()
                
                # If it's now the AI's turn, make AI move
                if self.turn == game_logic.PLAYER2 and self.is_ai_game:
                    self.make_ai_move()
                return True
        return False

    def switch_turns(self):
        """Switch turns between PLAYER1 and PLAYER2."""
        self.turn = game_logic.PLAYER2 if self.turn == game_logic.PLAYER1 else game_logic.PLAYER1

    def make_ai_move(self):
        print("Entering make_ai_move method.")
        if self.is_ai_game and self.turn == game_logic.PLAYER2:
            ai_column = game_ai.ai_move(self.board, self.ai_difficulty)
            print(f"AI selected column {ai_column} for its move.")

            if ai_column is not None:
                made_move = game_logic.make_move(self.board, ai_column, game_logic.PLAYER2)
                print(f"Move made by AI in column {ai_column}: {'Success' if made_move else 'Failed'}")
                
                # After making a move, check for win or draw
                if game_logic.check_win(self.board, game_logic.PLAYER2):
                    self.winner = "AI"
                    print("AI wins the game.")
                elif game_logic.is_draw(self.board):
                    self.draw = True
                    print("Game is a draw.")
                else:
                    self.switch_turns()  # It's now the human player's turn

                return ai_column  # Return the column where AI made its move for server notification
            else:
                print("AI did not choose a valid column. This should be checked.")
        else:
            print("AI move not triggered due to game state or missing AI in players.")
        return None

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
        """Return the board state as a string for easy transmission over the network."""
        return '\n'.join(['|'.join(row) for row in self.board])
    
    def reset_board(self):
        self.board = game_logic.create_board()
        self.winner = None
        self.draw = False
        self.turn = game_logic.PLAYER1
        self.player_moves = 0
        self.ai_moves = 0

    def update_wins(self):
        if self.winner == "AI":
            self.ai_wins += 1
        elif self.winner != "DRAW":
            self.player_wins += 1

    def check_series_winner(self):
        if self.player_wins >= self.num_wins:
            return "PLAYER"
        elif self.ai_wins >= self.num_wins:
            return "AI"
        else:
            return None
    
    


   