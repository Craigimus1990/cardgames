import websockets
from euchre.setup import EuchreSetup
from core.net import Connection
from core.state import Player

if __name__ == "__main__":
    setup = EuchreSetup()

    # Create a websocket server
    server = websockets.serve(setup.handle_connection, "localhost", 8000)

    # Create players
    player_1 = Player("Me")
    player_2 = Player("Cpu 1")
    player_3 = Player("Cpu 2")
    player_4 = Player("Cpu 3")

    # Create connections
    connection_1 = Connection(server, player_1)
    connection_2 = Connection(server, player_2)
    connection_3 = Connection(server, player_3)
    connection_4 = Connection(server, player_4)

    # Add connections to setup
    setup.add_player(1, connection_1, player_1)
    setup.add_player(2, connection_2, player_2)
    setup.add_player(3, connection_3, player_3)
    setup.add_player(4, connection_4, player_4)
