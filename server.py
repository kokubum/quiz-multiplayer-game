import socket
import select
import random
import sys
import time
from questions import Q_and_A
from _thread import *
from constants import MAX_SIZE_LEN

random.shuffle(Q_and_A)

quiz_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
quiz_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

if len(sys.argv) != 3:
	print("Para inicializar o servidor é necessario passar: IP (Host), Porta (Host)")
	exit()

number_of_participants = int(input("Informe o numero de participantes (MAX=4): "))  
number_joined = 0

if number_of_participants > 4 or number_of_participants < 1:
	while number_of_participants > 4 or number_of_participants < 1:
		number_of_participants = int(input("Informe um número válido: "))


IP_address = str(sys.argv[1])
Port = int(sys.argv[2])
quiz_server.bind((IP_address, Port))
quiz_server.listen(10)
print("Servidor rodando!")

print(f"Esperando Participantes se conectarem ao servidor: IP={IP_address}, PORT={Port}")

clients_list = []
participants = {}
marks = {}
mapping = {}
Person = [quiz_server]
answer = [-1]

def receive_message(client_socket):
	message = client_socket.recv(1024).decode('utf-8')
	return message

def send_to_one(receiver, message):
	message = f"{len(message):<{MAX_SIZE_LEN}}" + message 
	try:
		receiver.send(bytes(message, 'utf-8'))
	except:
		receiver.close()
		clients_list.remove(receiver)

def send_to_all(sender, message):
	message = f"{len(message):<{MAX_SIZE_LEN}}" + message
	for socket in clients_list:
		if (socket != quiz_server and socket != sender):
			try:
				socket.send(bytes(message, 'utf-8'))
			except:
				socket.close()
				clients_list.remove(socket)

def update_marks(player, number):
	print(participants[mapping[player]])
	marks[participants[mapping[player]]] += number
	print(marks)
	send_to_all(quiz_server, "\nPONTUACAO: ")
	for j in marks:
		send_to_all(quiz_server, ">> " + str(j) + ": " + str(marks[j]))

def end_quiz():
	send_to_all(quiz_server, "GAME OVER\n")
	print("GAME OVER\n")
	for i in marks:
		if marks[i] >= 5:
			send_to_all(quiz_server, "GANHADOR: " + str(i))
	send_to_all(quiz_server, "TABELA DE PONTOS:")
	print("TABELA DE PONTOS:")
	for i in marks:
		send_to_all(quiz_server, ">> " + str(i) + ": " + str(marks[i]))
		print(">> " + str(i) + ": " + str(marks[i]))
	sys.exit()

def ask_question():
	if len(Q_and_A) != 0:
		question_and_answer = Q_and_A[0]
		question = question_and_answer[0]
		options = question_and_answer[1]
		Answer = question_and_answer[2]

		random.shuffle(options)
		option_number = 1

		send_to_all(quiz_server, "\nQ. " + str(question))
		print("\nQ. " + str(question))
		for j in range(len(options)):
			send_to_all(quiz_server, "   " + str(option_number) + ") " + str(options[j]))
			print("   " + str(option_number) + ") " + str(options[j]))
			if options[j] == Answer: 
				answer.pop(0)
				answer.append(int(option_number))
			option_number += 1
		send_to_all(quiz_server, "\nAperte o ENTER pra Responder")
		print("Resposta: alternativa numero " + str(answer))
	else:
		send_to_all(quiz_server, "Questoes ESGOTADAS!")
		end_quiz()
		sys.exit()

