import selectors
import socket
import types
import sys
import game_logic
import game_session

sel = selectors.DefaultSelector()
active_sessions = {}

def log(message):
    """Utility function for standardized logging."""
    print(f"[LOG] {message}")

def start_game(addr, game_type, ai_difficulty, data):
    log(f"Starting game for {addr}, game_type: {game_type}, AI difficulty: {ai_difficulty}")
    if game_type == "2":
        new_session = game_session.GameSession(player1=addr, ai_difficulty=ai_difficulty)
        active_sessions[new_session.session_id] = new_session
        data.session_id = new_session.session_id
        log(f"New AI game session created with ID {new_session.session_id} for player {addr}")
        response_message = "New AI game session created. Your turn or AI's turn depending on the game logic."
    else:
        assign_player_to_session(addr, data)
        response_message = "New player session created. Waiting for another player."
    if data and hasattr(data, 'outb'):
        data.outb += response_message.encode('utf-8')

def accept_wrapper(sock):
    conn, addr = sock.accept()
    log(f"Accepted connection from {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)
    assign_player_to_session(addr, data)

def assign_player_to_session(addr, data):
    # Existing logic with a correction for immediate session readiness check
    print(f"[LOG] Attempting to assign player {addr} to session...")
    found_session = False

    for session_id, session in active_sessions.items():
        if session.state == "waiting" and len(session.players) < 2:
            session.players[addr] = game_logic.PLAYER2
            data.session_id = session_id
            found_session = True
            # Check if the session is now full and update state accordingly
            if len(session.players) == 2:
                session.update_state("ready")
                notify_players_session_ready(session_id)
            break

    if not found_session:
        create_new_session(addr, data)

def create_new_session(addr, data):
    new_session = game_session.GameSession(player1=addr)
    active_sessions[new_session.session_id] = new_session
    data.session_id = new_session.session_id
    print(f"[LOG] New session created with ID {new_session.session_id} for player {addr}. Waiting for another player.")


def notify_players_session_ready(session_id):
    session = active_sessions[session_id]
    message = "Both players connected. The game starts now."
    for player_addr, _ in session.players.items():
        client = find_client_by_addr(player_addr)
        if client:
            client.data.outb += message.encode('utf-8')
    print(f"[LOG] Notification sent for session {session_id}.")

def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)
        if recv_data:
            data.inb += recv_data
            process_command(data.inb.decode("utf-8"), data, sock)
            data.inb = b""
        else:
            log(f"Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE and data.outb:
        log(f"Sending to {data.addr}: {data.outb.decode('utf-8')}")
        sent = sock.send(data.outb)
        data.outb = data.outb[sent:]

def process_command(command, data, sock):
    args = command.strip().split()
    log(f"Processing command from {data.addr}: {command}")

    current_session = active_sessions.get(data.session_id, None)

    if args[0].upper() == "START_GAME":
        game_type = args[1].upper()
        ai_difficulty = args[2] if len(args) > 2 else None

        if current_session:
            # If the session is ready or already started, ignore the START_GAME command
            if current_session.state == "ready" or data.addr in current_session.players:
                log(f"Player {data.addr} already in an active or ready session ({data.session_id}). Ignoring START_GAME command.")
                data.outb += "Game already started or session is ready. Please wait.".encode()
                return

        # Start a new game or join an existing one
        start_game(data.addr, game_type, ai_difficulty, data)

    elif args[0].upper() == "MOVE" and len(args) == 2:
        if not current_session:
            log(f"No active session found for {data.addr}. Ignoring MOVE command.")
            data.outb += "No active game. Start a new game first.".encode()
            return

        column = int(args[1])
        if current_session.make_move(column, data.addr):
            update_game_state(current_session, data.session_id)
        else:
            data.outb += "Invalid move. Try again.".encode()
    else:
        data.outb += "Unknown command.".encode()



def find_client_by_addr(addr):
    for key in sel.get_map().values():
        if hasattr(key.data, 'addr') and key.data.addr == addr:
            return key
    return None

# Server initialization code remains unchanged

def update_game_state(session, session_id):
    log(f"Updating game state for session {session_id}.")
    game_status = session.get_game_status()
    
    message = ""
    
    if session.is_ai_game and session.turn == game_logic.PLAYER2:
        ai_column = session.make_ai_move()
        if ai_column is not None:
            log(f"AI made a move in column {ai_column}.")
            message += f"AI moved to column {ai_column}.\n"
            # After AI move, check game status again
            game_status = session.get_game_status()
        else:
            log("AI failed to make a move or no valid moves available.")
            message += "AI failed to make a move. Please check the game logic.\n"
    
    board_state = session.serialize_board()
    message += f"Board State:\n{board_state}\n"
    message += f"Game Status: {game_status}\n"

    for addr in session.players.keys():
        if addr != "AI":  # Send update only to real players
            client = find_client_by_addr(addr)
            if client:
                client.data.outb += message.encode("utf-8")
                log(f"Updated game state sent to {addr}.")












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
