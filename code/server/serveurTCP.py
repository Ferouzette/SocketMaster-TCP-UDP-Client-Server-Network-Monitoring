import socket
import threading
import time
import datetime
import csv
import tkinter as tk

# Constantes réseau 
IPV4 = socket.AF_INET
TCP  = socket.SOCK_STREAM

HOST = "0.0.0.0"
PORT = 5000
T    = 5

# Limites anti-flood 
MAX_AGE      = 3 * T   # secondes sans REPORT avant de considérer un agent inactif
MAX_AGENTS   = 30      # nombre maximum d'agents simultanés
RATE_LIMIT_S = 2       # délai minimum entre deux REPORT d'un même agent

# État global 
agents           = {}
lock             = threading.Lock()
inactive_alerted = set()
rate_limit_count = {}   # compteur de requêtes bloquées par agent

# Nom du fichier CSV avec horodatage 
_ts = time.strftime("_%b-%d-%Y_%H%M", time.localtime())
CSV_FILE = "stats" + _ts + ".csv"


# ===================================
# Export CSV
# ===================================
def export_csv(active_agents):
    """Ajouter un snapshot des agents actifs dans le fichier CSV horodaté."""
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        for agent_id, data in active_agents.items():
            writer.writerow([
                datetime.datetime.now(),
                agent_id,
                data["hostname"],
                data["cpu"],
                data["ram"],
            ])


# ======================================================
# Thread : statistiques périodiques + mise à jour GUI
# ======================================================
def handle_stats(live_text, history_text):
    """
    - live_text    : panneau supérieur — snapshot courant (écrasé à chaque cycle)
    - history_text : panneau inférieur — historique cumulé (append uniquement)
    """
    while True:
        time.sleep(T)
        now = time.time()

        with lock:
            # Détection et suppression des agents inactifs 
            to_remove = []
            for agent_id, info in agents.items():

                # Coupure brutale : attendre MAX_AGE (3*T) depuis disconnected_at
                if info.get("disconnected"):
                    elapsed = now - info.get("disconnected_at", now)
                    if elapsed >= MAX_AGE:
                        if agent_id not in inactive_alerted:
                            print(f"\n[ALERT] Agent '{agent_id}' DISCONNECTED unexpectedly "
                                  f"(silent for {elapsed:.0f}s)")
                            inactive_alerted.add(agent_id)
                        to_remove.append(agent_id)

                # Toujours connecté mais silencieux depuis trop longtemps
                else:
                    elapsed = now - info["last_seen"]
                    if elapsed > MAX_AGE:
                        if agent_id not in inactive_alerted:
                            print(f"\n[ALERT] Agent '{agent_id}' is INACTIVE! "
                                  f"(silent for {elapsed:.0f}s)")
                            inactive_alerted.add(agent_id)
                        to_remove.append(agent_id)

            for agent_id in to_remove:
                agents.pop(agent_id, None)
                print(f"[INFO] Agent '{agent_id}' removed from stats.")

            # Résumé rate-limit (affiché toutes les T secondes) 
            if rate_limit_count:
                print("\n[RATE LIMIT] Blocked request summary:")
                for aid, count in rate_limit_count.items():
                    print(f"  - {aid}: {count} blocked request(s)")
                rate_limit_count.clear()

            active = {
                k: v for k, v in agents.items()
                if v.get("verified")
                and not v.get("disconnected")
                and (time.time() - v["last_seen"]) <= MAX_AGE
            }

        # Contenu des deux panneaux 
        ts = datetime.datetime.now().strftime("%H:%M:%S")

        if not active:
            print("No agents are active as of now...")
            live_content  = (
                f"  Last update   : {ts}\n"
                f"  Active agents : 0\n"
                f"  Avg CPU       : —\n"
                f"  Avg RAM       : —\n"
            )
            history_entry = f"[{ts}]  No agents are active as of now...\n" + "─" * 70 + "\n"
        else:
            avg_cpu = sum(a["cpu"] for a in active.values()) / len(active)
            avg_ram = sum(a["ram"] for a in active.values()) / len(active)

            # Panneau live : résumé global + détail par agent (toujours à jour)
            live_content = (
                f"  Last update   : {ts}\n"
                f"  Active agents : {len(active)}\n"
                f"  Avg CPU       : {avg_cpu:.2f}%\n"
                f"  Avg RAM       : {avg_ram:.2f} MB\n"
            )
            for uid, data in active.items():
                live_content += (
                    f"  {uid} ({data['hostname']})"
                    f"    CPU : {data['cpu']:.2f}%  |  RAM : {data['ram']:.2f} MB\n"
                )

            # Panneau historique : entrée compacte horodatée
            history_entry = (
                f"[{ts}]  Agents: {len(active)}  |  "
                f"Avg CPU: {avg_cpu:.2f}%  |  Avg RAM: {avg_ram:.2f} MB\n"
            )
            for uid, data in active.items():
                history_entry += (
                    f"  {uid} ({data['hostname']})  "
                    f"CPU: {data['cpu']:.2f}%  RAM: {data['ram']:.2f} MB\n"
                )
            history_entry += "─" * 70 + "\n"

        # Panneau LIVE : remplacement complet à chaque cycle 
        def update_live(c=live_content):
            live_text.config(state="normal")
            live_text.delete("1.0", "end")
            live_text.insert("end", c)
            live_text.config(state="disabled")

        # Panneau HISTORIQUE : append uniquement 
        def append_history(e=history_entry):
            history_text.config(state="normal")
            history_text.insert("end", e)
            history_text.see("end")   # auto-scroll vers le bas
            history_text.config(state="disabled")

        live_text.after(0, update_live)
        history_text.after(0, append_history)

        export_csv(active)


