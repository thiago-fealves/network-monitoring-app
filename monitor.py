import socket
import json
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich import box

# Informações da conexão
HOST = "0.0.0.0"
PORT = 5050

# Definição do console e do dicionário com os dados de cada client
console = Console()
clients_data = {} # Cada client tem um ID único e um array com seus status

# Configura o Server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Facilita reiniciar o servidor
server.bind((HOST, PORT))
server.listen(5)
server.setblocking(False) # Permite o server se manter rodando mesmo sem nenhum client

connections = {} # Armazena cada socket de cada client

def is_internal_ip(ip):
    """Verifica se o IP do cliente pertence à rede 192.168.18.x"""
    return ip.startswith("192.168.18.")

def render_dashboard():
    layout = Layout()

    clients_layout = Layout() # Uma box dentro do layout principal, que também é uma box
    clients_layout.split_row( # Faz uma linha, deixando os clientes lado a lado
        *[
            Layout(
                Panel( # Vertical por conta dos \n
                    f"[bold cyan]ID:[/bold cyan] {id_unico.removesuffix('.local')}\n\n"
                    f"[bold blue]CPU:[/bold blue] {stats['CPU']}%\n"
                    f"[bold green]Memória:[/bold green] {stats['Memória']}%\n"
                    f"[bold yellow]Disco:[/bold yellow] 📥 {stats['Disco_Leitura']:.2f} MB/s | 📤 {stats['Disco_Escrita']:.2f} MB/s",
                    title=f"📟 {id_unico.removesuffix('.local')}",
                    border_style="cyan",
                    box=box.ROUNDED,# Estilo
                )
            )
            for id_unico, stats in clients_data.items()
        ]
    )

    layout.split_column(clients_layout) # Mantém eles lado a lado
    return layout

with Live(console=console, refresh_per_second=2) as live: # Atualiza dinamicamente sem limpar e reescrever
    try:
        while True:
            try:
                conn, addr = server.accept()
                client_ip, _ = addr # só o endereço ip interessa, a porta é descartada
                
                # Medida de segurança, como é pra ser um monitoramento privado, ninguém de fora da rede precisa acessar
                if not is_internal_ip(client_ip):
                    console.log(f"[red]Conexão rejeitada de {client_ip} (IP não autorizado)[/red]")
                    conn.close()
                    continue  
                
                conn.setblocking(False) # Permite que a conexão continue mesmo sem receber dados a principio
                connections[conn] = None  # Inicialmente a conexão não tem ID
                console.log(f"Nova conexão de {client_ip}")

            except BlockingIOError:
                pass  

            disconnected_clients = []

            for conn in list(connections):  # Itera sobre a lista e confere se alguém se desconectou
                try:
                    data = conn.recv(1024).decode()
                    if not data:
                        raise ConnectionResetError  # Cliente fechou a conexão
                    
                    for json_data in data.strip().split("\n"):
                        # Carrega os dados e associa à um ID no dicionário
                        stats = json.loads(json_data)
                        client_id = stats["ID"]
                        clients_data[client_id] = stats

                        connections[conn] = client_id  # Associa ID e os dados no dicionário à conexão

                except (BlockingIOError, json.JSONDecodeError):
                    pass  # Continua normalmente e espera o proximo pacote

                except (ConnectionResetError, BrokenPipeError, OSError):
                    # Cliente desconectado
                    disconnected_clients.append(conn)

            # Remove clientes desconectados
            for conn in disconnected_clients:
                client_id = connections.pop(conn, None)
                if client_id and client_id in clients_data:
                    del clients_data[client_id]
                console.log(f"[yellow]Cliente {client_id} desconectado[/yellow]")
                conn.close()

            # Depois de fazer toda a verificação sobre essas conexões, renderiza o monitor
            live.update(render_dashboard())

    # Desliga o servidor enviando um sinal aos clients
    except KeyboardInterrupt:
        print("\nFinalizando servidor...")
        for conn in list(connections):
            conn.close()
        server.close()
