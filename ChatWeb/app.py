from flask import Flask, request,jsonify, render_template
from flask_socketio import SocketIO, join_room,leave_room, emit, send
import mysql.connector, bcrypt
from datetime import datetime,timedelta
import secrets


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

users = {}

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="chatuser",
        password="strongpass123!",
        database="chatapp"
    )
    
@app.route("/")
def index():
    return render_template("chat.html")

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data["username"]
    password = data["password"]
    full_name = data.get("full_name")
    age = data.get("age")
    email = data.get("email")
    gender = data.get("gender")
    
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("insert into users (username, password, full_name, age, email,gender) VALUES (%s,%s,%s,%s,%s,%s)", (username,hashed,full_name,age,email,gender))
        conn.commit()   
    except mysql.connector.IntegrityError:
        return jsonify({"success": False, "error": "username already exists"}), 400
    finally:
        cur.close()
        conn.close()
    return jsonify({"success": True})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username= data["username"]
    password= data["password"]
    
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("select * from users where username=%s", (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    if user and bcrypt.checkpw(password.encode(), user["password"].encode()):
        return jsonify({"success": True})
    return jsonify({"success": False}), 401

@app.route("/profile/<username>", methods=["GET"])
def get_profile(username):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("select username, display_name, avatar_url,full_name,age ,email, gender from users where username=%s", (username,))
    user = cur.fetchone()
    cur.close(); conn.close()
    if not user:
        return jsonify({"success": False, "error": "User not found"}),404
    return jsonify({"success": True ,"profile": user})

@app.route("/profile/<username>", methods = ["PUT"])
def update_profile(username):
    data = request.json
    display_name = (data.get("display_name") or "").strip()
    avatar_url = (data.get("avatar_url") or "").strip()
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET display_name=%s, avatar_url=%s WHERE username=%s",
                (display_name or None, avatar_url or None, username))
    conn.commit()
    cur.close(); 
    conn.close()
    return jsonify({"success": True})

@app.route("/forget", methods=["POST"])
def forget_password():
    data = request.json
    username = (data.get("username") or "").strip()
    
    token = secrets.token_urlsafe(32)
    expires = datetime.now() + timedelta(minutes=30)
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("select 1 from users where username=%s", (username,))
    exists = cur.fetchone()
    if not exists:
        cur.close(); conn.close()
        return jsonify({"success": True})
    
    cur.execute("insert into password_reset (username, token, expires_at) VALUES (%s,%s,%s)",
                (username, token,expires))
    conn.commit()
    cur.close(); conn.close()
    
    print(f"[RESET] Token for {username}: {token}")
    return jsonify({"success": True})

@app.route("/reset", methods=["POST"])
def reset_password():
    data = request.json
    token = (data.get("token") or "").strip()
    new_password = (data.get("password") or "").strip()
    
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT username , expires_at  FROM password_reset WHERE token=%s", (token,))
    row = cur.fetchone()
    if not row or row["expires_at"] < datetime.now():
        cur.close(); conn.close()
        return jsonify({"success": False, "error": "invalid or expired token"}), 400
    
    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    cur2 = conn.cursor()
    cur2.execute("UPDATE users SET password=%s WHERE username=%s ", (hashed, row["username"]))
    cur2.execute("DELETE FROM password_reset WHERE token=%s", (token,))
    conn.commit()
    cur.close(); cur2.close(); conn.close()
    return jsonify({"success": True})   

@app.route("/online_users", methods=["GET"])
def online_users():
    unique = sorted(set(users.values()))
    return jsonify({"success": True, "users": unique})

@app.route("/room/<room_name>", methods=["GET"])
def get_room(room_name):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT room_name, is_private, theme, background_url FROM rooms WHERE room_name=%s", (room_name,))
    room = cur.fetchone()
    cur.close(); conn.close()
    if not room:
        return jsonify({"success": False, "error": "room not found"}), 404
    return jsonify({"success": True, "room": room})

@app.route("/room/<room_name>", methods=["PUT"])
def update_room(room_name):
    data = request.json
    new_name = (data.get("new_name") or "").strip()
    theme = (data.get("theme") or "").strip()
    background_url = (data.get("background_url") or "").strip()
    
    conn = get_db()
    cur = conn.cursor()
    if new_name:
        cur.execute("UPDATE rooms SET room_name=%s WHERE room_name=%s", (new_name, room_name))
        room_name = new_name
    cur.execute("UPDATE rooms SET theme=%s, background_url=%s WHERE room_name=%s",
            (theme or None, background_url or None, room_name))
    conn.commit()
    cur.close(); conn.close()
    return jsonify({"success": True, "room_name": room_name})
    
@app.route("/create_room", methods=["POST"])
def create_room():
    data = request.json
    room_name = data["room_name"]
    is_private = data.get("is_private",False)
    password = data.get("password")
    
    password_hash = None
    if is_private and password:
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO rooms (room_name, is_private, password_hash) VALUES(%s,%s,%s)",
            (room_name,is_private, password_hash)
        )
        conn.commit()
        return jsonify({"success":True})
    except mysql.connector.IntegrityError:
        return jsonify({"success":False,"error": 'room already exists'}), 400
    finally:
        cur.close()
        conn.close()

