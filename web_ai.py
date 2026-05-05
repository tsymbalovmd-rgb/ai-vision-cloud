from flask import Flask, render_template_string, request
import g4f
import base64

app = Flask(__name__)

# Твой топовый дизайн
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>AI Vision Cloud | Vision Pro</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0b0e14; color: #ffffff; margin: 0; display: flex; height: 100vh; overflow: hidden; }
        .sidebar { width: 260px; background: #000; border-right: 1px solid #232931; display: flex; flex-direction: column; padding: 15px; }
        .new-chat-btn { border: 1px solid #333; padding: 12px; border-radius: 8px; text-align: center; cursor: pointer; transition: 0.3s; margin-bottom: 20px; font-weight: bold; }
        .new-chat-btn:hover { background: #2d343f; border-color: #00a2ff; }
        .chat-list { flex: 1; overflow-y: auto; }
        .chat-item { padding: 12px; border-radius: 8px; margin-bottom: 8px; cursor: pointer; font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #aaa; border: 1px solid transparent; }
        .chat-item:hover { background: #151921; color: white; }
        .chat-item.active { background: #1f242d; color: #00a2ff; border-color: #00a2ff33; }
        .main-content { flex: 1; display: flex; flex-direction: column; background: #0b0e14; }
        #chat-box { flex: 1; overflow-y: auto; padding: 40px 10% 100px 10%; scroll-behavior: smooth; }
        .msg { margin-bottom: 30px; }
        .user-tag { color: #00a2ff; font-weight: bold; display: block; margin-bottom: 5px; }
        .ai-tag { color: #00ff95; font-weight: bold; display: block; margin-bottom: 5px; }
        .msg-text { white-space: pre-wrap; line-height: 1.6; }
        .preview-img { max-width: 300px; border-radius: 10px; margin: 10px 0; border: 1px solid #333; }
        .input-container { padding: 20px 10% 40px 10%; background: linear-gradient(transparent, #0b0e14 20%); }
        .input-area { display: flex; gap: 10px; background: #1f242d; padding: 10px; border-radius: 12px; border: 1px solid #2d343f; align-items: center; }
        input[type="text"] { flex: 1; padding: 10px; background: transparent; border: none; color: white; outline: none; font-size: 15px; }
        .btn-icon { background: #2d343f; color: white; border: none; width: 40px; height: 40px; border-radius: 8px; cursor: pointer; font-size: 18px; display: flex; align-items: center; justify-content: center; }
        .btn-send { background: #00a2ff; color: white; border: none; width: 45px; height: 45px; border-radius: 8px; cursor: pointer; font-weight: bold; }
        #imageInput { display: none; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="new-chat-btn" onclick="startNewChat()">+ Новый чат</div>
        <div class="chat-list" id="chatList"></div>
    </div>
    <div class="main-content">
        <div id="chat-box"></div>
        <div class="input-container">
            <div class="input-area">
                <label for="imageInput" class="btn-icon" id="file-label">📷</label>
                <input type="file" id="imageInput" accept="image/*" onchange="handleFile()">
                <input type="text" id="userInput" placeholder="Прикрепи задачу и жми ↑..." onkeypress="if(event.keyCode==13) send()">
                <button class="btn-send" onclick="send()">↑</button>
            </div>
        </div>
    </div>

    <script>
        let currentChatId = Date.now();
        let allChats = JSON.parse(localStorage.getItem('ai_vision_final_v3') || '{}');
        let currentImageData = null;

        function handleFile() {
            const file = document.getElementById('imageInput').files;
            const reader = new FileReader();
            reader.onloadend = () => {
                currentImageData = reader.result;
                document.getElementById('file-label').innerText = '✅';
            };
            if (file) reader.readAsAsDataURL(file);
        }

        function updateSidebar() {
            const list = document.getElementById('chatList');
            list.innerHTML = '';
            Object.keys(allChats).sort((a, b) => b - a).forEach(id => {
                const item = document.createElement('div');
                item.className = 'chat-item' + (id == currentChatId ? ' active' : '');
                item.innerText = allChats[id].title || "Диалог " + id;
                item.onclick = () => loadChat(id);
                list.appendChild(item);
            });
        }

        async function send() {
            const input = document.getElementById('userInput');
            const text = input.value.trim();
            if (!text && !currentImageData) return;

            if (!allChats[currentChatId]) {
                allChats[currentChatId] = { title: (text || "Анализ фото").substring(0, 25), messages: [] };
            }

            const userMsg = { role: "user", content: text, image: currentImageData };
            allChats[currentChatId].messages.push(userMsg);
            renderMessage("ВЫ", text, "user-tag", currentImageData);
            
            const tempImage = currentImageData;
            input.value = '';
            currentImageData = null;
            document.getElementById('imageInput').value = '';
            document.getElementById('file-label').innerText = '📷';

            try {
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ 
                        messages: allChats[currentChatId].messages.map(m => ({role: m.role, content: m.content})),
                        image: tempImage 
                    })
                });
                const data = await response.text();
                
                const aiMsg = { role: "assistant", content: data };
                allChats[currentChatId].messages.push(aiMsg);
                renderMessage("AI", data, "ai-tag");

                localStorage.setItem('ai_vision_final_v3', JSON.stringify(allChats));
                updateSidebar();
            } catch (e) {
                renderMessage("SYSTEM", "Ошибка на сервере.", "user-tag");
            }
        }

        function renderMessage(tag, text, className, img = null) {
            const chatBox = document.getElementById('chat-box');
            let imgHtml = img ? `<img src="${img}" class="preview-img"><br>` : "";
            chatBox.innerHTML += `<div class="msg"><span class="${className}">${tag}:</span>${imgHtml}<div class="msg-text">${text}</div></div>`;
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        function startNewChat() {
            currentChatId = Date.now();
            document.getElementById('chat-box').innerHTML = '';
            updateSidebar();
        }

        function loadChat(id) {
            currentChatId = id;
            document.getElementById('chat-box').innerHTML = '';
            allChats[id].messages.forEach(m => {
                renderMessage(m.role === "user" ? "ВЫ" : "AI", m.content, m.role === "user" ? "user-tag" : "ai-tag", m.image);
            });
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

@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.json
        history = data.get('messages', [])
        image_data = data.get('image')
        
        if image_data and "," in image_data:
            image_data = image_data.split(",")

        # Самый стабильный способ: пусть библиотека сама ищет рабочего провайдера
        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_4o, # Модель, которая умеет видеть
            messages=history,
            image=image_data if image_data else None
        )
        
        if response:
            return str(response)
        return "Нейросеть промолчала. Попробуй еще раз."

    except Exception as e:
        return f"Сервер столкнулся с проблемой: {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