def quiz():
		Person[0] = quiz_server
		random.shuffle(Q_and_A)
		ask_question()
		keypress = select.select(clients_list, [], [], 10)
		if len(keypress[0]) > 0:
			who_buzzed = keypress[0][0]
			send_to_one(who_buzzed, "VOCE APERTOU A BUZINA")
			send_to_one(who_buzzed, "INSIRA SUA RESPOSTA: ")
			send_to_all(who_buzzed, "BUZINA APERTADA")
			print("BUZINA APERTADA")
			time.sleep(0.01)
			Person.pop(0)
			Person.append(who_buzzed)
			t0 = time.time()
			Q_and_A.pop(0)

			answering = select.select(Person, [], [], 10)
			if len(answering) > 0:
				if time.time() - t0 >= 10:
					send_to_one(who_buzzed, "NAO RESPONDEU A TEMPO! UEN UEN UEN")
					send_to_all(quiz_server, str(participants[mapping[who_buzzed]]) + " -0.5")
					print(str(participants[mapping[who_buzzed]]) + " -0.5")
					update_marks(who_buzzed, -0.5)
					time.sleep(3)
					quiz()
				else:
					time.sleep(3)
					quiz()
			else:
				print("NADA!")						
		else:
			send_to_all(quiz_server, "BUZINA NAO FOI APERTADA")
			print("BUZINA NAO FOI APERTADA")
			time.sleep(3)
			Q_and_A.pop(0)
			quiz()

clients_list.append(quiz_server)

while True:
	rList, wList, error_sockets = select.select(clients_list, [], [])
	for socket in rList:
		if socket == quiz_server:
			client_socket, client_address = quiz_server.accept()
			if number_joined == number_of_participants:
				send_to_one(client_socket, "Sala LOTADA!")
				client_socket.close()
			else:
				name = receive_message(client_socket)
				if name:
					if name in participants.values():
						send_to_one(client_socket, "Esse nome ja existe. Pensa um pouco mais e seleciona outro para jogar com a gente!")
						client_socket.close()
					else:
						participants[client_address] = name
						marks[name] = 0
						number_joined += 1
						mapping[client_socket] = client_address
						clients_list.append(client_socket)
						print("Participante CONECTADO: " + str(client_address) +" [ " + participants[client_address] + " ]" )
						if number_joined < number_of_participants:
							send_to_one(client_socket, "Bem vindo ao QUIZ " + name + "!\nEspera so um pouquinho por mais participantes...")
	
						if number_joined == number_of_participants:
							send_to_all(quiz_server, "\nParticipantes:")
							for i in participants:
								send_to_all(quiz_server,">> " + participants[i])
							send_to_all(quiz_server, "\nCOMECAREMOS EM 30 SEGUNDOS...")
							send_to_all(quiz_server, "\n> Use o Enter como sua buzina.\n> 10 segundos para responder cada questao..\n> 1 ponto por questao correta.\n> -0.5 ponto devido a erro ou resposta invalida.\n\n> Ganha o jogo o primeiro a completar 5 pontos!")
							print("\n" + str(number_of_participants) + " participant(s) connected! The quiz will begin in 30 seconds")
							time.sleep(30)
							start_new_thread(quiz, ())
		else:
			msg = receive_message(socket)
			print(msg)
			if socket == Person[0]:
				try:
					ans = int(msg)
					if ans == answer[0]:
						send_to_one(socket, "Resposta CORRETA - MAOE!")
						send_to_all(quiz_server, str(participants[mapping[socket]]) + " +1")
						print(str(participants[mapping[socket]]) + " +1")
						update_marks(socket, 1.0)
						Person[0] = quiz_server
						if marks[participants[mapping[socket]]] >= 5:
							end_quiz()
										
					else:
						send_to_one(socket, "Resposta ERRADA - Errou Rude Errou Feio")
						send_to_all(quiz_server, str(participants[mapping[socket]]) + " -0.5")
						print(str(participants[mapping[socket]]) + " -0.5")
						update_marks(socket, -0.5)
						Person[0] = quiz_server
				except ValueError:
					send_to_one(socket, "Resposta INVALIDA")
					send_to_all(quiz_server, str(participants[mapping[socket]]) + " -0.5")
					print(str(participants[mapping[socket]]) + " -0.5")
					update_marks(socket, -0.5)
					Person[0] = quiz_server		

			elif Person[0] != quiz_server:
				send_to_one(socket, "Tempo ESGOTADO!")

			
client_socket.close()
quiz_server.close()