import json
from threading import Thread


class EventHandler:
    def __init__(self, connection, game_instance):
        self.connection = connection  # The socket connection
        self.game_instance = game_instance  # Reference to the IGameInstance
        self.running = True

    def receive_packets(self):
        buffer = ""
        while self.running:
            try:
                data = self.connection.recv(
                    1024).decode()  # Read incoming data
                if data:
                    buffer += data
                    while "\n" in buffer:
                        packet_data, buffer = buffer.split("\n", 1)
                        try:
                            packet = json.loads(packet_data)
                            self.game_instance.packet_queue.put(packet)
                        except json.JSONDecodeError as e:
                            print(f"Error decoding packet: {e}")
            except (ConnectionResetError, OSError):
                print("Connection lost.")
                self.connection = None
                self.running = False
                break

    def start(self):
        thread = Thread(target=self.receive_packets)
        thread.start()

    def stop(self):
        self.running = False
