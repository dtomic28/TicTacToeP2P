import tkinter as tk
from tkinter import messagebox
from threading import Thread
from server import Server
from client import Client
from ComputerPlayer import ComputerPlayer
from EventHandler import EventHandler


class TicTacToeGUI:
    def __init__(self, root):
        """
        Initialize the GUI with the root window.
        Args:
            root (tk.Tk): The root window.
        """
        self.root = root
        self.root.title("Tic Tac Toe")
        self.game_instance = None
        self.event_handler = None
        self.running = True
        self.turn_label = None  # Label for displaying current player's turn
        self.buttons = []  # Button references for the 3x3 board
        self.reset_button = None  # Reset button reference

        # Display the role selection window
        self.create_role_selection_window()

    def create_role_selection_window(self):
        """
        Create the role selection window.
        """
        tk.Label(self.root, text="Tic Tac Toe",
                 font=("Arial", 20)).pack(pady=20)

        roles = [
            ("Server", self.start_server),
            ("Client", self.start_client),
            ("Computer", self.start_computer)
        ]

        for role, command in roles:
            tk.Button(self.root, text=role, command=command,
                      font=("Arial", 14)).pack(pady=10)

    def cleanup_window(self):
        """
        Destroy all widgets in the current window.
        """
        for widget in self.root.winfo_children():
            widget.destroy()

    def start_server(self):
        """
        Start the game in server mode.
        """
        self.cleanup_window()
        self.initialize_game_window("server")

    def start_client(self):
        """
        Start the game in client mode.
        """
        self.cleanup_window()
        self.initialize_game_window("client")

    def start_computer(self):
        """
        Start the game in computer mode.
        """
        self.cleanup_window()
        self.initialize_game_window("computer")

    def initialize_game_window(self, role):
        """
        Initialize the game window based on the selected role.
        """
        self.root.title(f"Tic Tac Toe - {role.capitalize()} Mode")

        # Create the game board
        self.create_game_board()

        if role == "server":
            self.game_instance = Server()
            self.game_instance.set_gui_callback(
                self.update_gui)  # Bind GUI callback
            self.game_instance.initialize()
            self.event_handler = EventHandler(
                self.game_instance.connection, self.game_instance)
            Thread(target=self.event_handler.receive_packets, daemon=True).start()

        elif role == "client":
            self.game_instance = Client()
            self.game_instance.set_gui_callback(
                self.update_gui)  # Bind GUI callback
            self.game_instance.initialize()
            self.event_handler = EventHandler(
                self.game_instance.connection, self.game_instance)
            Thread(target=self.event_handler.receive_packets, daemon=True).start()

        elif role == "computer":
            self.game_instance = ComputerPlayer()
            self.game_instance.set_gui_callback(
                self.update_gui)  # Bind GUI callback
            self.game_instance.initialize()

        # Start the game instance logic
        Thread(target=self.game_instance.run_game, daemon=True).start()

    def create_game_board(self):
        """
        Create the 3x3 grid for the game board and a turn indicator.
        """
        self.turn_label = tk.Label(
            self.root, text="Waiting for turn...", font=("Arial", 16))
        self.turn_label.pack(pady=10)

        grid_frame = tk.Frame(self.root)
        grid_frame.pack(pady=20)

        for row in range(3):
            for col in range(3):
                index = row * 3 + col
                button = tk.Button(grid_frame, text=" ", font=("Arial", 24), width=5, height=2,
                                   command=lambda i=index: self.make_move(i))
                button.grid(row=row, column=col)
                self.buttons.append(button)

        # Add reset button (only enabled at endgame)
        self.reset_button = tk.Button(self.root, text="Reset", command=self.reset_game,
                                      font=("Arial", 14), state=tk.DISABLED)
        self.reset_button.pack(pady=10)

        close_button = tk.Button(
            self.root, text="Close", command=self.close_game, font=("Arial", 14))
        close_button.pack(pady=10)

    def make_move(self, index):
        """
        Handle button press for making a move.
        """
        if self.game_instance.current_player == self.game_instance.id:  # Check if it's the client's turn
            # Delegate the move to the game instance
            self.game_instance.play_turn(index)
        else:
            messagebox.showerror("Invalid Move", "It's not your turn!")

    def update_gui(self, update):
        """
        Handle updates from the game instance.
        Args:
            update (dict): An update packet from the game instance.
        """
        if update["type"] == "BOARD":
            # Update the board buttons based on the game instance's board
            for i, value in enumerate(self.game_instance.board):
                self.buttons[i].config(text=value)

        elif update["type"] == "TURN":
            # Update the turn label
            current_player = update["player"]
            self.turn_label.config(text=f"It's {current_player}'s turn!")

        elif update["type"] == "END":
            # Display endgame modal and enable reset button
            result = update["result"]
            self.show_endgame_modal(result)
            # Enable the reset button
            self.reset_button.config(state=tk.NORMAL)

        elif update["type"] == "RESET":
            # Reset the GUI
            self.reset_gui()

    def show_endgame_modal(self, message):
        """
        Display a modal when the game ends.
        Args:
            message (str): The endgame message (e.g., "You win!" or "Draw!").
        """
        messagebox.showinfo("Game Over", message)

    def reset_game(self):
        """
        Reset the game state. Only available at endgame.
        """
        if isinstance(self.game_instance, Server):
            self.game_instance.reset_game()  # Only the server can initiate a reset
        else:
            messagebox.showerror(
                "Error", "Only the server can reset the game.")

    def reset_gui(self):
        """
        Reset the GUI elements for a new game.
        """
        for button in self.buttons:
            button.config(text=" ")  # Clear button text
        self.turn_label.config(text="Waiting for turn...")
        self.reset_button.config(state=tk.DISABLED)  # Disable the reset button

    def close_game(self):
        """
        Close the game and stop all threads.
        """
        self.running = False
        self.game_instance.running = False
        if self.event_handler:
            self.event_handler.running = False
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = TicTacToeGUI(root)
    root.mainloop()
