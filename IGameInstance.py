from abc import ABC, abstractmethod
from queue import Queue
from enum import Enum
import socket


class PacketType(Enum):
    PLAYER_TURN = "PLAYER_TURN"
    GAME_STATE = "GAME_STATE"
    GAME_WIN = "GAME_WIN"
    ACKNOWLEDGE = "ACKNOWLEDGE"
    MOVE = "MOVE"
    RESET = "RESET"  # New reset packet type


class IGameInstance(ABC):
    def __init__(self, role, host="localhost", port=11342):
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

    def set_gui_callback(self, callback):
        """
        Set the callback function for GUI updates.
        """
        self.gui_callback = callback

    @abstractmethod
    def initialize(self):
        """Initialize the instance (connect or start listening)."""
        pass

    @abstractmethod
    def send_packet(self, packet):
        """Send a packet to the peer."""
        pass

    @abstractmethod
    def process_packet(self, packet):
        """Process a received packet."""
        pass

    def run(self):
        """Continuously process packets from the queue."""
        while self.running:
            if not self.packet_queue.empty():
                packet = self.packet_queue.get()
                self.process_packet(packet)