@socketio.on("join")
def handle_join(data):
    username = (data.get("username") or data.get("user") or "Anonymous").strip()
    room = (data.get("room") or "lobby").strip()
    
    users[request.sid] = username
    
    join_room(room)
    
    now = datetime.now().strftime("%H:%M:%S")
    emit("message", {"type": "system", "user": "System", "text": f"{username} joined {room}", "time": now}, room=room)
    
    emit("update_users", list(set(users.values())), broadcast=True)
    
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    
    cur.execute("SELECT sender, recipient, room, text, timestamp FROM messages WHERE room=%s ORDER BY timestamp DESC LIMIT 10", (room,))
    history = cur.fetchall()
    cur.close()
    conn.close()
    normalized = [
        {
            "type": "chat" if not row["recipient"] else "private",
            "user": row["sender"],
            "to": row["recipient"],
            "text": row["text"],
            "time": row["timestamp"].strftime("%H:%M:%S")    
        } for row in history
    ]
    emit("history",normalized,room=request.sid)
    
@socketio.on("join_room")
def handle_join_room(data):
    username = (data.get("username") or "Anonymous").strip()
    room_name = data.get("room_name")
    password = data.get("password")
    
    users[request.sid] = username
    
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM rooms WHERE room_name=%s", (room_name,))
    room = cur.fetchone()
    cur.close()
    conn.close()
    
    if not room:
        emit("message", {"type": "system", "user": "System","text":"Room not found.","time":datetime.now().strftime("%H:%M:%S")}, room=request.sid)
        return
    
    if room["is_private"]:
        if not password or not bcrypt.checkpw(password.encode(), room["password_hash"].encode()):
            emit("message", {"type":"system", "user":"System","text":"Wrong password","time":datetime.now().strftime("%H:%M:%S")}, room=request.sid)
            return
        
    join_room(room_name)
    emit("message",{"type":"system","user":"System","text":f"{username} joined {room_name}","time":datetime.now().strftime("%H:%M:%S")}, room=room_name)
    emit("update_users", list(set(users.values())), broadcast=True)
      
            
@socketio.on("chat")
def handle_chat(data):
    username = (data.get("user") or users.get(request.sid) or "Anonymous").strip()
    text = (data.get("text") or "").strip()
    room = (data.get("room") or "lobby").strip()
    now = datetime.now().strftime("%H:%M:%S")
     
    if not text:
        return
         
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO messages (sender, room ,text) VALUES (%s,%s,%s)", (username, room, text))
    conn.commit()
    cur.close()
    conn.close()
    
    emit("message", {"type": "chat", "user": username, "text": text, "time": now}, room=room)
    
@socketio.on("private_msg")
def handle_private_msg(data):
    sender = (data.get("user") or users.get(request.sid) or "Anonymous").strip()
    recipient = (data.get("to") or "").strip()
    text = (data.get("text") or "").strip()
    now = datetime.now().strftime("%H:%M:%S")
    
    if not recipient or not text:
        emit("message",{"type": "system", "user": "System","text": "Invalid private message", "time":now}, room=request.sid)
        return
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO messages (sender,recipient,room, text, timestamp) VALUES (%s,%s,%s,%s,%s)",
        (sender,recipient,None,text, datetime.now()))
    conn.commit()
    cur.close()
    conn.close()
    
    recipient_sid = next((sid for sid,user in users.items() if user.lower() == recipient.lower()), None)
    if recipient_sid:
        emit("message", {"type": "private", "user": sender, "to": recipient,"text": text, "time":now}, room =recipient_sid)
        emit("message", {"type": "private", "user": sender, "to": recipient,"text": text, "time":now}, room =request.sid)
    else:
        emit("message", {"type": "system", "user": "System", "text": f"User {recipient} not found", "time":now}, room=request.sid)

@socketio.on("invite_user")
def handle_invite(data):
    recipient = data.get("to")
    room = data.get("room")
    recipient_sid = next((sid for sid,user in users.items() if user == recipient), None)
    if recipient_sid:
        emit("message", {"type":"system", "user":"System","text":f"You are invited to join {room} room."}, room=recipient_sid)

@socketio.on("friend_request")
def handle_friend_request(data):
    recipient = data.get("to")
    sender = data.get("from")
    recipient_sid = next((sid for sid, user in users.items() if user == recipient), None)
    if recipient_sid:
        emit("message", {"type":"system", "user":"System","text":f"{sender} send you a friend request"}, room=recipient_sid)

@socketio.on("quit")
def handle_quit(data):
    username = users.pop(request.sid, "Anonymous")
    now = datetime.now().strftime("%H:%M:%S")
    emit("message",{"type": "system", "user": "System", "text": f"{username} left", "time":now}, broadcast=True)
    emit("update_users", list(set(users.values())), broadcast=True)

@socketio.on("disconnect")
def handle_disconnect():
    username = users.pop(request.sid, "Anonymous")
    now = datetime.now().strftime("%H:%M:%S")
    emit("message",{"type": "system", "user": "System", "text": f"{username} disconnected", "time":now}, broadcast=True)
    emit("update_users", list(set(users.values())), broadcast=True)
      
    
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)

    