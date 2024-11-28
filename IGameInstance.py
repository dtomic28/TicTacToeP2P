from abc import ABC, abstractmethod
from queue import Queue
from enum import Enum
import socket
import json


class PacketType(Enum):
    PLAYER_TURN = "PLAYER_TURN"
    GAME_STATE = "GAME_STATE"
    GAME_WIN = "GAME_WIN"
    ACKNOWLEDGE = "ACKNOWLEDGE"
    MOVE = "MOVE"
    RESET = "RESET"  # New reset packet type


class IGameInstance(ABC):
    def __init__(self, role, host="localhost", port=11341):
        self.role = role  # "server" or "client"
        self.host = host
        self.port = port
        self.board = [" "] * 9  # Shared game board
        self.packet_queue = Queue()  # Queue for processing packets
        self.running = True
        self.current_player = None  # Tracks whose turn it is
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection = None
        self.gui_callback = None  # Optional callback for GUI updates
        self.id = None
        self.isOver = False

    def set_gui_callback(self, callback):
        self.gui_callback = callback

    @abstractmethod
    def initialize(self):
        pass

    def send_packet(self, packet):

        try:
            # Append newline as a delimiter
            message = json.dumps(packet) + "\n"
            self.connection.sendall(message.encode())
        except Exception as e:
            print(f"Error sending packet: {e}")

    @abstractmethod
    def process_packet(self, packet):
        pass

    def run(self):
        while self.running:
            if not self.packet_queue.empty():
                packet = self.packet_queue.get()
                self.process_packet(packet)

    def check_win(self, player):
        win_positions = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
            [0, 4, 8], [2, 4, 6]              # Diagonals
        ]
        for positions in win_positions:
            # Check if all positions are occupied by the same player and not " "
            if all(self.board[pos] == player for pos in positions) and player != " ":
                return True
        return False

    def stop(self):
        self.running = False
