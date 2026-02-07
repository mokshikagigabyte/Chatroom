"""import mysql.connector
username="alice"
password="1234"
conn = mysql.connector.connect(
        host="localhost",
        user="chatuser",
        password="strongpass123!",
        database="chatapp"
    )

cur = conn.cursor()

cur.execute("select id FROM users WHERE username=%s", (username,))
if cur.fetchone():
    print("username already exists")
else:
    cur.execute("insert into users (username, password) VALUES (%s,%s)", (username, password))

conn.commit()

print("inserted user ID:", cur.lastrowid)

cur.close()
conn.close()

def authentication(username, password):
    conn = mysql.connector.connect(
        host="localhost",
        user="chatuser",
        password="strongpass123!",
        database="chatapp"
    )
    cur = conn.cursor(dictionary= True)
    cur.execute("select * from users WHERE username = %s AND password=%s", (username, password))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user is not None

print(authentication("alice","1234"))
    
def save_message(sender, recipient, room, text):
    conn = mysql.connector.connect(
        host="localhost",
        user="chatuser",
        password="strongpass123!",
        database="chatapp"
    )
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO messages (sender,recipient , room, text) VALUES (%s,%s,%s,%s)",
        (sender,recipient, room ,text)
    )
    conn.commit()
    
    print("inserted user ID:", cur.lastrowid)
    
    cur.close()
    conn.close()
    
save_message("alice","bob",None,"Hello bob!")

def get_recent_messages(limit=10):
    conn = mysql.connector.connect(
        host="localhost",
        user="chatuser",
        password="strongpass123!",
        database="chatapp"
    )
    cur = conn.cursor(dictionary= True)
    cur.execute("SELECT * FROM messages ORDER BY timestamp DESC LIMIT %s", (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

print(get_recent_messages())
"""