import random
from IGameInstance import *


class ComputerPlayer(IGameInstance):
    def __init__(self):
        super().__init__("computer")
        self.human_player = "X"
        self.computer_player = "O"

    def initialize(self):
        """
        Start the game and decide who goes first.
        """
        print("Initializing game against the computer...")
        self.current_player = random.choice(
            [self.human_player, self.computer_player])
        print(f"{self.current_player} starts!")

        # If the computer starts, it makes the first move
        if self.current_player == self.computer_player:
            self.make_computer_move()

    def send_packet(self, packet):
        """
        Dummy implementation since no packets are sent in this mode.
        """
        pass

    def send_game_state(self):
        """
        Send the current game state to both the client and the server's own queue.
        """
        packet = {"type": PacketType.GAME_STATE.value, "board": self.board}
        self.send_packet(packet)
        self.packet_queue.put(packet)

    def process_packet(self, packet):
        """
        Process packets for game logic.
        """
        packet_type = packet.get("type")

        if packet_type == PacketType.PLAYER_TURN.value:
            if packet.get("player") == self.human_player:
                self.play_turn()
            elif packet.get("player") == self.computer_player:
                self.make_computer_move()

        elif packet_type == PacketType.MOVE.value:
            player = packet.get("player")
            move = packet.get("move")

            if self.board[move] == " ":
                self.board[move] = player
                print(f"Move processed: Player {player} to position {move}")
                self.display_board()

                # Check for win after the move
                if self.check_win(player):
                    print(f"Player {player} wins!")
                    self.running = False
                elif " " not in self.board:
                    # Check for a draw
                    print("The game is a draw!")
                    self.running = False
                else:
                    # Alternate turns
                    self.current_player = (
                        self.human_player
                        if player == self.computer_player
                        else self.computer_player
                    )
                    self.packet_queue.put(
                        {"type": PacketType.PLAYER_TURN.value,
                            "player": self.current_player}
                    )
            else:
                print(f"Invalid move by {player} at position {move} ignored.")

        elif packet_type == PacketType.GAME_WIN.value:
            print(packet.get("result"))
        elif packet_type == PacketType.GAME_STATE.value:
            self.board = packet.get("board")
            print("Updated board:")
            self.display_board()

    def play_turn(self):
        """
        Let the human player make a move.
        """
        move = int(input("Enter your move (0-8): "))
        if self.board[move] == " ":
            # Add the human player's move to the packet queue
            self.packet_queue.put(
                {"type": PacketType.MOVE.value,
                    "player": self.human_player, "move": move}
            )
        else:
            print("Invalid move. Try again.")
            self.play_turn()

    def make_computer_move(self):
        """
        Let the computer make a move.
        """
        print("Computer's turn...")
        # Simple AI: Choose the first available space
        for i in range(len(self.board)):
            if self.board[i] == " ":
                # Add the computer's move to the packet queue
                self.packet_queue.put(
                    {"type": PacketType.MOVE.value,
                        "player": self.computer_player, "move": i}
                )
                return
        print("No moves available! Game over.")
        self.running = False

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
            if all(self.board[pos] == player for pos in positions):
                return True
        return False

    def display_board(self):
        """
        Display the current board in a user-friendly format.
        """
        print("\nCurrent Board:")
        for i in range(0, 9, 3):
            print(f"{self.board[i]} | {self.board[i+1]} | {self.board[i+2]}")
            if i < 6:
                print("--+---+--")
        print()

    def run_game(self):
        """
        Continuously process packets from the queue.
        """
        while self.running:
            if not self.packet_queue.empty():
                packet = self.packet_queue.get()
                self.process_packet(packet)
