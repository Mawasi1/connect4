# Student's name: Aladin Nour Mawasi
# Student's ID: 316172410


ROWS, COLUMNS = 6, 7
EMPTY, PLAYER1, PLAYER2 = " ", "X", "O"

# Initialize the game board
def create_board():
    return [[EMPTY for _ in range(COLUMNS)] for _ in range(ROWS)]

# Print the game board (simple CLI interface)
def print_board(board):
    for row in board:
        print('|' + '|'.join(row) + '|')

# Make a move on the board
def make_move(board, column, player_token):
    for row in reversed(board):
        if row[column] == EMPTY:
            row[column] = player_token
            return True  # Move was successful
    return False  # Column is full, move was not made

# Check if the current player has won
def check_win(board, player_token):
    # Check horizontal
    for row in range(ROWS):
        for col in range(COLUMNS - 3):
            if board[row][col] == player_token and board[row][col + 1] == player_token \
               and board[row][col + 2] == player_token and board[row][col + 3] == player_token:
                return True

    # Check vertical
    for col in range(COLUMNS):
        for row in range(ROWS - 3):
            if board[row][col] == player_token and board[row + 1][col] == player_token \
               and board[row + 2][col] == player_token and board[row + 3][col] == player_token:
                return True

    # Check diagonals with positive slope
    for col in range(COLUMNS - 3):
        for row in range(3, ROWS):
            if board[row][col] == player_token and board[row - 1][col + 1] == player_token \
               and board[row - 2][col + 2] == player_token and board[row - 3][col + 3] == player_token:
                return True

    # Check diagonals with negative slope
    for col in range(COLUMNS - 3):
        for row in range(ROWS - 3):
            if board[row][col] == player_token and board[row + 1][col + 1] == player_token \
               and board[row + 2][col + 2] == player_token and board[row + 3][col + 3] == player_token:
                return True

    return False

def is_draw(board):
    # Check if any cell in the board is still empty, indicating the game is not a draw
    for row in board:
        if EMPTY in row:
            return False
    # If the board is full and no win condition is met, it's a draw
    return True

