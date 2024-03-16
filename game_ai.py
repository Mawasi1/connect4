import random
import game_logic  # Import your game logic to use constants like EMPTY, PLAYER1, etc.

def random_ai_move(board):
    import random
    # Find columns that are not full
    valid_columns = [col for col in range(len(board[0])) if board[0][col] == game_logic.EMPTY]
    # Pick a random column from the list of valid columns
    if valid_columns:
        return random.choice(valid_columns)
    else:
        return None

def find_winning_move(board, player_token):
    for col in range(len(board[0])):
        temp_board = [row[:] for row in board]  # Create a copy of the board
        for row in range(len(board) - 1, -1, -1):
            if temp_board[row][col] == game_logic.EMPTY:
                temp_board[row][col] = player_token
                if game_logic.check_win(temp_board, player_token):
                    return col
                break
    return None

def algorithmic_ai_move(board):
    # First, check if AI can win in the next move
    winning_move = find_winning_move(board, game_logic.PLAYER2)
    if winning_move is not None:
        return winning_move
    
    # Next, check to block the player's winning move
    player_win_move = find_winning_move(board, game_logic.PLAYER1)
    if player_win_move is not None:
        return player_win_move

    # As a fallback, make a random move
    return random_ai_move(board)


def ai_move(board, difficulty):
    if difficulty == "easy":
        return random_ai_move(board)
    elif difficulty == "hard":
        return algorithmic_ai_move(board)
    else:
        raise ValueError("Unknown difficulty level")
