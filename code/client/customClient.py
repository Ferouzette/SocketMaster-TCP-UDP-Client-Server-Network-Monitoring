import socket
import time
import psutil
import uuid

# Constantes réseau 
IPV4 = socket.AF_INET
TCP  = socket.SOCK_STREAM

SERVER_IP   = "127.0.0.1"
PORT        = 5000
T           = 5   # intervalle entre deux envois (secondes)
CHECK_EVERY = 1   # durée mesure CPU (secondes)
MAX_TRIES   = 5   # nombre max de rejets consécutifs avant abandon

# Saisie interactive 
HOSTNAME      = input("Enter your HOSTNAME: ").strip() or "CustomHost"
CustomMessage = input("Enter your custom message: ").strip()
AGENT_ID      = "Agent_" + str(uuid.uuid4())[:8]

print(f"[CLIENT] Starting with ID: {AGENT_ID}  |  Hostname = {HOSTNAME}")


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
    tries    = 0
    sock = sock_file = None

    try:
        # Connexion 
        try:
            sock, sock_file = connect()
            print(f"[CLIENT] Connected to {SERVER_IP}:{PORT}")
        except ConnectionRefusedError:
            print(f"[ERROR] Could not connect to {SERVER_IP}:{PORT}. "
                  "Is the server running?")
            return

        # Enregistrement HELLO 
        resp = sendReceive(sock, sock_file, f"HELLO {AGENT_ID} {HOSTNAME}")
        log_response(f"HELLO {AGENT_ID} {HOSTNAME}", resp)

        if resp != "OK":
            print("[CLIENT] Server rejected HELLO. Exiting.")
            return

        psutil.cpu_percent(interval=None)  # appel d'amorçage psutil

        # Boucle principale : envoi du message personnalisé en boucle 
        while True:
            resp = sendReceive(sock, sock_file, CustomMessage)

            if not resp:
                raise ConnectionError("Server disconnected (empty response).")

            log_response(CustomMessage, resp)

            if resp != "OK":
                tries += 1
                print(f"[CLIENT] Rejected ({tries}/{MAX_TRIES}) — retrying in {T}s...")
                if tries >= MAX_TRIES:
                    raise ConnectionError(
                        f"Server rejected message {MAX_TRIES} times in a row. Aborting."
                    )
            else:
                tries = 0  # réinitialiser le compteur après un succès

            time.sleep(max(0, T - CHECK_EVERY))

    # Déconnexion propre via Ctrl+C 
    except KeyboardInterrupt:
        print("\n[CLIENT] Interrupted by user. Disconnecting properly...")
        if sock:
            try:
                resp = sendReceive(sock, sock_file, f"BYE {AGENT_ID}")
                log_response(f"BYE {AGENT_ID}", resp)
            except Exception:
                pass

    # Perte de connexion ou trop de rejets 
    except (ConnectionError, OSError, BrokenPipeError) as e:
        print(f"[ERROR] {e}")
        print("[CLIENT] Exiting.")

    finally:
        if sock:
            sock.close()
        print("[CLIENT] Disconnected.")


if __name__ == "__main__":
    main()

