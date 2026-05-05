from flask import Flask, render_template_string, request
import g4f
import os

app = Flask(__name__)

# История чатов хранится в браузере (в LocalStorage), поэтому тут она пустая
chat_history = [] 

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>AI Vision Cloud | Online</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0b0e14; color: #ffffff; margin: 0; display: flex; height: 100vh; overflow: hidden; }
        .sidebar { width: 260px; background: #000; border-right: 1px solid #232931; display: flex; flex-direction: column; padding: 15px; }
        .new-chat-btn { border: 1px solid #333; padding: 12px; border-radius: 8px; text-align: center; cursor: pointer; transition: 0.3s; margin-bottom: 20px; font-weight: bold; color: #00a2ff; }
        .new-chat-btn:hover { background: #2d343f; border-color: #00a2ff; }
        .chat-list { flex: 1; overflow-y: auto; }
        .chat-item { padding: 12px; border-radius: 8px; margin-bottom: 8px; cursor: pointer; font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #aaa; border: 1px solid transparent; }
        .chat-item:hover { background: #151921; color: white; }
        .chat-item.active { background: #1f242d; color: #00a2ff; border-color: #00a2ff33; }
        .main-content { flex: 1; display: flex; flex-direction: column; background: #0b0e14; }
        header { padding: 15px; border-bottom: 1px solid #1f242d; text-align: center; }
        header h1 { margin: 0; font-size: 1.2em; color: #00a2ff; }
        #chat-box { flex: 1; overflow-y: auto; padding: 40px 15% 100px 15%; scroll-behavior: smooth; white-space: pre-wrap; }
        .msg { margin-bottom: 30px; border-bottom: 1px solid #1f242d; padding-bottom: 15px; line-height: 1.6; }
        .user-tag { color: #00a2ff; font-weight: bold; display: block; margin-bottom: 5px; }
        .ai-tag { color: #00ff95; font-weight: bold; display: block; margin-bottom: 5px; }
        .input-container { padding: 20px 15% 40px 15%; background: linear-gradient(transparent, #0b0e14 20%); }
        .input-area { display: flex; gap: 10px; background: #1f242d; padding: 10px; border-radius: 12px; border: 1px solid #2d343f; }
        input { flex: 1; padding: 10px; background: transparent; border: none; color: white; outline: none; font-size: 15px; }
        button { background: #00a2ff; color: white; border: none; width: 45px; height: 45px; border-radius: 8px; cursor: pointer; font-weight: bold; }
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-thumb { background: #2d343f; border-radius: 10px; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="new-chat-btn" onclick="startNewChat()">+ Новый чат</div>
        <div class="chat-list" id="chatList"></div>
    </div>
    <div class="main-content">
        <header><h1>AI VISION CLOUD</h1></header>
        <div id="chat-box"></div>
        <div class="input-container">
            <div class="input-area">
                <input type="text" id="userInput" placeholder="Спроси о чем угодно..." onkeypress="if(event.keyCode==13) send()">
                <button onclick="send()">↑</button>
            </div>
        </div>
    </div>

    <script>
        let currentChatId = Date.now();
        let allChats = JSON.parse(localStorage.getItem('cloud_chats_v1') || '{}');

        function updateSidebar() {
            const list = document.getElementById('chatList');
            list.innerHTML = '';
            Object.keys(allChats).sort((a, b) => b - a).forEach(id => {
                const item = document.createElement('div');
                item.className = 'chat-item' + (id == currentChatId ? ' active' : '');
                item.innerText = allChats[id].title || "Диалог";
                item.onclick = () => loadChat(id);
                list.appendChild(item);
            });
        }

        async function send() {
            const input = document.getElementById('userInput');
            const chatBox = document.getElementById('chat-box');
            const text = input.value.trim();
            if (!text) return;

            if (!allChats[currentChatId]) {
                allChats[currentChatId] = { title: text.substring(0, 25), html: "" };
            }

            chatBox.innerHTML += `<div class="msg"><span class="user-tag">ВЫ:</span>${text}</div>`;
            input.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;

            try {
                const response = await fetch('/ask?q=' + encodeURIComponent(text));
                const data = await response.text();
                chatBox.innerHTML += `<div class="msg"><span class="ai-tag">AI:</span>${data}</div>`;
                
                allChats[currentChatId].html = chatBox.innerHTML;
                localStorage.setItem('cloud_chats_v1', JSON.stringify(allChats));
                updateSidebar();
            } catch (e) {
                chatBox.innerHTML += `<div style="color:red">Ошибка связи</div>`;
            }
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        function startNewChat() {
            currentChatId = Date.now();
            document.getElementById('chat-box').innerHTML = '';
            updateSidebar();
        }

        function loadChat(id) {
            currentChatId = id;
            document.getElementById('chat-box').innerHTML = allChats[id].html;
            updateSidebar();
        }

        updateSidebar();
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/ask')
def ask():
    query = request.args.get('q')
    try:
        response = g4f.ChatCompletion.create(
            model=g4f.models.default,
            messages=[{"role": "user", "content": query}]
        )
        return str(response)
    except Exception as e:
        return f"Сервер под нагрузкой, попробуй еще раз. (Ошибка: {str(e)})"

if __name__ == '__main__':
    # Получаем порт из переменной окружения (нужно для Render)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

