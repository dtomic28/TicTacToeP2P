import socket
import json
from threading import Thread
from IGameInstance import *


class Client(IGameInstance):
    def __init__(self, host="localhost", port="12345"):
        super().__init__("client", host, port)
        self.id = "X"

    def initialize(self):
        print("Connecting to server...")
        self.socket.connect((self.host, self.port))
        self.connection = self.socket
        print("Connected to server.")

    def process_packet(self, packet):
        packet_type = packet.get("type")

        if packet_type == PacketType.PLAYER_TURN.value:
            self.current_player = packet.get("player")
            print(f"It's {self.current_player}'s turn!")

        elif packet_type == PacketType.GAME_STATE.value:
            self.board = packet.get("board")
            print("Updated board:", self.board)

        elif packet_type == PacketType.RESET.value:
            print("Game reset requested by the server.")
            self.reset_game()  # Call the reset logic
        elif packet_type == PacketType.GAME_WIN.value:
            result = packet.get("result")
            self.gui_callback(
                {"type": "END", "result": result})

    def reset_game(self):
        self.board = [" "] * 9  # Clear the board
        self.current_player = None  # Reset the current player
        self.packet_queue.queue.clear()  # Clear any pending packets
        self.isOver = False  # Reset game over flag

    def play_turn(self, index):
        if self.board[index] == " ":
            # Send the MOVE packet to the server
            self.send_packet(
                {"type": PacketType.MOVE.value, "player": self.id, "move": index}
            )
        else:
            print("Invalid move. This spot is already taken.")

    def run_game(self):
        while self.running:
            if not self.packet_queue.empty():
                packet = self.packet_queue.get()
                self.process_packet(packet)
