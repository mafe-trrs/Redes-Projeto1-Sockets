import socket
import threading

HOST = '0.0.0.0'
PORT = 55555

MAX_SALAS = 5  

clientes = {}         # socket -> nickname
salas = {'Geral': []} # nome_sala -> lista de sockets
cliente_sala = {}      # socket -> nome_sala
lock = threading.Lock()  # evita conflito entre threads


def broadcast_global(mensagem):
    with lock:
        if len(clientes) == 0:
            print("[LOG] Nenhum cliente conectado. Aviso não enviado.")
            return
        print(f"[AVISO] Enviando: {mensagem}") 
        for cliente_socket in list(clientes.keys()):
            try:
                cliente_socket.send(f"SERVER|AVISO DO SERVIDOR|{mensagem}".encode('utf-8'))
            except:
                remover_cliente(cliente_socket)

def input_admin():
    while True:
        mensagem = input("[ADMIN] Digite um aviso global: ")
        if mensagem:
            broadcast_global(mensagem)

def broadcast_sala(sala, mensagem, remetente=None):
    for cliente in salas.get(sala, []):
        if cliente != remetente:
            try:
                cliente.send(mensagem.encode('utf-8'))
            except:
                remover_cliente(cliente)

def remover_cliente(sock):
    with lock:
        nick = clientes.get(sock, "Desconhecido")
        sala = cliente_sala.get(sock, "Geral")

        if sala in salas and sock in salas[sala]:
            salas[sala].remove(sock)
        if sock in clientes:
            del clientes[sock]
        if sock in cliente_sala:
            del cliente_sala[sock]
        if sala != 'Geral' and not salas.get(sala):
            del salas[sala]
            print(f"[SALA REMOVIDA] Sala '{sala}' estava vazia e foi apagada.")

    broadcast_sala(sala, f"ROOM_MSG|{sala}|[Servidor]: {nick} saiu da sala.")
    print(f"[DESCONECTADO] {nick} saiu ({sala})")
    try:
        sock.close()
    except:
        pass

