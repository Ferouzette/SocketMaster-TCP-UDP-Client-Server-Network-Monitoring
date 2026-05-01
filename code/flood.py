import threading
import socket
import uuid
import random
import psutil
import time  

cpu_base = psutil.cpu_percent(interval=None)
ram_base = psutil.virtual_memory().used / (1024 * 1024)

def flood_server(agent_id):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("127.0.0.1", 5000))
        sock.send(f"HELLO {agent_id} FloodPC\n".encode())
        resp = sock.recv(1024).decode().strip()
        if "ERROR" in resp:
            print(f"[{agent_id}] Rejected by server: {resp}")
            sock.close()
            return
        for _ in range(1000):
            cpu = round(max(0.0, min(100.0, cpu_base + random.uniform(-10.0, 10.0))), 2)
            ram = round(max(0.0, ram_base + random.uniform(-50.0, 50.0)), 2)
            sock.send(f"REPORT {agent_id} 0 {cpu} {ram}\n".encode())
            sock.recv(1024)
        
        # Pause : laisser le dashboard capturer au moins 2 cycles (T=5s)
        time.sleep(12)
        sock.close()
    except (ConnectionRefusedError, OSError, BrokenPipeError) as e:
        print(f"[{agent_id}] Connection lost: {e}")

print("[ATTACK] Starting flood simulation with 50 threads...")
threads = [
    threading.Thread(target=flood_server, args=(f"agent_{str(uuid.uuid4())[:8]}",))
    for _ in range(50)
]
for t in threads:
    t.start()
for t in threads:
    t.join()
print("[ATTACK] Flood simulation complete.")