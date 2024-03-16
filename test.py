import game_logic

def test_game():
    board = game_logic.create_board()
    game_logic.print_board(board)  # Assuming you have a function to print the board state

    # Simulate a game where players take turns making moves
    moves = [(0, 'X'), (4, 'O'), (1, 'X'), (5, 'O'), (2, 'X'), (4, 'O'), (3, 'X')]
    for column, player in moves:
        if game_logic.make_move(board, column, player):
            print(f"Player {player} makes a move in column {column}")
            game_logic.print_board(board)
            if game_logic.check_win(board, player):
                print(f"Player {player} wins!")
                break
    else:  # This part is executed if the loop completes without a break statement
        if is_draw(board):
            print("It's a draw!")
        else:
            print("Game is not finished yet.")

def is_draw(board):
    # Check if the board is full (a simple way to check for a draw)
    return all(cell != game_logic.EMPTY for row in board for cell in row)

if __name__ == "__main__":
    test_game()
