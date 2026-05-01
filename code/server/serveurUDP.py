import socket
import threading
import time
import datetime
import csv
import tkinter as tk

# Constantes réseau 
IPV4 = socket.AF_INET
UDP  = socket.SOCK_DGRAM

HOST = "0.0.0.0"
PORT = 5001
T    = 5

# Limites 
MAX_AGE      = 3 * T   # secondes sans REPORT avant de considérer un agent inactif
MAX_AGENTS   = 30      # nombre maximum d'agents simultanés
RATE_LIMIT_S = 2       # délai minimum entre deux REPORT d'un même agent

# État global 
agents           = {}
lock             = threading.Lock()
inactive_alerted = set()
rate_limit_count = {}   # compteur de requêtes bloquées par agent (résumé toutes les T s)

# addr_to_agent : addr (ip, port) → agent_id
# Equivalent UDP du current_agent_id TCP : chaque adresse source ne peut
# enregistrer qu'un seul agent, et elle seule peut lui envoyer des REPORT/BYE
addr_to_agent = {}

# Nom du fichier CSV avec horodatage 
_ts      = time.strftime("_%b-%d-%Y_%H%M", time.localtime())
CSV_FILE = "statsUDP" + _ts + ".csv"


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


# ============================================================
# Thread : statistiques périodiques + mise à jour GUI
# ============================================================
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

                # En UDP il n'y a pas de connexion persistante donc pas de
                # coupure brutale détectable : on se base uniquement sur
                # last_seen. Cependant on conserve le même mécanisme
                # disconnected/disconnected_at pour les BYE explicites ou
                # toute coupure signalée manuellement
                if info.get("disconnected"):
                    elapsed = now - info.get("disconnected_at", now)
                    if elapsed >= MAX_AGE:
                        if agent_id not in inactive_alerted:
                            print(f"\n[ALERT] Agent '{agent_id}' DISCONNECTED unexpectedly "
                                  f"(silent for {elapsed:.0f}s)")
                            inactive_alerted.add(agent_id)
                        to_remove.append(agent_id)

                # Silencieux depuis trop longtemps (cas principal en UDP)
                else:
                    elapsed = now - info["last_seen"]
                    if elapsed > MAX_AGE:
                        if agent_id not in inactive_alerted:
                            print(f"\n[ALERT] Agent '{agent_id}' is INACTIVE! "
                                  f"(silent for {elapsed:.0f}s)")
                            inactive_alerted.add(agent_id)
                        to_remove.append(agent_id)

            for agent_id in to_remove:
                # Nettoyer aussi addr_to_agent
                owner_addr = agents[agent_id].get("owner_addr")
                if owner_addr and addr_to_agent.get(owner_addr) == agent_id:
                    del addr_to_agent[owner_addr]
                agents.pop(agent_id, None)
                print(f"[INFO] Agent '{agent_id}' removed from stats.")

            # Résumé rate-limit (affiché toutes les T secondes)
            if rate_limit_count:
                print("\n[RATE LIMIT] Blocked request summary:")
                for aid, count in rate_limit_count.items():
                    print(f"  - {aid}: {count} blocked request(s)")
                rate_limit_count.clear()

            # Seuls les agents ayant reçu au moins un REPORT valide sont affichés
            active = {
                k: v for k, v in agents.items()
                if v.get("verified")
                and not v.get("disconnected")
                and (now - v["last_seen"]) <= T
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
# Handlers par type de message
# ===================================
def handle_hello(parts, addr, sock):
    if len(parts) < 3:
        sock.sendto(b"ERROR InvalidMessageFormat\n", addr)
        return

    agent_id = parts[1]
    hostname = " ".join(parts[2:])

    with lock:
        # Equivalent du "un seul HELLO par connexion" TCP
        if addr in addr_to_agent:
            existing = addr_to_agent[addr]
            print(f"[BLOCK] {addr} tried a second HELLO (already owns '{existing}').")
            sock.sendto(b"ERROR AlreadyRegistered\n", addr)
            return

        # Refuser si l'agent_id est déjà pris par une autre adresse
        if agent_id in agents:
            print(f"[BLOCK] '{agent_id}' already registered by another address. "
                  f"{addr} refused.")
            sock.sendto(b"ERROR AgentIDTaken\n", addr)
            return

        if len(agents) >= MAX_AGENTS:
            print(f"[BLOCK] Agent limit ({MAX_AGENTS}) reached. '{agent_id}' refused.")
            sock.sendto(b"ERROR Max agents reached\n", addr)
            return

        agents[agent_id] = {
            "hostname"        : hostname,
            "cpu"             : 0.0,
            "ram"             : 0.0,
            "last_seen"       : time.time(),
            "last_report"     : 0.0,
            "verified"        : False,   # devient True après le 1er REPORT valide
            "owner_addr"      : addr,    # adresse propriétaire (équivalent current_agent_id)
            "disconnected"    : False,   # devient True si coupure signalée
            "disconnected_at" : None,    # timestamp de la coupure
        }
        addr_to_agent[addr] = agent_id
        inactive_alerted.discard(agent_id)

    print(f"[HELLO] Agent '{agent_id}' ({hostname}) registered from {addr}.")
    sock.sendto(b"OK\n", addr)


def handle_report(parts, addr, sock):
    if len(parts) != 5:
        sock.sendto(b"ERROR InvalidMessageFormat\n", addr)
        return
    try:
        agent_id = parts[1]
        cpu      = float(parts[3])
        ram      = float(parts[4])

        if not (0 <= cpu <= 100) or ram < 0:
            raise ValueError("CPU/RAM out of range")

        with lock:
            if agent_id not in agents:
                print(f"[WARNING] REPORT from unregistered agent '{agent_id}', ignored.")
                sock.sendto(b"ERROR Unknown agent\n", addr)
                return

            # Ownership check : seule l'adresse propriétaire peut REPORT
            if agents[agent_id]["owner_addr"] != addr:
                print(f"[SECURITY] {addr} tried to REPORT for '{agent_id}' "
                      f"but owner is {agents[agent_id]['owner_addr']}. Rejected.")
                sock.sendto(b"ERROR Unauthorized\n", addr)
                return

            now = time.time()
            if now - agents[agent_id]["last_report"] < RATE_LIMIT_S:
                rate_limit_count[agent_id] = rate_limit_count.get(agent_id, 0) + 1
                sock.sendto(b"ERROR Rate limit\n", addr)
                return

            agents[agent_id]["cpu"]             = cpu
            agents[agent_id]["ram"]             = ram
            agents[agent_id]["last_seen"]       = now
            agents[agent_id]["last_report"]     = now
            agents[agent_id]["verified"]        = True
            agents[agent_id]["disconnected"]    = False
            agents[agent_id]["disconnected_at"] = None
            inactive_alerted.discard(agent_id)

        print(f"[REPORT] '{agent_id}' → CPU: {cpu:.2f}%  RAM: {ram:.2f} MB")
        sock.sendto(b"OK\n", addr)

    except ValueError as exc:
        print(f"[ERROR] Invalid REPORT data from {addr}: {exc}")
        sock.sendto(b"ERROR InvalidData\n", addr)


def handle_bye(parts, addr, sock):
    if len(parts) != 2:
        sock.sendto(b"ERROR InvalidMessageFormat\n", addr)
        return

    agent_id = parts[1]

    with lock:
        if agent_id not in agents:
            sock.sendto(b"ERROR Unknown agent\n", addr)
            return

        # Ownership check : seule l'adresse propriétaire peut BYE
        if agents[agent_id]["owner_addr"] != addr:
            print(f"[SECURITY] {addr} tried to BYE '{agent_id}' "
                  f"but owner is {agents[agent_id]['owner_addr']}. Rejected.")
            sock.sendto(b"ERROR Unauthorized\n", addr)
            return

        # Nettoyer addr_to_agent en même temps
        addr_to_agent.pop(addr, None)
        agents.pop(agent_id, None)
        inactive_alerted.discard(agent_id)

    sock.sendto(b"OK\n", addr)
    print(f"[BYE] Agent '{agent_id}' disconnected.")


# ===================================
# Boucle d'écoute UDP (thread dédié)
# ===================================
def listening_loop(server_sock):
    print(f"[UDP SERVER] Listening on UDP port {PORT}  |  Max agents: {MAX_AGENTS}")
    print(f"[UDP SERVER] CSV export → {CSV_FILE}")
    print("         Press Ctrl+C or close the window to stop.\n")
    try:
        while True:
            data, addr = server_sock.recvfrom(1024)
            msg   = data.decode().strip()
            parts = msg.split()

            if not parts:
                continue

            flag = parts[0]

            if   flag == "HELLO":  handle_hello(parts, addr, server_sock)
            elif flag == "REPORT": handle_report(parts, addr, server_sock)
            elif flag == "BYE":    handle_bye(parts, addr, server_sock)
            else:
                print(f"[ERROR] Unknown/malformed message from {addr}: {msg!r}")
                server_sock.sendto(b"ERROR InvalidMessageFormat\n", addr)

    except Exception:
        pass


# ====================================================================================
# Main — GUI Tkinter : panneau live (haut, scrollable) + panneau historique (bas)
# =====================================================================================
def main():
    server_sock = socket.socket(IPV4, UDP)
    server_sock.bind((HOST, PORT))

    root = tk.Tk()
    root.title('Agent Monitor Dashboard "SocketMaster" — UDP')
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
        print("\n[UDP SERVER] Shutting down.")


if __name__ == "__main__":
    main()