import socket
import json
from threading import Thread
from IGameInstance import *


class Client(IGameInstance):
    def __init__(self, host="localhost"):
        super().__init__("client", host)
        self.id = "X"

    def initialize(self):
        print("Connecting to server...")
        self.socket.connect((self.host, self.port))
        self.connection = self.socket
        print("Connected to server.")

    def send_packet(self, packet):
        """
        Send a packet to the client.
        """
        try:
            # Append newline as a delimiter
            message = json.dumps(packet) + "\n"
            self.connection.sendall(message.encode())
        except Exception as e:
            print(f"Error sending packet: {e}")

    def process_packet(self, packet):
        """
        Handle packets received from the server.
        """
        packet_type = packet.get("type")

        if packet_type == PacketType.PLAYER_TURN.value:
            self.current_player = packet.get("player")
            print(f"It's {self.current_player}'s turn!")
            if self.gui_callback:
                self.gui_callback(
                    {"type": "TURN", "player": self.current_player})

        elif packet_type == PacketType.GAME_STATE.value:
            self.board = packet.get("board")
            print("Updated board:", self.board)
            if self.gui_callback:
                self.gui_callback({"type": "BOARD", "board": self.board})

        elif packet_type == PacketType.GAME_WIN.value:
            result = packet.get("result")
            print(result)
            if self.gui_callback:
                self.gui_callback({"type": "END", "result": result})

        elif packet_type == PacketType.RESET.value:
            print("Game reset requested by the server.")
            self.reset_game()  # Call the reset logic

    def reset_game(self):
        """
        Reset the game state for the client.
        """
        self.board = [" "] * 9  # Clear the board
        self.current_player = None  # Reset the current player
        self.packet_queue.queue.clear()  # Clear any pending packets

        # Notify the GUI (if applicable) to reset
        if self.gui_callback:
            self.gui_callback({"type": "RESET"})

    def play_turn(self, index):
        """
        Handle the client's turn and send the move to the server.
        Args:
            index (int): The board position for the move (0-8).
        """
        if self.board[index] == " ":
            # Send the MOVE packet to the server
            self.send_packet(
                {"type": PacketType.MOVE.value, "player": self.id, "move": index}
            )
        else:
            print("Invalid move. This spot is already taken.")

    def run_game(self):
        """
        Continuously process packets from the queue.
        """
        while self.running:
            if not self.packet_queue.empty():
                packet = self.packet_queue.get()
                self.process_packet(packet)
