import socket
import select
import sys
from constants import MAX_SIZE_LEN
 
class QuizClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.nickname = None
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        try:
            self.client_socket.connect((self.host, self.port))
        except Exception as e:
            print(f"Não Conseguimos nos conectar no servidor - Host: {self.host}, Port: {self.port}")
            sys.exit()
        self.client_socket.setblocking(False)


    def send_name_to_server(self, message):
        if message == "":
            print("Nome vazio não é permitido, pense em um nome melhor e se junte ao quiz novamente!")
            print("Desconectado!")
            sys.exit()
        else:
            try:
                self.client_socket.send(bytes(message, 'utf-8'))
            except Exception as e:
                self.client_socket.close()
                sys.exit()

    def send_to_server(self, message):
        try:
            self.client_socket.send(bytes(message, 'utf-8'))
        except Exception as e:
            self.client_socket.close()
            sys.exit()

    def receive_message(self):
        try:
            msg_len = self.client_socket.recv(MAX_SIZE_LEN)

            if not len(msg_len):
                return False

            message_length = int(msg_len.decode('utf-8').strip())
            return {'Length': msg_len, 'data': self.client_socket.recv(message_length)}

        except Exception as e:
            return False

    def run(self):
        self.nickname = input("Nickname: ")
        self.connect()
        self.send_name_to_server(self.nickname)

        while True:
            sockets_list = [sys.stdin, self.client_socket]
            read_sockets, write_socket, error_socket = select.select(sockets_list, [], [])
            for sock in read_sockets:
                if sock == self.client_socket:
                    encoded_message = self.receive_message()
                    if not encoded_message:
                        print("Desconectado!")
                        sys.exit()
                    else:
                        message = encoded_message['data'].decode('utf-8')
                        print(message)

                else:
                    message = sys.stdin.readline()
                    self.send_to_server(message)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("A chamada ao client.py precisa ter 2 argumentos: IP (Host), Porta (Host)")
        exit()

    host = str(sys.argv[1])
    port = int(sys.argv[2])

    client = QuizClient(host, port)
    client.run()