# ===================================
# Thread : gestion d'un client
# ===================================
def handle_client(conn, addr):
    """Gérer une connexion client dans un thread dédié."""
    print(f"[+] Connection from {addr}")
    conn_file = conn.makefile("r")
    current_agent_id = None

    try:
        while True:
            raw = conn_file.readline()
            if not raw:
                break
            data = raw.strip()
            if not data:
                continue

            parts = data.split()
            flag  = parts[0]

            # HELLO 
            if flag == "HELLO" and len(parts) >= 3:
                agent_id = parts[1]
                hostname = " ".join(parts[2:])

                with lock:
                    if current_agent_id is not None:
                        print(f"[BLOCK] '{addr}' tried a second HELLO (already '{current_agent_id}').")
                        conn.send(b"ERROR AlreadyRegistered\n")
                        continue

                    if agent_id in agents:
                        print(f"[BLOCK] '{agent_id}' already registered by another connection. "
                              f"'{addr}' refused.")
                        conn.send(b"ERROR AgentIDTaken\n")
                        continue

                    if len(agents) >= MAX_AGENTS:
                        print(f"[BLOCK] Agent limit ({MAX_AGENTS}) reached. "
                              f"'{agent_id}' refused.")
                        conn.send(b"ERROR Max agents reached\n")
                        continue

                    current_agent_id = agent_id
                    agents[current_agent_id] = {
                        "hostname"        : hostname,
                        "cpu"             : 0.0,
                        "ram"             : 0.0,
                        "last_seen"       : time.time(),
                        "last_report"     : 0.0,
                        "verified"        : False,
                        "disconnected"    : False,
                        "disconnected_at" : None,
                    }
                    inactive_alerted.discard(current_agent_id)

                print(f"[HELLO] Agent '{current_agent_id}' ({hostname}) registered.")
                conn.send(b"OK\n")

            # REPORT 
            elif flag == "REPORT" and len(parts) == 5:
                try:
                    agent_id = parts[1]
                    cpu      = float(parts[3])
                    ram      = float(parts[4])

                    if not (0 <= cpu <= 100) or ram < 0:
                        raise ValueError("CPU/RAM out of range")

                    with lock:
                        if agent_id not in agents:
                            print(f"[WARNING] REPORT from unregistered agent '{agent_id}', ignored.")
                            conn.send(b"ERROR Unknown agent\n")
                            continue

                        if agent_id != current_agent_id:
                            print(f"[SECURITY] '{addr}' tried to REPORT for '{agent_id}' "
                                  f"but owns '{current_agent_id}'. Rejected.")
                            conn.send(b"ERROR Unauthorized\n")
                            continue

                        now = time.time()
                        if now - agents[agent_id]["last_report"] < RATE_LIMIT_S:
                            rate_limit_count[agent_id] = \
                                rate_limit_count.get(agent_id, 0) + 1
                            conn.send(b"ERROR Rate limit\n")
                            continue

                        agents[agent_id]["cpu"]             = cpu
                        agents[agent_id]["ram"]             = ram
                        agents[agent_id]["last_seen"]       = now
                        agents[agent_id]["last_report"]     = now
                        agents[agent_id]["verified"]        = True
                        agents[agent_id]["disconnected"]    = False
                        agents[agent_id]["disconnected_at"] = None
                        inactive_alerted.discard(agent_id)

                    print(f"[REPORT] '{agent_id}' → CPU: {cpu:.2f}%  RAM: {ram:.2f} MB")
                    conn.send(b"OK\n")

                except ValueError as exc:
                    print(f"[ERROR] Invalid REPORT data from {addr}: {exc}")
                    conn.send(b"ERROR InvalidData\n")

            # BYE 
            elif flag == "BYE" and len(parts) == 2:
                agent_id = parts[1]

                if agent_id != current_agent_id:
                    print(f"[SECURITY] '{addr}' tried to BYE '{agent_id}' "
                          f"but owns '{current_agent_id}'. Rejected.")
                    conn.send(b"ERROR Unauthorized\n")
                    continue

                with lock:
                    agents.pop(agent_id, None)
                    inactive_alerted.discard(agent_id)
                conn.send(b"OK\n")
                print(f"[BYE] Agent '{agent_id}' disconnected properly.")
                current_agent_id = None
                break

            # Message inconnu 
            else:
                print(f"[ERROR] Unknown/malformed message from {addr}: {data!r}")
                conn.send(b"ERROR InvalidMessageFormat\n")

    except Exception as e:
        print(f"[!] Error with client {addr}: {e}")
    finally:
        if current_agent_id:
            with lock:
                if current_agent_id in agents:
                    agents[current_agent_id]["disconnected"]    = True
                    agents[current_agent_id]["disconnected_at"] = time.time()
            print(f"[INFO] Agent '{current_agent_id}' connection lost — "
                  f"alert in {MAX_AGE}s if no reconnection.")
        conn.close()
        print(f"[-] Connection closed: {addr}")


