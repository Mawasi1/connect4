import selectors
import socket
import types
import sys
import game_logic
import game_session

sel = selectors.DefaultSelector()
# Dictionary to hold active game sessions, keyed by session ID
active_sessions = {}

def start_game(addr, game_type, ai_difficulty, data):
    response_message = ""
    if game_type == "2":
        new_session = game_session.GameSession(player1=addr, ai_difficulty=ai_difficulty)
        active_sessions[new_session.session_id] = new_session
        data.session_id = new_session.session_id
        print(f"New AI game session created with ID {new_session.session_id} for player {addr}")
        response_message = f"New AI game session created. Your turn or AI's turn depending on the game logic."
    else:
        # Follow your existing logic to pair players or create a new session
        assign_player_to_session(addr, data)
        response_message = "New player session created. Waiting for another player."

    # Send response back to the client
    if data and hasattr(data, 'outb'):
        data.outb += response_message.encode('utf-8')

def accept_wrapper(sock):
    conn, addr = sock.accept()  # Accept the connection
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)
    # Assign player to a new or existing session
    assign_player_to_session(addr, data)

def assign_player_to_session(addr, data):
    # Attempt to find an existing session awaiting a second player
    for session_id, session in active_sessions.items():
        if len(session.players) == 1 and "AI" not in session.players:
            session.players[addr] = game_logic.PLAYER2
            data.session_id = session_id
            print(f"Player {addr} added to existing session {session_id}")
            # Inform both players that the game can start
            notify_players_session_ready(session_id)
            return
    # No suitable session found, create a new one
    create_new_session(addr, data)

def create_new_session(addr, data):
    new_session = game_session.GameSession(player1=addr)
    active_sessions[new_session.session_id] = new_session
    data.session_id = new_session.session_id
    print(f"New session created with ID {new_session.session_id} for player {addr}")

def notify_players_session_ready(session_id):
    session = active_sessions[session_id]
    message = "Both players connected. The game starts now."
    for player_addr in session.players.keys():
        client = find_client_by_addr(player_addr)
        if client:
            client.data.outb += message.encode('utf-8')


def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        if recv_data:
            data.inb += recv_data
            process_command(data.inb.decode("utf-8"), data, sock)
            data.inb = b""  # Clear input buffer after processing
        else:
            print(f"Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE and data.outb:
        print(f"Sending to {data.addr}: {data.outb.decode('utf-8')}")  # Log what's being sent
        sent = sock.send(data.outb)  # Should be ready to write
        data.outb = data.outb[sent:]

def process_command(command, data, sock):
    args = command.strip().split()
    if args[0].upper() == "START_GAME":
        game_type = args[1].upper()  # PLAYER or AI
        ai_difficulty = args[2] if len(args) > 2 else None  # easy or hard
        start_game(data.addr, game_type, ai_difficulty, data)
    elif args[0].upper() == "MOVE" and len(args) == 2:
        try:
            column = int(args[1])
            session = active_sessions.get(data.session_id, None)
            if session and session.make_move(column, data.addr):
                update_game_state(session, data.session_id)
            else:
                data.outb += b"Invalid move. Try again.\n"
        except ValueError:
            data.outb += b"Invalid command.\n"
    else:
        data.outb += b"Unknown command.\n"

def update_game_state(session, session_id):
    # Initial status check to determine game state before any AI action
    pre_ai_status = session.get_game_status()

    # Initialize an empty message string to accumulate message parts
    message = ""

    # If the game is ongoing and it's the AI's turn to move
    if pre_ai_status == "ONGOING" and session.turn == game_logic.PLAYER2:
        # Attempt the AI move
        ai_column = session.make_ai_move()

        # If a valid AI move was made (ai_column is not None)
        if ai_column is not None:
            print("OOGA BOOGA", flush=True)
            print(f"AI moved to column {ai_column}")  # Confirm AI move determination
            message += f"AI moved to column {ai_column}. "  # Construct message
            print(f"Complete message to be sent: {message}")  # Confirm message content
            print("whatever!!")

        else:
            # If the AI was expected to move but didn't, log an error
            print("AI was supposed to move but didn't.")
            message += "AI failed to make a move. Please check the game logic.\n"
            
    board_state = session.serialize_board()
    message += f"Board State:\n{board_state}\n"

    # After handling the AI move, update the game status to reflect any changes
    post_ai_status = session.get_game_status()
    message += f"Game Status: {post_ai_status}\n"

    # Send the compiled message to all clients connected to this game session
    for addr in session.players.keys():
        # Find each client using their address
        client = find_client_by_addr(addr)
        if client:
            # If client is found, append the compiled message to their outb buffer for sending
            client.data.outb += message.encode("utf-8")
            # Log the outgoing message for server-side clarity
            print(f"Sending to {addr}: {message}")


def find_client_by_addr(addr):
    """Helper function to find the client object by address."""
    # Your existing logic to return the client based on address





def find_client_by_addr(addr):
    """Helper function to find the client object by address."""
    for key in sel.get_map().values():
        if hasattr(key.data, 'addr') and key.data.addr == addr:
            return key
    return None


def find_client_by_addr(addr):
    """Helper function to find the client object by address."""
    for key in sel.get_map().values():
        if hasattr(key.data, 'addr') and key.data.addr == addr:
            return key
    return None

if len(sys.argv) != 3:
    print("Usage:", sys.argv[0], "<host> <port>")
    sys.exit(1)

host, port = sys.argv[1], int(sys.argv[2])
lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.bind((host, port))
lsock.listen()
print(f"Listening on {host}:{port}")
lsock.setblocking(False)
sel.register(lsock, selectors.EVENT_READ, data=None)

try:
    while True:
        events = sel.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                accept_wrapper(key.fileobj)
            else:
                service_connection(key, mask)
except KeyboardInterrupt:
    print("Caught keyboard interrupt, exiting")
finally:
    sel.close()
