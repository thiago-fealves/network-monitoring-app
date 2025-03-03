import psutil
import socket
import json
import time

SERVER_IP = "192.168.X.X" # Substitua pelo IP do servidor
PORT = 5050

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER_IP, PORT))

ID_UNICO = socket.gethostname()

def get_system_stats():
    # Pega dois timestamps onde mede entrada e saída no disco
    disk_io_antes = psutil.disk_io_counters()
    time.sleep(1)  
    disk_io_depois = psutil.disk_io_counters()

    leitura_mb = (disk_io_depois.read_bytes - disk_io_antes.read_bytes) / (1024 * 1024)
    escrita_mb = (disk_io_depois.write_bytes - disk_io_antes.write_bytes) / (1024 * 1024)

    return {
        "ID": ID_UNICO,
        "IP": socket.gethostbyname(socket.gethostname()),
        "CPU": psutil.cpu_percent(),
        "Memória": psutil.virtual_memory().percent,
        "Disco_Leitura": leitura_mb,  
        "Disco_Escrita": escrita_mb 
    }

try:
    while True:
        stats = json.dumps(get_system_stats()) + "\n" # Para separar cada pacote
        client.sendall(stats.encode())

# Finaliza o programa
except KeyboardInterrupt:
    print("Finalizando conexão...")
    client.close()
