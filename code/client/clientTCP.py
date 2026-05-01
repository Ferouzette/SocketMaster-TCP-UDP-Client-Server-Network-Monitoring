import socket
import time
import psutil
import uuid
import platform
import sys

# Constantes réseau 
IPV4 = socket.AF_INET
TCP  = socket.SOCK_STREAM

SERVER_IP   = "127.0.0.1"
PORT        = 5000
T           = 5   # intervalle entre deux REPORT (secondes)
CHECK_EVERY = 1   # durée de la mesure CPU psutil (secondes)

# Identité de l'agent 
# Option 1 : python client.py MonHostname   → hostname fixé par argument
# Option 2 : python client.py               → hostname = nom de la machine
if len(sys.argv) >= 2:
    HOSTNAME = sys.argv[1]
else:
    HOSTNAME = platform.node()

AGENT_ID = "Agent_" + str(uuid.uuid4())[:8]

print(f"[TCP CLIENT] Starting with ID: {AGENT_ID}  |  Hostname = {HOSTNAME}")


# ===================================
# Helpers réseau
# ===================================
def connect():
    """Créer et retourner une connexion TCP + fichier socket."""
    sock = socket.socket(IPV4, TCP)
    sock.connect((SERVER_IP, PORT))
    sock_file = sock.makefile("r")
    return sock, sock_file


def sendReceive(sock, sock_file, message):
    """Envoyer un message et retourner la réponse du serveur."""
    sock.send((message.strip() + "\n").encode())
    return sock_file.readline().strip()


def log_response(message, response):
    """Afficher le résultat d'un échange en console."""
    if response == "OK":
        print(f"[OK]  {message.strip()!r}")
    else:
        print(f"[WARNING] {message.strip()!r}  →  server replied: {response!r}")


# ===================================
# Main
# ===================================
def main():
    sock = sock_file = None

    try:
        # Connexion 
        try:
            sock, sock_file = connect()
            print(f"[TCP CLIENT] Connected to {SERVER_IP}:{PORT}")
        except ConnectionRefusedError:
            print(f"[ERROR] Could not connect to {SERVER_IP}:{PORT}. "
                  "Is the server running?")
            return

        # Enregistrement HELLO 
        resp = sendReceive(sock, sock_file, f"HELLO {AGENT_ID} {HOSTNAME}")
        log_response(f"HELLO {AGENT_ID} {HOSTNAME}", resp)

        if resp != "OK":
            print("[TCP CLIENT] Server rejected HELLO. Exiting.")
            return

        psutil.cpu_percent(interval=None)  # appel d'amorçage psutil

        # Boucle principale REPORT 
        while True:
            cpu       = psutil.cpu_percent(interval=CHECK_EVERY)
            ram       = psutil.virtual_memory().used / (1024 * 1024)
            timestamp = int(time.time())
            msg       = f"REPORT {AGENT_ID} {timestamp} {cpu:.5f} {ram:.2f}"

            resp = sendReceive(sock, sock_file, msg)

            if not resp:
                raise ConnectionError("Server disconnected (empty response).")

            log_response(msg, resp)

            if resp != "OK":
                print(f"[TCP CLIENT] Report rejected — retrying in {T}s...")

            time.sleep(max(0, T - CHECK_EVERY))

    # Déconnexion propre via Ctrl+C 
    except KeyboardInterrupt:
        print("\n[TCP CLIENT] Interrupted by user. Disconnecting properly...")
        if sock:
            try:
                resp = sendReceive(sock, sock_file, f"BYE {AGENT_ID}")
                log_response(f"BYE {AGENT_ID}", resp)
            except Exception:
                pass

    # Perte de connexion 
    except (ConnectionError, OSError, BrokenPipeError) as e:
        print(f"[ERROR] Connection lost: {e}")
        print("[TCP CLIENT] Server unreachable. Exiting.")

    finally:
        if sock:
            sock.close()
        print("[TCP CLIENT] Disconnected.")


if __name__ == "__main__":
    main()
