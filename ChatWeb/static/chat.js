const socket = io("http://localhost:5000");

const messagesEl = document.getElementById("messages");
const inputEl = document.getElementById("input");
const nameEl = document.getElementById("name");
const sendBtn = document.getElementById("send");
const userEl = document.getElementById("users");
const recipientEl = document.getElementById("recipient");
const roomEl = document.getElementById("room");
const roomPasswordEl =document.getElementById("roomPassword");
const authSection = document.getElementById("auth-section");
const roomSection = document.getElementById("room-section");
const chatSection = document.getElementById("chat-section");
const joinRoomBtn = document.getElementById("joinRoomBtn");
const createRoomSection =document.getElementById("create-room-section");
const currentRoomEl = document.getElementById("currentRoom");
const currentUserLabel = document.getElementById("currentUser");
const loginWrapper = document.getElementById("loginFormWrapper");
const registerWrapper = document.getElementById("registerFormWrapper");
const showRegister =document.getElementById("showRegister");
const showLogin = document.getElementById("showLogin");


let currentUser = "";
let currentRoom = "";



document.getElementById("loginForm").addEventListener("submit", async(e) =>{
    e.preventDefault();
    const username = document.getElementById("loginUser").value;
    const password = document.getElementById("loginPass").value;

    const res = await fetch("/login",{
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({username, password})
    });
    const data = await res.json();

    if (data.success){
        currentUser = username;
        showSection("dashboard");
    
       try{
        const pRes = await fetch(`/profile/${currentUser}`);
        const pData = await pRes.json();
        if(pData.success){
            const p = pData.profile;
            currentUserLabel.textContent = `logged in as: ${p.display_name || p.username}`;
        }
        } catch (err){
            console.warn("Profile fetch Failed:", err);
        }
            
        alert("login successful!");
    } else{
        alert("login failed!");
    }

});

function showSection(sectionId){
    const section = ["auth-section", "dashboard", "profile-section", "chat-section"];
    section.forEach(id => {
        document.getElementById(id).classList.add("hidden");
    });
    document.getElementById(sectionId).classList.remove("hidden");
}

document.getElementById("forgotPassLink").addEventListener("click", (e) =>{
    e.preventDefault();
    document.getElementById("forgotPassModel").classList.remove("hidden");
});

async function loadOnlineUsers(){
    const res = await fetch("/online_users");
    const data = await res.json();
    if(!data.success) return;
    userEl.innerHTML = "";
   data.users.filter(u => u !== currentUser).forEach(u => {
    const li = document.createElement("li");
    li.textContent = u;
    li.onclick = () =>{
        recipientEl.value = u;
        inputEl.focus();
    };
    userEl.appendChild(li);
});
}

socket.on("update_users", () => loadOnlineUsers());


async function applyRoomTheme(roomName) {
    const res = await fetch(`/room/${roomName}`);
    const data = await res.json();
    if (!data.success) return;
    const r = data.room;
    if (r.background_url){
        document.body.style.backgroundImage = `url(${r.background_url})`;
        document.body.style.backgroundSize = "cover";
    } else{
        document.body.style.backgroundImage = "";
    }
    document.body.dataset.theme = r.theme || "default";
}

socket.on("message", (msg) => {
    if (msg.type === "system" && msg.text.includes("joined")){
        const match = msg.text.match(/joined (.+)$/);
        if (match) applyRoomTheme(match[1].trim());
        addMessage(msg);
    } else if(msg.type === "private"){
        addPrivateMessage(msg);
    } else{
        addMessage(msg);
    }
});

document.getElementById("registerForm").addEventListener("submit", async(e) =>{
    e.preventDefault();
    const username = document.getElementById("regUser").value;
    const password = document.getElementById("regPass").value;
    const full_name = document.getElementById("regName").value;
    const age = document.getElementById("regAge").value;
    const email = document.getElementById("regEmail").value;
    const gender = document.getElementById("regGender").value;
    
    const res = await fetch("/register",{
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({username, password,full_name,age,email,gender})
    });
    const data = await res.json();

    if (data.success){
        alert("Registration successful! please login.");
        showSection("auth-section");
    } else{
        alert("Registration failed: " + data.error);
    }
});

