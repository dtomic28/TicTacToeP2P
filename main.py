from threading import Thread
from server import Server
from client import Client
from ComputerPlayer import ComputerPlayer
from EventHandler import EventHandler


def main():
    try:
        role = input("Enter role (server/client/computer): ").strip().lower()
        game_instance = None
        event_handler = None
        game_thread = None
        event_handler_thread = None

        if role == "server":
            game_instance = Server()
        elif role == "client":
            game_instance = Client()
        elif role == "computer":
            game_instance = ComputerPlayer()
        else:
            print("Invalid role.")
            return

        # Initialize and start the game instance
        game_instance.initialize()
        game_thread = Thread(target=game_instance.run_game)
        game_thread.start()

        if role != "computer":
            # Create and start the event handler for server or client mode
            event_handler = EventHandler(
                game_instance.connection, game_instance)
            event_handler_thread = Thread(target=event_handler.receive_packets)
            event_handler_thread.start()

        print("Game started. Main thread can later initialize GUI.")

        while True:
            pass

    except KeyboardInterrupt:
        print("\nCtrl-C detected! Stopping all threads...")

        # Stop the game instance
        if game_instance:
            game_instance.running = False

        # Stop the event handler if it's running
        if event_handler:
            event_handler.running = False

        # Wait for threads to finish
        if game_thread:
            game_thread.join()
        if event_handler_thread:
            event_handler_thread.join()

        print("Game stopped. Goodbye!")


if __name__ == "__main__":
    main()