def tratar_cliente(sock, endereco):
    try:
        dados_iniciais = sock.recv(1024).decode('utf-8')
        if not dados_iniciais:
            return
        ip_cliente, nick = dados_iniciais.split('|', 1)
    except:
        sock.close()
        return

    with lock:
        clientes[sock] = nick
        salas['Geral'].append(sock)
        cliente_sala[sock] = 'Geral'

    print(f"\n[NOVA CONEXÃO] {nick} entrou ({endereco[0]})")
    sock.send("JOIN_OK|Conectado à sala Geral.".encode('utf-8'))
    broadcast_sala("Geral", f"ROOM_MSG|Geral|[Servidor]: {nick} entrou na sala.")

    while True:
        try:
            msg = sock.recv(1024).decode('utf-8')
            if not msg:
                break

            partes = msg.split('|', 2)
            comando = partes[0]

            if comando == "ROOM_MSG":
                _, sala, conteudo = partes
                if sala in salas:
                    broadcast_sala(sala, f"ROOM_MSG|{nick}|{conteudo}", sock)
                    if sala == "Geral":
                        print(f"[GERAL] {nick}: {conteudo}")

            elif comando == "JOIN_ROOM":
                nova_sala = partes[1]
                with lock:
                    sala_atual = cliente_sala.get(sock, "Geral")

                    if sala_atual == nova_sala:
                        sock.send(f"SERVER|INFO|Você já está na sala {nova_sala}.".encode())
                        continue

                    salas_ativas = []
                    for sala_nome in salas.keys():
                        if sala_nome != 'Geral':
                            salas_ativas.append(sala_nome)

                    if nova_sala not in salas and len(salas_ativas) >= MAX_SALAS:
                        sock.send(f"SERVER|INFO|Número máximo de salas atingido.".encode())
                        continue

                    if sala_atual in salas and sock in salas[sala_atual]:
                        salas[sala_atual].remove(sock)
                        broadcast_sala(sala_atual, f"ROOM_MSG|{sala_atual}|[Servidor]: {nick} saiu da sala.")
                        if sala_atual != 'Geral' and len(salas[sala_atual]) == 0:
                            del salas[sala_atual]
                            print(f"[SALA REMOVIDA] Sala '{sala_atual}' estava vazia e foi apagada.")

                    if nova_sala not in salas:
                        salas[nova_sala] = []
                        print(f"[NOVA SALA] {nova_sala} criada.")

                    salas[nova_sala].append(sock)
                    cliente_sala[sock] = nova_sala

                sock.send(f"JOIN_OK|Entrou na sala {nova_sala}.".encode())
                broadcast_sala(nova_sala, f"ROOM_MSG|{nova_sala}|[Servidor]: {nick} entrou na sala.", sock)
                print(f"[MUDOU DE SALA] {nick}: {sala_atual} -> {nova_sala}")

            elif comando == "LEAVE_ROOM":
                sala = partes[1]
                with lock:
                    if sala in salas and sock in salas[sala]:
                        salas[sala].remove(sock)
                        broadcast_sala(sala, f"ROOM_MSG|{sala}|[Servidor]: {nick} saiu da sala.")
                        if sala != 'Geral' and len(salas[sala]) == 0:
                            del salas[sala]
                            print(f"[SALA REMOVIDA] Sala '{sala}' estava vazia e foi apagada.")

                    if sock not in salas['Geral']:
                        salas['Geral'].append(sock)
                    cliente_sala[sock] = 'Geral'

                sock.send("JOIN_OK|Você voltou para a sala Geral.".encode('utf-8'))
                broadcast_sala("Geral", f"ROOM_MSG|Geral|[Servidor]: {nick} voltou para a sala Geral.", sock)
                print(f"[VOLTOU PARA GERAL] {nick}")

            elif comando == "PRIVMSG":
                _, destino, conteudo = partes
                alvo = None
                with lock:
                    for s, nome in clientes.items():
                        if nome == destino:
                            alvo = s
                            break
                if alvo:
                    alvo.send(f"PV|{nick}|{conteudo}".encode('utf-8'))
                else:
                    sock.send(f"SERVER|INFO|Usuário '{destino}' não encontrado.".encode('utf-8'))

            elif comando == "CHECKNICK":
                novo_nick = partes[1]
                with lock:
                    clientes[sock] = novo_nick
                sock.send(f"SERVER|INFO|Nickname alterado para {novo_nick}".encode('utf-8'))
                print(f"[NICK ALTERADO] {nick} -> {novo_nick}")
                nick = novo_nick

            elif comando == "LIST_ROOMS":
                with lock:
                    salas_ativas = ['Geral']
                    for nome_sala, usuarios in salas.items():
                        if nome_sala != 'Geral' and len(usuarios) > 0:
                            salas_ativas.append(nome_sala)
                    if len(salas_ativas) > 0:
                        salas_ordenadas = sorted(salas_ativas)
                        lista = ', '.join(sorted(salas_ordenadas))
                        sock.send(f"ROOM_LIST|{lista}".encode('utf-8'))
                        print(f"[LOG] {nick} solicitou /salas -> {lista}")
                    else:
                        sock.send("SERVER|INFO|Não há salas disponíveis.".encode('utf-8'))
                        print(f"[LOG] {nick} solicitou /salas -> não há salas")

            elif comando == "LIST_USERS":
                sala = partes[1]
                with lock:
                    if sala not in salas:
                        sock.send(f"SERVER|INFO|Sala '{sala}' não existe.".encode('utf-8'))
                        print(f"[LOG] {nick} solicitou /usuarios {sala} -> sala não existe")
                    else:
                        nomes = []
                        for c in salas[sala]:
                            if c in clientes:
                                nomes.append(clientes[c])
                        if nomes:
                            sock.send(f"USER_LIST|{sala}|{','.join(nomes)}".encode('utf-8'))
                            print(f"[LOG] {nick} solicitou /usuarios {sala} -> {', '.join(nomes)}")
                        else:
                            sock.send(f"SERVER|INFO|Não há usuários na sala '{sala}'.".encode('utf-8'))
                            print(f"[LOG] {nick} solicitou /usuarios {sala} -> sala vazia")

        except:
            break
    remover_cliente(sock)

def iniciar_servidor():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind((HOST, PORT))
    servidor.listen()
    print(f"[SERVIDOR ATIVO] Escutando em {HOST}:{PORT}")

    threading.Thread(target=input_admin, daemon=True).start()

    while True:
        sock, endereco = servidor.accept()
        threading.Thread(target=tratar_cliente, args=(sock, endereco), daemon=True).start()

if __name__ == "__main__":
    iniciar_servidor()




