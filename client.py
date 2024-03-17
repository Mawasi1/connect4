import socket
import selectors
import types
import sys
import threading
import time


sel = selectors.DefaultSelector()


def get_player_choice():
    print("Welcome to Connect 4!")
    print("Do you want to play against (1) another player or (2) the AI?")
    game_type = input("Enter 1 for another player, 2 for AI: ").strip()

    ai_difficulty = None
    num_wins = None

    if game_type == "2":
        print("Select AI difficulty level:")
        print("1: Easy")
        print("2: Hard")
        difficulty_choice = input("Enter difficulty level (1-2): ").strip()
        ai_difficulty = "easy" if difficulty_choice == "1" else "hard"

        invalid_count = 0
        suspension_duration = 60  # Initial suspension duration in seconds

        while True:
            num_wins = input("Enter the number of wins to play in the series (must be greater than 0): ").strip()

            if num_wins.isdigit() and int(num_wins) > 0:
                num_wins = int(num_wins)
                break
            else:
                invalid_count += 1
                print("Invalid input. Please enter a valid number greater than 0.")

                if invalid_count >= 5:
                    print(f"You have entered an invalid number {invalid_count} consecutive times.")
                    print(f"Your activity will be suspended for {suspension_duration} seconds.")
                    time.sleep(suspension_duration)
                    suspension_duration *= 2  # Double the suspension duration for the next occurrence
                    invalid_count = 0  # Reset the invalid count after the suspension

    return game_type, ai_difficulty, num_wins
    

def create_request(action, value="", extra="", num_wins=""):
    if action == "start_game":
        return f"START_GAME {value} {extra} {num_wins}".encode('utf-8')
    elif action == "move":
        return f"MOVE {value}".encode('utf-8')
    return None

def start_connection(host, port, game_type, ai_difficulty, num_wins):
    server_addr = (host, port)
    print(f"Starting connection to {server_addr}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(False)
    result = sock.connect_ex(server_addr)
    print(f"Connect_ex result: {result}")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    data = types.SimpleNamespace(
        connid=1,
        msg_total=0,
        recv_total=0,
        messages=[create_request("start_game", game_type, ai_difficulty, num_wins)],
        outb=b"",
    )
    print(f"Message queued to be sent: {data.messages[0]}")
    sel.register(sock, events, data=data)
    return data

def handle_server_response(response, data):
    print(f"Received response from server: {response}")

    # Split the response by lines for easier parsing
    response_lines = response.split('\n')

    # Initialize a flag to track if the board state is being processed
    processing_board_state = False
    board_state_lines = []

    for line in response_lines:
        # Handle the start of the board state section
        if "Board State:" in line:
            processing_board_state = True
            board_state_lines = []  # Reset the list to start collecting board state lines
            continue  # Move to the next line

        # If processing the board state, collect lines until the section ends
        if processing_board_state:
            if line.strip():  # If the line is not empty, add it to the board state lines
                board_state_lines.append(line)
            else:  # An empty line signifies the end of the board state section
                processing_board_state = False  # Stop processing board state
                # Print the collected board state
                print("Current board state:")
                for board_line in board_state_lines:
                    print(board_line)
                continue  # Move to the next line after processing the board state

        # Handle AI move messages
        if "AI moved to column" in line:
            ai_move_msg = line.split("AI moved to column ")[1].split(".")[0]
            print(f"AI made a move in column {ai_move_msg}.")

        # Handle game status updates
        if "Game Status:" in line:
            status_msg = line.split("Game Status: ")[1]
            print(f"Game status: {status_msg}")
            if "WIN" in status_msg or "DRAW" in status_msg:
                print(f"Game over: {status_msg}")
                # The game has ended, but the series may continue
                # Continue reading the response to check for win counts and series winner

        # Handle win count updates
        if "Player wins:" in line:
            win_counts = line.split("Player wins:")[1].strip()
            print(f"Current win counts: {win_counts}")

        # Handle move count updates
        if "Player moves:" in line:
            move_counts = line.split("Player moves:")[1].strip()
            print(f"Move counts for the last match: {move_counts}")

        # Handle series winner announcement
        if "Series winner:" in line:
            series_winner = line.split("Series winner:")[1].strip()
            print(f"Series winner: {series_winner}")
            # The series has ended, so we can exit the game or perform necessary cleanup
            sys.exit(0)

        # Handle invalid move responses
        if "Invalid move" in line:
            print("Invalid move. Try again.")


def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        try:
            recv_data = sock.recv(1024)
            if recv_data:
                response = recv_data.decode('utf-8')
                print(f"Received: {response}")
                handle_server_response(response, data)
            else:
                print("Connection closed by server, exiting.")
                sel.unregister(sock)
                sock.close()
                sys.exit(0)
        except ConnectionResetError:
            print("Server capacity reached. Please try again later.")
            sel.unregister(sock)
            sock.close()
            sys.exit(0)
    if mask & selectors.EVENT_WRITE and data.messages:
        data.outb = data.messages.pop(0)
        print(f"Sending: {data.outb.decode('utf-8')}")
        sock.send(data.outb)

def user_input_thread(data):
    while True:
        user_input = input("Enter your move (column number) or 'q' to quit: ")
        if user_input.lower() == 'q':
            print("Exiting the game.")
            sel.close()  # Close the selector to trigger closing the main event loop
            sys.exit(0)  # Exit the client application
        elif user_input.isdigit():
            action = create_request("move", user_input) 
            data.messages.append(action)
            print(f"Move queued to be sent: {action.decode('utf-8')}")
        else:
            print("Invalid input. Please enter a valid column number or 'q' to quit.")

def main(host, port, game_type, ai_difficulty, num_wins):
    data = start_connection(host, port, game_type, ai_difficulty, num_wins)
    input_thread = threading.Thread(target=user_input_thread, args=(data,), daemon=True)
    input_thread.start()

    try:
        while True:
            events = sel.select(timeout=None)
            if events:
                for key, mask in events:
                    service_connection(key, mask)
            else:
                break  # Break the loop if the selector is closed
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")
    finally:
        sel.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage:", sys.argv[0], "<host> <port>")
        sys.exit(1)

    game_type, ai_difficulty, num_wins = get_player_choice()
    host, port = sys.argv[1], int(sys.argv[2])
    main(host, port, game_type, ai_difficulty, num_wins)
