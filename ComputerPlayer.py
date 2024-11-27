import random
from IGameInstance import *


class ComputerPlayer(IGameInstance):
    def __init__(self):
        super().__init__("computer")
        self.id = "X"
        self.computer_player = "O"

    def send_packet(self, packet):
        return

    def initialize(self):
        print("Initializing game against the computer...")
        self.current_player = random.choice(
            [self.id, self.computer_player])
        print(f"{self.current_player} starts!")

        if self.current_player == self.computer_player:
            self.make_computer_move()

    def reset_game(self):
        self.board = [" "] * 9  # Clear the board
        self.current_player = random.choice(
            [self.id, self.computer_player])
        self.game_over = False  # Reset game over flag
        print("Game has been reset!")
        if (self.gui_callback):
            self.gui_callback({"type": "RESET"})  # Notify GUI of the reset

        if self.current_player == self.computer_player:
            self.make_computer_move()

    def process_packet(self, packet):
        packet_type = packet.get("type")

        if packet_type == PacketType.MOVE.value:
            player = packet.get("player")
            move = packet.get("move")

            if self.board[move] == " ":
                self.board[move] = player
                print(f"Move processed: Player {player} to position {move}")

                if self.check_win(player):
                    result = "You win!" if player == self.id else "Computer wins!"
                    print(result)
                    if (self.gui_callback):
                        self.gui_callback({"type": "END", "result": result})
                    self.isOver = True
                    return

                if " " not in self.board:
                    result = "The game is a draw!"
                    print(result)
                    if (self.gui_callback):
                        self.gui_callback({"type": "END", "result": result})
                    self.isOver = True
                    return

                self.current_player = (
                    self.id if player == self.computer_player else self.computer_player
                )

                if self.current_player == self.computer_player:
                    self.make_computer_move()
            else:
                print(f"Invalid move by {player} at position {move} ignored.")

    def play_turn(self, index):
        if self.board[index] == " ":
            self.packet_queue.put(
                {"type": PacketType.MOVE.value,
                    "player": self.id, "move": index}
            )
        else:
            print("Invalid move. Try again.")

    def make_computer_move(self):
        print("Computer's turn...")
        move = self.find_best_move()
        if move != -1:
            self.packet_queue.put(
                {"type": PacketType.MOVE.value,
                    "player": self.computer_player, "move": move}
            )
        else:
            print("No moves available! Game over.")

    def find_best_move(self):
        for i in range(9):
            if self.board[i] == " ":
                return i
        return -1  # No valid moves

    def check_win(self, player):
        win_positions = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
            [0, 4, 8], [2, 4, 6],             # Diagonals
        ]
        for positions in win_positions:
            if all(self.board[pos] == player for pos in positions):
                return True
        return False

    def run_game(self):
        while self.running:
            if not self.packet_queue.empty():
                packet = self.packet_queue.get()
                self.process_packet(packet)
