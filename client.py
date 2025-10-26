import socket
import threading

def receber_mensagens(sock):
    while True:
        try:
            msg = sock.recv(1024).decode('utf-8')
            if not msg:
                print("\n[INFO] Servidor desconectado.")
                break

            partes = msg.split('|', 2)
            tipo = partes[0]

            if tipo == 'SERVER':
                print(f"\n[{partes[1]}]: {partes[2]}")
            elif tipo == 'ROOM_MSG':
                print(f"\n<{partes[1]}> {partes[2]}")
            elif tipo == 'PV':
                print(f"\n[Privado de {partes[1]}]: {partes[2]}")
            elif tipo == 'JOIN_OK':
                print(f"\n[SERVIDOR]: {partes[1]}")
            elif tipo == 'ROOM_LIST':
                salas = partes[1].split(',')
                print(f"\n[SERVIDOR] Salas disponíveis: {', '.join(salas)}")
            elif tipo == 'USER_LIST':
                sala = partes[1]
                usuarios = partes[2].split(',')
                print(f"\n[SERVIDOR] Usuários na sala {sala}: {', '.join(usuarios)}")
            else:
                print(f"\n[MENSAGEM DESCONHECIDA]: {msg}")

        except ConnectionResetError:
            print("\n[ERRO] Conexão com o servidor perdida.")
            break
        except Exception as erro:
            print(f"\n[ERRO] {erro}")
            break

def iniciar_cliente():
    ip_server = input("Digite o IP do servidor: ").strip()
    port = 55555

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip_server, port))
    except Exception as erro:
        print(f"[ERRO] Não foi possível conectar ao servidor. Erro: {erro}")
        return

    nickname = input("Digite seu nickname: ")
    ip_client = sock.getsockname()[0]
    sock.send(f"{ip_client}|{nickname}".encode('utf-8'))

    try:
        resposta = sock.recv(1024).decode('utf-8')
        if not resposta.startswith("JOIN_OK"):
            print(resposta)
            return
    except Exception as erro:
        print(f"[ERRO] Falha ao receber confirmação do servidor: {erro}")
        return

    threading.Thread(target=receber_mensagens, args=(sock,), daemon=True).start()

    sala_atual = "Geral"

    print("\n--- Conectado ao servidor ---")
    print("Comandos disponíveis:")
    print("/entrar <sala>   → entrar em outra sala")
    print("/sair <sala>     → sair de uma sala")
    print("/nick <novo>     → mudar seu nickname")
    print("/pm <nick> <msg> → enviar mensagem privada")
    print("/salas           → listar salas disponíveis")
    print("/usuarios <sala> → listar usuários de uma sala")
    print("/desconectar     → sair do chat")
    print("-------------------------------------")

    while True:
        entrada = input(f"[{nickname} @ {sala_atual}]> ").strip()
        if not entrada:
            continue
        try:
            if entrada.startswith('/entrar '):
                nova_sala = entrada.split(' ', 1)[1]
                sock.send(f"JOIN_ROOM|{nova_sala}".encode('utf-8'))
                sala_atual = nova_sala

            elif entrada.startswith('/sair '):
                partes = entrada.split(' ', 1)
                if len(partes) == 2:
                    sala = partes[1] 
                else:
                    sala = sala_atual
                sock.send(f"LEAVE_ROOM|{sala}".encode('utf-8'))
                if sala == sala_atual:
                    sala_atual = 'Geral'

            elif entrada.startswith('/nick '):
                novo_nickname = entrada.split(' ', 1)[1]
                sock.send(f"CHECKNICK|{novo_nickname}".encode('utf-8'))
                nickname = novo_nickname

            elif entrada.startswith('/pm '):
                dest = entrada.split(' ', 2)[1]
                msg = entrada.split(' ', 2)[2]
                sock.send(f"PRIVMSG|{dest}|{msg}".encode('utf-8'))

            elif entrada == '/salas':
                sock.send(b"LIST_ROOMS")

            elif entrada.startswith('/usuarios '):
                sala = entrada.split(' ', 1)[1]
                sock.send(f"LIST_USERS|{sala}".encode('utf-8'))

            elif entrada == '/desconectar':
                print("Saindo do chat...")
                sock.close()
                break

            else:
                sock.send(f"ROOM_MSG|{sala_atual}|{entrada}".encode('utf-8'))

        except Exception as erro:
            print(f"[ERRO] Não foi possível enviar a mensagem: {erro}")
            break

if __name__ == "__main__":
    iniciar_cliente()
