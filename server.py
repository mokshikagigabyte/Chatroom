"""""
import threading
import socket
import argparse
import sys
import json


class Server(threading.Thread):
    def __init__(self, host, port):
        super().__init__(daemon=True)
        self.connections = []
        self.lock = threading.Lock()
        self.host = host
        self.port = port
        self.sock = None
        self._running = True

    def run(self):
        print("Server running...")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen(5)
        print("Listening at", self.sock.getsockname())

        while self._running:
            try:
                sc, sockname = self.sock.accept()
            except OSError:
                # Socket closed during stop()
                break

            try:
                peer = sc.getpeername()
                local = sc.getsockname()
                print(f"Accepted a new connection from {peer} to {local}")
            except OSError:
                print("Accepted connection (peer info unavailable)")

            client = ServerSocket(sc, sockname, self)
            with self.lock:
                self.connections.append(client)
            client.start()

        print("Server accept loop ended.")

    def broadcast(self, message, source):
        with self.lock:
            for connection in list(self.connections):
                    try:
                        connection.send(message)
                    except OSError:
                        connection.cleanup()

    def remove_connection(self, connection):
        with self.lock:
            if connection in self.connections:
                self.connections.remove(connection)

    def stop(self):
        self._running = False
        # Close listening socket to unblock accept()
        try:
            if self.sock:
                self.sock.close()
        except OSError:
            pass

        # Cleanup all client connections
        with self.lock:
            for conn in list(self.connections):
                conn.cleanup()





def exit_thread(server):
    while True:
        cmd = input().strip().lower()
        if cmd == "q":
            print("Shutting down server...")
            server.stop()
            # Wait briefly for server thread to end
            server.join(timeout=2.0)
            sys.exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Chatroom server")
    parser.add_argument('host', help='interface the server listens at')
    parser.add_argument('-p', metavar='PORT', type=int, default=1060, help='TCP port (default 1060)')

    args = parser.parse_args()

    # create and start server thread
    server_instance = Server(args.host, args.p)
    server_instance.start()

    # start exit thread (type 'q' + Enter to shutdown)
    exit_t = threading.Thread(target=exit_thread, args=(server_instance,), daemon=True)
    exit_t.start()

    # Keep the main thread alive so daemon threads can run
    try:
        server_instance.join()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Stopping server...")
        server_instance.stop()
        server_instance.join(timeout=2.0)"""