#!/usr/bin/env python3
"""
Fixed Tkinter chat client.

Usage:
    python chat_client.py HOST [-p PORT]
"""
import threading
import socket
import argparse
import tkinter as tk
from tkinter import simpledialog
import json
from datetime import datetime

DEFAULT_PORT = 1060
PLACEHOLDER = "Write your message here."


class Receive(threading.Thread):
    def __init__(self, sock, window, messages_widget):
        super().__init__(daemon=True)
        self.sock = sock
        self.window = window
        self.messages = messages_widget
        self._running = True

    def stop(self):
        self._running = False
        try:
            # Interrupt blocking recv
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

    def run(self):
        buffer = ""
        while self._running:
            try:
                data = self.sock.recv(1024)
                if not data:
                    self._safe_insert("Server disconnected")
                    break

                buffer += data.decode("utf-8", errors="ignore")

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()

                    if not line.startswith("{"):
                        self._safe_insert(line, "system")
                        continue

                    try:
                        msg = json.loads(line)
                        # Validate expected keys
                        time_str = msg.get("time", "")
                        user = msg.get("user", "Unknown")
                        text = msg.get("text", "")
                        display = f"[{time_str}] {user}: {text}"
                        self._safe_insert(display)
                    except json.JSONDecodeError as e:
                        print("CLIENT JSON error:", e)
                        continue

            except (OSError, ConnectionResetError):
                self._safe_insert("Receiver error.")
                break

    def _safe_insert(self, msg, tag="chat"):
        if self.window.winfo_exists():
            def insert_msg():
                self.messages.config(state ="normal")
                self.messages.insert(tk.END, msg + "\n", tag)
                self.messages.yview(tk.END)
                self.messages.config(state ="disabled")
            self.window.after(0, insert_msg)

class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.name = "Anonymous"
        self.receive_thread = None
        # UI references (set by main)
        self.window = None
        self.messages = None
        self.entry_widget = None
        self.send_button = None
        self._closed = False

    def connect(self):
        # Apply a short temporary timeout for connect, then restore original
        self.sock.settimeout(5)
        self.sock.connect((self.host, self.port))
        self.sock.settimeout(None)

    def start_receive(self, window, messages_widget):
        self.receive_thread = Receive(self.sock, window, messages_widget)
        self.receive_thread.start()

    def send(self, text_input):
        if self._closed:
            return

        message = text_input.get().strip()
        if not message or message == PLACEHOLDER:
            return

        # clear input immediately
        text_input.delete(0, tk.END)

        if message.upper() == "QUIT":
            try:
                quit_msg = {
                    "type": "system",
                    "user": self.name,
                    "text": f"{self.name} has left the chat.",
                    "time": datetime.now().strftime("%H:%M"),
                }
                self.sock.sendall((json.dumps(quit_msg) + "\n").encode("utf-8"))
            except OSError:
                self.close()
        else:
            try:
                chat_msg = {
                    "type": "chat",
                    "user": self.name,
                    "text": message,
                    "time": datetime.now().strftime("%H:%M"),
                }
                self.sock.sendall((json.dumps(chat_msg) + "\n").encode("utf-8"))
            except OSError:
                self.close()

    def send_join(self):
        try:
            msg = {
                "type": "system",
                "user": self.name,
                "text": f"{self.name} has joined the chat.",
                "time": datetime.now().strftime("%H:%M"),
            }
            self.sock.sendall((json.dumps(msg) + "\n").encode("utf-8"))
        except OSError:
            pass

    def close(self):
        if self._closed:
            return
        self._closed = True
        try:
            if self.receive_thread:
                self.receive_thread.stop()
                # give thread a moment to exit
                self.receive_thread.join(timeout=1.0)
        except RuntimeError:
            pass
        try:
            self.sock.close()
        except OSError:
            pass


def main(host, port):
    window = tk.Tk()
    window.title("ChatRoom")
    window.geometry("600x450")

    header = tk.Label(window, text="💬 ChatRoom", font=("Helvetica", 16, "bold"))
    header.pack(side=tk.TOP, fill=tk.X, pady=5)

    # Messages area (Text + Scrollbar)
    frame_messages = tk.Frame(window)
    text_area = tk.Text(frame_messages, wrap="word", state="disabled",
                        bg="#f9f9f9", font=("Arial", 11))
    scrollbar = tk.Scrollbar(frame_messages, command=text_area.yview)
    text_area.configure(yscrollcommand=scrollbar.set)
    text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    frame_messages.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    text_area.tag_configure("chat", foreground="#222")
    text_area.tag_configure("system", foreground="#666", font=("Arial", 11, "italic"))

    # Entry + Send button
    frame_entry = tk.Frame(window)
    text_input = tk.Entry(frame_entry, font=("Arial", 11))
    text_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
    btn_send = tk.Button(frame_entry, text="Send")
    btn_send.pack(side=tk.RIGHT)
    frame_entry.pack(fill=tk.X, padx=10, pady=10)

    # Example welcome message
    text_area.config(state="normal")
    text_area.insert(tk.END, "Welcome! Type your message below...\n", "system")
    text_area.config(state="disabled")

    # client setup
    client = Client(host, port)
    client.window = window
    client.messages = text_area   # use Text widget now
    client.entry_widget = text_input
    client.send_button = btn_send

    # ... rest of your setup unchanged ...
   

    try:
        client.connect()
    except Exception as e:
        text_area.insert(tk.END, f"Failed to connect: {e}\n", "system")
        # disable UI so user can't attempt to send
        text_input.config(state=tk.DISABLED)
        btn_send.config(state=tk.DISABLED)
        window.mainloop()
        return

    # ask for name
    try:
        name = simpledialog.askstring("Your Name", "Enter your name:", parent=window) 
        client.name = name if name else "Anonymous"
        
    except tk.TclError:
        client.name = "Anonymous"
 
    text_area.config(state="normal")
    text_area.insert(tk.END, f"Welcome, {client.name}! Type your message and press Enter or click Send.\n", "system")
    text_area.config(state="disabled")
    
    client.start_receive(window, text_area)

    # announce join
    window.after(200, client.send_join)

    # Entry behavior and bindings for placeholder
    def _clear_placeholder(event):
        try:
            if text_input.get() == PLACEHOLDER:
                text_input.delete(0, tk.END)
        except tk.TclError:
            pass

    def _restore_placeholder(event):
        try:
            if not text_input.get().strip():
                text_input.insert(0, PLACEHOLDER)
        except tk.TclError:
            pass

    text_input.bind("<FocusIn>", _clear_placeholder)
    text_input.bind("<FocusOut>", _restore_placeholder)
    text_input.bind("<Return>", lambda e: client.send(text_input))
    text_input.insert(0, PLACEHOLDER)

    # wire send button
    btn_send.config(command=lambda: client.send(text_input))

    def on_close():
        # ensure client is closed and thread joined before destroying window
        client.close()
        try:
            window.destroy()
        except tk.TclError:
            pass

    window.protocol("WM_DELETE_WINDOW", on_close)
    window.mainloop()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Chatroom client")
    parser.add_argument('host', nargs='?', default='localhost',
                        help='server hostname or IP to connect to (default: localhost)')
    parser.add_argument('-p', metavar='PORT', type=int, default=DEFAULT_PORT,
                        help='TCP port (default 1060)')
    args = parser.parse_args()
    main(args.host, args.p)