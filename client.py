import socket
import selectors
import types
import sys
import threading

sel = selectors.DefaultSelector()

def get_player_choice():
    print("Welcome to Connect 4!")
    print("Do you want to play against (1) another player or (2) the AI?")
    game_type = input("Enter 1 for another player, 2 for AI: ").strip()

    ai_difficulty = None
    if game_type == "2":
        print("Select AI difficulty level:")
        print("1: Easy")
        print("2: Hard")
        difficulty_choice = input("Enter difficulty level (1-2): ").strip()
        ai_difficulty = "easy" if difficulty_choice == "1" else "hard"
    
    return game_type, ai_difficulty

def create_request(action, value="", extra=""):
    """Prepare a request to send to the server based on an action, optional value, and extra info."""
    if action == "start_game":
        return f"START_GAME {value} {extra}".encode('utf-8')
    elif action == "move":
        return f"MOVE {value}".encode('utf-8')
    return None

def start_connection(host, port, game_type, ai_difficulty):
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
        messages=[create_request("start_game", game_type, ai_difficulty)],
        outb=b"",
    )
    print(f"Message queued to be sent: {data.messages[0]}")
    sel.register(sock, events, data=data)
    return data  # Return the data object for use in the user_input_thread

def handle_server_response(response, data):
    print(f"Received response from server: {response}")

    # Handling AI move messages
    if "AI moved to column" in response:
        # This assumes the message is correctly formed as "AI moved to column X. "
        ai_move_msg = response.split("AI moved to column ")[1].split(".")[0]
        print(f"AI made a move in column {ai_move_msg}.")

    # Handle game status updates
    if "Game Status: ONGOING" in response:
        print("Game is ongoing. Your turn.")
    elif "Game Status: WIN" in response or "Game Status: DRAW" in response:
        # Extract and display the complete status message
        status_msg = response.split("Game Status: ")[1].split("\n")[0]
        print(f"Game over: {status_msg}")
        sys.exit(0)  # Exit the client if the game is over
    elif "Invalid move" in response:
        print("Invalid move. Try again.")
    
    if "Board State:" in response:
        board_state = response.split("Board State:\n")[1].split("\n\n")[0]
        print("Current board state:")
        print(board_state)


def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)
        if recv_data:
            response = recv_data.decode('utf-8')
            print(f"Received: {response}")
            handle_server_response(response, data)
        else:
            print("Connection closed by server, exiting.")
            sel.unregister(sock)
            sock.close()
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

def main(host, port, game_type, ai_difficulty):
    data = start_connection(host, port, game_type, ai_difficulty)
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

    game_type, ai_difficulty = get_player_choice()
    host, port = sys.argv[1], int(sys.argv[2])
    main(host, port, game_type, ai_difficulty)
