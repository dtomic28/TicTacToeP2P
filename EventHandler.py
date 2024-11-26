import json
from threading import Thread


class EventHandler:
    def __init__(self, connection, game_instance):
        self.connection = connection  # The socket connection
        self.game_instance = game_instance  # Reference to the IGameInstance
        self.running = True

    def receive_packets(self):
        """
        Continuously receive packets from the socket and add them to the game instance's queue.
        """
        while self.running:
            try:
                data = self.connection.recv(1024).decode()
                if data:
                    packet = json.loads(data)
                    # Add the packet to the IGameInstance queue
                    self.game_instance.packet_queue.put(packet)
            except Exception as e:
                print(f"Error receiving packets: {e}")
                self.running = False

    def start(self):
        """
        Run the receive_packets method in a separate thread.
        """
        thread = Thread(target=self.receive_packets)
        thread.start()
