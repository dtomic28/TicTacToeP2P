import socket
import random
import json
from threading import Thread
from IGameInstance import *
from copy import deepcopy
from json_utils import *


class Server(IGameInstance):
    def __init__(self, host="localhost", port="12345"):
        super().__init__("server", host, port)
        self.id = "O"

    def initialize(self):
        print("Starting server...")
        self.socket.bind((self.host, self.port))
        self.socket.listen(1)
        self.connection, _ = self.socket.accept()
        print("Client connected.")
        self.decide_first_player()

    def decide_first_player(self):
        self.current_player = random.choice(
            ["X", "O"])  # Decide the first player
        print(f"{self.current_player} starts!")

        # Notify the client about the starting player
        self.send_packet(createPlayerTurnPacket(self.current_player))

        # Update the server's own queue for GUI sync
        self.packet_queue.put(
            createPlayerTurnPacket(self.current_player))

    def reset_game(self):
        self.board = [" "] * 9  # Clear the board
        self.current_player = None  # Reset the current player
        self.packet_queue.queue.clear()  # Clear any pending packets
        self.send_packet({"type": PacketType.RESET.value})
        self.isOver = False  # Reset game over flag
        self.decide_first_player()

    def process_packet(self, packet):
        packet_type = packet.get("type")

        if packet_type == PacketType.MOVE.value:
            player = packet.get("player")
            move = packet.get("move")

            # Only process valid moves
            if self.board[move] == " ":
                self.board[move] = player
                print(f"Move processed: Player {player} to position {move}")

                # Send updated game state to the client
                self.send_game_state()

                # Check for win
                if self.check_win(player):
                    result = {"type": PacketType.GAME_WIN.value,
                              "result": f"Player {player} wins!"}
                    self.send_packet(result)
                    self.packet_queue.put(result)
                    self.isOver = True
                elif " " not in self.board:
                    # If no spaces left, it's a draw
                    result = {"type": PacketType.GAME_WIN.value,
                              "result": "The game is a draw!"}
                    self.send_packet(result)
                    self.packet_queue.put(result)
                    self.isOver = True
                else:
                    # Alternate turn
                    self.current_player = "O" if player == "X" else "X"
                    self.send_packet(
                        {"type": PacketType.PLAYER_TURN.value,
                            "player": self.current_player}
                    )
                    self.packet_queue.put(
                        {"type": PacketType.PLAYER_TURN.value,
                            "player": self.current_player}
                    )
            else:
                print(f"Invalid move by {player} at position {move} ignored.")

        elif packet_type == PacketType.PLAYER_TURN.value:
            self.current_player = packet.get("player")
            print(f"It's {self.current_player}'s turn!")

        elif packet_type == PacketType.GAME_STATE.value:
            self.board = packet.get("board")
            print("Updated board:", self.board)

        elif packet_type == PacketType.GAME_WIN.value:
            result = packet.get("result")
            self.gui_callback(
                {"type": "END", "result": result})

    def send_game_state(self):
        packet = {"type": PacketType.GAME_STATE.value, "board": self.board}
        self.send_packet(packet)
        self.packet_queue.put(deepcopy(packet))

    def play_turn(self, index=None):
        if index is not None and self.board[index] == " ":
            self.packet_queue.put(
                {"type": "MOVE", "player": self.id, "move": index})
        else:
            print("Invalid move.")

    def run_game(self):
        while self.running:
            if not self.packet_queue.empty():
                packet = self.packet_queue.get()
                self.process_packet(packet)