document.getElementById("showRegister").addEventListener("click", (e) =>{
    e.preventDefault();
    document.getElementById("loginFormWrapper").classList.add("hidden");
    document.getElementById("registerFormWrapper").classList.remove("hidden");
});

document.getElementById("showLogin").addEventListener("click", (e) =>{
    e.preventDefault();
    document.getElementById("registerFormWrapper").classList.add("hidden");
    document.getElementById("loginFormWrapper").classList.remove("hidden");
});




document.getElementById("roomForm").addEventListener("submit", (e) =>{
    e.preventDefault();
    const room = roomEl.value.trim() || "lobby";
    const roomPassword = roomPasswordEl.value.trim();
    if(!currentUser ){
        alert("please login first.");
        return;
    }

    currentRoom = room;
    currentRoomEl.textContent = `current Room: ${room}`;
    socket.emit("join_room", {room_name: room,password: roomPassword , username : currentUser});
    showSection("chat-section");

});
    
document.getElementById("createRoomForm").addEventListener("submit", async (e) =>{
    e.preventDefault();
    const roomName = document.getElementById("newRoomName").value.trim();
    const password = document.getElementById("newRoomPassword").value.trim();
    const isPrivate = document.getElementById("isPrivate").checked;

    const res = await fetch("/create_room",{
        method : "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({room_name: roomName, is_private: isPrivate, password})
    });
    const data = await res.json();
    if (data.success){
        alert(`Room "${roomName}" created! now join it from the join form.`);
        showSection("chat-section");
    } else{
        alert("failed to create room:" +data.error);
    }
});

document.getElementById("exitRoomBtn").addEventListener("click", () =>{
    showSection("dashboard");
});

document.getElementById("logoutBtn").addEventListener("click", () =>{
    currentUser = "";
    showSection("auth-section");
});

 socket.on("connect", () => 
    console.log("connected"));
    
 socket.on("history", (items) =>
    items.slice().reverse().forEach(addMessage));

socket.on("update_users",(userList) => {
    userEl.innerHTML = "";
    userList.forEach(user => {
        const li = document.createElement("li");
        li.textContent = user;

    const inviteBtn = document.createElement("button");
    inviteBtn.textContent = "Invite";
    inviteBtn.onclick = () =>{
        socket.emit("invite_user", {from: currentUser, to: user,room: currentRoom || "lobby"});
       
    };
    li.appendChild(inviteBtn);

    const friendBtn = document.createElement("button");
    friendBtn.textContent = "Add Friend";
    friendBtn.onclick = () =>{
        socket.emit("friend_request",{from: currentUser, to: user});
    };
    li.appendChild(friendBtn);

    userEl.appendChild(li);
    });
});


function addPrivateMessage(msg){
    const div = document.createElement("div");
    div.className = "private";
    if(msg.user === currentUser){
        div.textContent = `[DM] YOU -> ${msg.to}: ${msg.text}`;
    } else if(msg.to === currentUser){
        div.textContent = `[DM] ${msg.user} -> YOU: ${msg.text}`;
    }else{
    div.textContent = `[DM] ${msg.user} -> ${msg.to}: ${msg.text}`;
    }
    document.getElementById("dmMessages").appendChild(div);
}

document.getElementById("dmToggle").addEventListener("click", () => {
    document.getElementById("dmSection").classList.toggle("hidden");
});

function addMessage(msg) {
    if(msg.type === "private")return; 
    const div = document.createElement("div");
    div.className = "message " + (msg.type || "chat");
    const timeLabel = msg.time || new Date().toLocaleTimeString();
    let text = `[${timeLabel}] ${msg.user || "unknown"}: ${msg.text}`;
    div.textContent = text;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
}
 
sendBtn.addEventListener("click", () => {
    const text = inputEl.value.trim();
    const room = currentRoom || roomEl.value.trim() || "lobby";
    const recipient = recipientEl.value.trim();
    
    if (!currentUser || !socket.connected || !text) return;
    
    if (text.toUpperCase() === "QUIT") {
        socket.emit("quit", {user: currentUser });
        socket.disconnect();
        return
    }
    else if (recipient){
        socket.emit("private_msg",{user: currentUser,to: recipient,text});
    } else{
        socket.emit("chat",{user: currentUser,room,text});
    }

    inputEl.value = "";
    });
