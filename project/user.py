"""import socketio
from datetime import datetime

sio = socketio.Client()
username = None

@sio.event
def connect():
    print("connected to server")
    sio.emit("join", {"user": username })
    
@sio.event
def disconnect():
    print("disconnected from server")
    
@sio.on("message")
def on_message(data):
    msg_type = data.get("type","chat")
    if msg_type == "private":
        if data.get("to") == username :
            print(f"[{data['time']}], {data['user']} -> YOU: [PRIVATE] {data['text']}")
        elif data.get("user") == username:
            print(f"[{data['time']}] YOU -> {data['to']}: [PRIVATE] {data['text']}")
    else:
        print(f"[{data['time']}] {data['user']}: {data['text']}")
    
def main():
    global username
    username = input("Enter your username :") or "Anonymous"
    
    sio.connect("http://localhost:5050")
    try:
        while True:
            text = input('message:')
            if text.upper() == "QUIT":
                sio.emit("quit", {"user": username})
                break
            elif text.startswith("@"):
                try:
                    recipient, msg = text[1:].split(" ", 1)
                    sio.emit("private_msg", {"user": username, "to": recipient, "text":msg})
                except ValueError:
                    print("usage: @recipient message")
            else:
                sio.emit("chat", {"user": username, "text":text})
    finally:
        sio.disconnect()
        
if __name__ == "__main__":
    main()"""