# ===================================
# Thread : boucle d'écoute TCP
# ===================================
def listening_loop(server_sock):
    """Accepter les connexions entrantes en continu."""
    print(f"[TCP SERVER] Listening on port {PORT}  |  Max agents: {MAX_AGENTS}")
    print(f"[TCP SERVER] CSV export → {CSV_FILE}")
    print("         Press Ctrl+C (or close the window) to stop.\n")
    try:
        while True:
            conn, addr = server_sock.accept()
            threading.Thread(target=handle_client, args=(conn, addr),
                             daemon=True).start()
    except Exception:
        pass


# ==============================================================================================
# Main — GUI Tkinter : panneau live (haut, scrollable) + panneau historique (bas, scrollable)
# ==============================================================================================
def main():
    server_sock = socket.socket(IPV4, TCP)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(MAX_AGENTS)

    root = tk.Tk()
    root.title('Agent Monitor Dashboard "SocketMaster"')
    root.resizable(True, True)

    FONT_TITLE = ("Courier", 12, "bold")
    FONT_MONO  = ("Courier", 11)

    # Panneau LIVE (haut, scrollable, hauteur fixe)
    live_frame = tk.LabelFrame(
        root,
        text=" Live — current snapshot ",
        font=FONT_TITLE, fg="#1a6e2e",
        padx=10, pady=6
    )
    live_frame.pack(fill="x", padx=14, pady=(12, 4))

    live_scrollbar = tk.Scrollbar(live_frame)
    live_scrollbar.pack(side="right", fill="y")

    live_text = tk.Text(
        live_frame, font=FONT_MONO, state="disabled",
        width=80, height=8, wrap="none",
        bg="#f4fff6", relief="flat", bd=0,
        yscrollcommand=live_scrollbar.set
    )
    live_text.pack(side="left", fill="x", expand=True)
    live_scrollbar.config(command=live_text.yview)

    # Séparateur visuel 
    tk.Frame(root, height=2, bg="#cccccc").pack(fill="x", padx=14, pady=4)

    # Panneau HISTORIQUE (bas, scrollable, grandit avec la fenêtre) 
    history_frame = tk.LabelFrame(
        root,
        text=" History — all past snapshots ",
        font=FONT_TITLE, fg="#1a3a6e",
        padx=10, pady=6
    )
    history_frame.pack(fill="both", expand=True, padx=14, pady=(0, 12))

    scrollbar = tk.Scrollbar(history_frame)
    scrollbar.pack(side="right", fill="y")

    history_text = tk.Text(
        history_frame, font=FONT_MONO, state="disabled",
        width=80, height=14, wrap="none",
        bg="#f4f8ff", relief="flat", bd=0,
        yscrollcommand=scrollbar.set
    )
    history_text.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=history_text.yview)

    # Lancement des threads 
    threading.Thread(
        target=handle_stats, args=(live_text, history_text), daemon=True
    ).start()
    threading.Thread(
        target=listening_loop, args=(server_sock,), daemon=True
    ).start()

    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        server_sock.close()
        print("\n[TCP SERVER] Shutting down.")


if __name__ == "__main__":
    main()