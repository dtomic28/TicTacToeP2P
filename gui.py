import tkinter as tk
from tkinter import messagebox
from threading import Thread
from server import Server
from client import Client
from ComputerPlayer import ComputerPlayer
from EventHandler import EventHandler


class TicTacToeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Tic Tac Toe")
        self.game_instance = None
        self.event_handler = None
        self.running = True
        self.turn_label = None  # Label for displaying the current player's turn
        self.buttons = []  # Button references for the 3x3 board
        self.reset_button = None  # Reset button reference
        self.ip_entry = None
        self.port_entry = None

        self.create_role_selection_window()

    def create_role_selection_window(self):
        self.cleanup_window()

        tk.Label(self.root, text="Tic Tac Toe",
                 font=("Arial", 20)).pack(pady=20)

        # IP address input
        tk.Label(self.root, text="IP Address:", font=("Arial", 12)).pack()
        self.ip_entry = tk.Entry(self.root, font=("Arial", 12))
        self.ip_entry.pack(pady=5)
        self.ip_entry.insert(0, "127.0.0.1")  # Default IP

        # Port input
        tk.Label(self.root, text="Port:", font=("Arial", 12)).pack()
        self.port_entry = tk.Entry(self.root, font=("Arial", 12))
        self.port_entry.pack(pady=5)
        self.port_entry.insert(0, "12345")  # Default Port

        # Role selection buttons
        roles = [
            ("Server", self.start_server),
            ("Client", self.start_client),
            ("Computer", self.start_computer),
        ]

        for role, command in roles:
            tk.Button(self.root, text=role, command=command,
                      font=("Arial", 14)).pack(pady=10)

    def cleanup_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def get_ip_and_port(self):
        ip = self.ip_entry.get()
        try:
            port = int(self.port_entry.get())
        except ValueError:
            messagebox.showerror(
                "Invalid Port", "Port must be a valid integer.")
            return None, None
        return ip, port

    def start_server(self):
        ip, port = self.get_ip_and_port()
        if ip is None or port is None:
            return  # Invalid IP or port

        self.cleanup_window()
        self.initialize_game_window("server", ip, port)

    def start_client(self):
        ip, port = self.get_ip_and_port()
        if ip is None or port is None:
            return  # Invalid IP or port

        self.cleanup_window()
        self.initialize_game_window("client", ip, port)

    def start_computer(self):
        self.cleanup_window()
        self.initialize_game_window("computer")

    def initialize_game_window(self, role, ip=None, port=None):
        self.cleanup_window()
        self.root.title(f"Tic Tac Toe - {role.capitalize()} Mode")

        # Create the game board
        self.create_game_board()

        if role == "server":
            self.game_instance = Server(host=ip, port=port)
            self.game_instance.set_gui_callback(
                self.update_gui)  # Set the GUI callback
            self.game_instance.initialize()
            self.event_handler = EventHandler(
                self.game_instance.connection, self.game_instance)
            Thread(target=self.event_handler.receive_packets, daemon=True).start()

        elif role == "client":
            self.game_instance = Client(host=ip, port=port)
            self.game_instance.set_gui_callback(
                self.update_gui)  # Set the GUI callback
            self.game_instance.initialize()
            self.event_handler = EventHandler(
                self.game_instance.connection, self.game_instance)
            Thread(target=self.event_handler.receive_packets, daemon=True).start()

        elif role == "computer":
            self.game_instance = ComputerPlayer()
            self.game_instance.set_gui_callback(
                self.update_gui)  # Set the GUI callback
            self.game_instance.initialize()

        # Start the game instance logic
        Thread(target=self.game_instance.run_game, daemon=True).start()

        # Start polling for GUI updates
        self.refresh_gui()

    def create_game_board(self):
        self.turn_label = tk.Label(
            self.root, text="Waiting for turn...", font=("Arial", 16))
        self.turn_label.pack(pady=10)

        grid_frame = tk.Frame(self.root)
        grid_frame.pack(pady=20)

        for row in range(3):
            for col in range(3):
                index = row * 3 + col
                button = tk.Button(
                    grid_frame,
                    text=" ",
                    font=("Arial", 24),
                    width=5,
                    height=2,
                    command=lambda i=index: self.make_move(i),
                )
                button.grid(row=row, column=col)
                self.buttons.append(button)

        self.reset_button = tk.Button(
            self.root,
            text="Reset",
            command=self.reset_game,
            font=("Arial", 14),
            state=tk.DISABLED,
        )
        self.reset_button.pack(pady=10)

        tk.Button(self.root, text="Close", command=self.close_game,
                  font=("Arial", 14)).pack(pady=10)

    def make_move(self, index):
        if self.game_instance.current_player == self.game_instance.id:  # Check if it's the player's turn
            self.game_instance.play_turn(index)
        else:
            messagebox.showerror("Invalid Move", "It's not your turn!")

    def check_connection(self):
        if isinstance(self.game_instance, (Server, Client)):
            return self.game_instance.connection is not None
        return True  # For computer mode, no connection is used

    def handle_disconnection(self):
        messagebox.showerror(
            "Connection Lost", "The connection was closed unexpectedly.")
        self.close_game()  # Gracefully close the game

    def refresh_gui(self):
        # Check if the connection is still active
        if not self.check_connection():
            self.handle_disconnection()
            return

        # Update the board buttons
        for i, value in enumerate(self.game_instance.board):
            self.buttons[i].config(text=value)

        # Update the turn label
        self.turn_label.config(
            text=f"It's {self.game_instance.current_player}'s turn!")

        # Enable or disable the reset button based on the game state
        if not self.game_instance.running:
            self.reset_button.config(state=tk.NORMAL)

        if self.running:
            self.root.after(100, self.refresh_gui)  # Schedule the next refresh

    def update_gui(self, update):
        if update["type"] == "END":
            self.root.after(
                0, lambda: self.show_endgame_modal(update["result"]))
            self.reset_button.config(state=tk.NORMAL)
        elif update["type"] == "RESET":
            self.reset_gui()

    def show_endgame_modal(self, message):
        messagebox.showinfo("Game Over", message)

    def reset_gui(self):
        for button in self.buttons:
            button.config(text=" ")  # Clear button text
        self.turn_label.config(text="Waiting for turn...")
        self.reset_button.config(state=tk.DISABLED)  # Disable the reset button

    def reset_game(self):
        if isinstance(self.game_instance, Server) or isinstance(self.game_instance, ComputerPlayer):
            self.game_instance.reset_game()
        else:
            messagebox.showerror(
                "Error", "Only the server or computer mode can reset the game."
            )

    def close_game(self):
        if self.event_handler:
            self.event_handler.stop()
        self.game_instance.stop()
        self.running = False
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = TicTacToeGUI(root)
    root.mainloop()
