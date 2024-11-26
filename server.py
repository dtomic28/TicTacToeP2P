import socket
import random
import json
from threading import Thread
from IGameInstance import *
from copy import deepcopy


class Server(IGameInstance):
    def __init__(self, host="localhost"):
        super().__init__("server", host)
        self.id = "O"

    def initialize(self):
        print("Starting server...")
        self.socket.bind((self.host, self.port))
        self.socket.listen(1)
        self.connection, _ = self.socket.accept()
        print("Client connected.")
        self.decide_first_player()

    def decide_first_player(self):
        """
        Randomly decide who starts the game and send the appropriate packet.
        """
        self.current_player = random.choice(
            ["X", "O"])  # Decide the first player
        print(f"{self.current_player} starts!")

        # Notify the client about the starting player
        self.send_packet({"type": PacketType.PLAYER_TURN.value,
                          "player": self.current_player})

        # Update the server's own queue for GUI sync
        self.packet_queue.put(
            {"type": PacketType.PLAYER_TURN.value, "player": self.current_player})

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

    def check_win(self, player):
        """
        Check if the given player has won the game.

        Args:
            player (str): The player to check for ("X" or "O").

        Returns:
            bool: True if the player has won, False otherwise.
        """
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

    def process_packet(self, packet):
        """
        Handle packets received from the client or generated locally.
        """
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
                    self.running = False
                elif " " not in self.board:
                    # If no spaces left, it's a draw
                    result = {"type": PacketType.GAME_WIN.value,
                              "result": "The game is a draw!"}
                    self.send_packet(result)
                    self.packet_queue.put(result)
                    self.running = False
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
            if self.gui_callback:
                self.gui_callback(
                    {"type": "TURN", "player": self.current_player})

        elif packet_type == PacketType.GAME_STATE.value:
            self.board = packet.get("board")
            print("Updated board:", self.board)
            if self.gui_callback:
                self.gui_callback({"type": "BOARD", "board": self.board})

    def send_game_state(self):
        """
        Send the current game state to both the client and the server's own queue.
        """
        packet = {"type": PacketType.GAME_STATE.value, "board": self.board}
        self.send_packet(packet)
        self.packet_queue.put(deepcopy(packet))

    def play_turn(self, index=None):
        """
        Add a MOVE packet to the server's own queue for processing.
        """
        if index is not None and self.board[index] == " ":
            self.packet_queue.put(
                {"type": "MOVE", "player": self.id, "move": index})
        else:
            print("Invalid move.")

    def run_game(self):
        """
        Continuously process packets from the queue.
        """
        while self.running:
            if not self.packet_queue.empty():
                packet = self.packet_queue.get()
                self.process_packet(packet)
