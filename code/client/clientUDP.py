import socket
import time
import psutil
import uuid
import platform
import sys

# Constantes réseau 
IPV4 = socket.AF_INET
UDP  = socket.SOCK_DGRAM

SERVER_IP   = "127.0.0.1"
PORT        = 5001
T           = 5    # intervalle entre deux REPORT (secondes)
CHECK_EVERY = 1    # durée de la mesure CPU psutil (secondes)
TIMEOUT     = 3    # timeout socket UDP (secondes)
MAX_RETRIES = 5    # tentatives max pour le HELLO initial

# Identité de l'agent 
# Option 1 : python clientUDP.py MonHostname   → hostname fixé par argument
# Option 2 : python clientUDP.py               → hostname = nom de la machine
if len(sys.argv) >= 2:
    HOSTNAME = sys.argv[1]
else:
    HOSTNAME = platform.node()

AGENT_ID = "Agent_" + str(uuid.uuid4())[:8]

print(f"[UDP CLIENT] Starting with ID: {AGENT_ID}  |  Hostname = {HOSTNAME}")


# ===================================
# Helpers réseau
# ===================================
def sendReceive(sock, message):
    """Envoyer un datagramme et attendre la réponse (None si timeout ou perte)."""
    sock.sendto(message.encode(), (SERVER_IP, PORT))
    try:
        response, _ = sock.recvfrom(1024)
        return response.decode().strip()
    except (socket.timeout, ConnectionResetError, OSError):
        # socket.timeout        : pas de réponse dans le délai imparti
        # ConnectionResetError  : WinError 10054 — serveur arrêté sous Windows
        # OSError               : toute autre erreur réseau bas niveau
        return None


def log_response(message, response):
    """Afficher le résultat d'un échange en console."""
    if response == "OK":
        print(f"[OK]  {message!r}")
    elif response is None:
        print(f"[WARNING] {message!r}  →  no response (packet lost?)")
    else:
        print(f"[WARNING] {message!r}  →  server replied: {response!r}")


# ===================================
# Main
# ===================================
def main():
    sock = socket.socket(IPV4, UDP)
    sock.settimeout(TIMEOUT)

    # Enregistrement HELLO avec retry 
    hello_msg = f"HELLO {AGENT_ID} {HOSTNAME}"
    for attempt in range(1, MAX_RETRIES + 1):
        resp = sendReceive(sock, hello_msg)
        if resp:
            log_response(hello_msg, resp)
            if resp != "OK":
                print("[UDP CLIENT] Server rejected HELLO. Exiting.")
                sock.close()
                sys.exit(1)
            break
        print(f"[WARNING] No response to HELLO, retrying ({attempt}/{MAX_RETRIES})...")
        time.sleep(2)
    else:
        print("[ERROR] Server unreachable after several attempts. Exiting.")
        sock.close()
        sys.exit(1)

    psutil.cpu_percent(interval=None)  # appel d'amorçage psutil

    # Boucle principale REPORT 
    try:
        while True:
            start     = time.time()
            cpu       = psutil.cpu_percent(interval=CHECK_EVERY)
            ram       = psutil.virtual_memory().used / (1024 * 1024)
            timestamp = int(time.time())
            msg       = f"REPORT {AGENT_ID} {timestamp} {cpu:.5f} {ram:.2f}"

            resp = sendReceive(sock, msg)
            log_response(msg, resp)

            elapsed = time.time() - start
            time.sleep(max(0, T - elapsed))

    # Déconnexion propre via Ctrl+C 
    except KeyboardInterrupt:
        print("\n[UDP CLIENT] Interrupted by user. Disconnecting properly...")
        try:
            # UDP : on envoie BYE mais on n'attend pas forcément de réponse
            sock.sendto(f"BYE {AGENT_ID}".encode(), (SERVER_IP, PORT))
            resp = sendReceive(sock, f"BYE {AGENT_ID}")
            log_response(f"BYE {AGENT_ID}", resp)
        except Exception:
            pass

    finally:
        sock.close()
        print("[UDP CLIENT] Disconnected.")


if __name__ == "__main__":
    main()