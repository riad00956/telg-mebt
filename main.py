import os
import json
import asyncio
from threading import Thread
from pathlib import Path

from flask import Flask, render_template_string, request, redirect, session, url_for
from telethon import TelegramClient, events, functions, types
from telethon.sessions import StringSession

# ===================== কনফিগার =====================
PASSWORD = "Riadalh000@"
DB_FILE = Path("database/data.json")
SESSION_FILE = Path("account/account.season")   # আপনার ফাইল এখানে রাখবেন
SECRET_KEY = os.urandom(24)

# টেলিগ্রাম API (আপনার নিজের – env থেকে নিন)
API_ID = int(os.environ.get("API_ID", 12345))
API_HASH = os.environ.get("API_HASH", "your_api_hash")

app = Flask(__name__)
app.secret_key = SECRET_KEY

telegram_client = None
settings = {
    "auto_reply_text": "I am currently offline. Will reply later.",
    "online_duration": 15
}

# ===================== ডাটাবেস ফাংশন =====================
def ensure_files():
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DB_FILE.exists():
        with open(DB_FILE, "w") as f:
            json.dump(settings, f, indent=4)
    else:
        load_settings()

def load_settings():
    global settings
    with open(DB_FILE, "r") as f:
        settings = json.load(f)

def save_settings(new_settings):
    global settings
    settings.update(new_settings)
    with open(DB_FILE, "w") as f:
        json.dump(settings, f, indent=4)

# ===================== টেলিগ্রাম ব্যাকগ্রাউন্ড =====================
async def start_telegram_client():
    global telegram_client
    if not SESSION_FILE.exists():
        print("❌ account.season ফাইল পাওয়া যায়নি। দয়া করে ফাইলটি account/ ফোল্ডারে রাখুন।")
        return

    with open(SESSION_FILE, "r") as f:
        session_str = f.read().strip()
    if not session_str:
        print("❌ account.season ফাইল খালি।")
        return

    client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
    await client.connect()
    if not await client.is_user_authorized():
        print("❌ সেশনটি বৈধ নয়। পুনরায় সেশন নিন।")
        return

    telegram_client = client
    print("✅ টেলিগ্রাম সংযুক্ত – অটোরিপ্লাই সক্রিয়।")

    @client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
    async def auto_reply(event):
        load_settings()   # সর্বশেষ সেটিংস লোড
        reply_text = settings.get("auto_reply_text", "I am offline.")
        online_sec = settings.get("online_duration", 15)

        try:
            me = await client.get_me()
            user = await client(functions.users.GetUsersRequest(id=[me.id]))
            if isinstance(user[0].status, types.UserStatusOnline):
                return  # ইতিমধ্যে অনলাইন, রিপ্লাই দেবে না

            await event.reply(reply_text)
            await client(functions.account.UpdateStatusRequest(offline=False))
            await asyncio.sleep(online_sec)
            await client(functions.account.UpdateStatusRequest(offline=True))
        except Exception as e:
            print(f"অটোরিপ্লাই ত্রুটি: {e}")

    await client.run_until_disconnected()

def run_telegram_loop():
    asyncio.run(start_telegram_client())

# ===================== সুন্দর গ্লাসি ইউআই =====================
LOGIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
    <title>লগইন | অটো রিপ্লাই বট</title>
    <style>
        * { margin:0; padding:0; box-sizing:border-box; font-family:'Inter',system-ui; }
        body {
            min-height:100vh;
            background: linear-gradient(135deg, #e0f2fe 0%, #bfdbfe 100%);
            display:flex;
            align-items:center;
            justify-content:center;
            padding:1.5rem;
        }
        .glass {
            background: rgba(255,255,255,0.75);
            backdrop-filter: blur(12px);
            border-radius: 2rem;
            padding: 2rem 1.8rem;
            width:100%;
            max-width:400px;
            box-shadow: 0 20px 35px -10px rgba(0,0,0,0.1), 0 0 0 1px rgba(255,255,255,0.5);
        }
        h2 {
            font-size:1.8rem;
            font-weight:700;
            background: linear-gradient(120deg,#1e3a8a,#3b82f6);
            background-clip:text;
            -webkit-background-clip:text;
            color:transparent;
            text-align:center;
            margin-bottom:1.5rem;
        }
        input {
            width:100%;
            padding:1rem 1.2rem;
            background:rgba(255,255,255,0.9);
            border:1px solid rgba(59,130,246,0.3);
            border-radius:2rem;
            font-size:1rem;
            outline:none;
            margin-bottom:1.5rem;
        }
        input:focus {
            border-color:#3b82f6;
            box-shadow:0 0 0 3px rgba(59,130,246,0.2);
        }
        button {
            width:100%;
            padding:1rem;
            background:#2563eb;
            border:none;
            border-radius:2rem;
            font-weight:600;
            color:white;
            cursor:pointer;
            transition:0.2s;
            font-size:1rem;
        }
        button:hover { background:#1d4ed8; transform:translateY(-2px); }
        .error {
            background:rgba(239,68,68,0.15);
            color:#b91c1c;
            padding:0.8rem;
            border-radius:2rem;
            text-align:center;
            margin-bottom:1rem;
        }
        @media (max-width:480px) { .glass { padding:1.5rem; } h2 { font-size:1.5rem; } }
    </style>
</head>
<body>
    <div class="glass">
        <h2>✨ অটো রিপ্লাই বট</h2>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="post">
            <input type="password" name="password" placeholder="পাসওয়ার্ড দিন" required>
            <button type="submit">🔓 লগইন</button>
        </form>
    </div>
</body>
</html>
'''

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
    <title>ড্যাশবোর্ড | অটো রিপ্লাই বট</title>
    <style>
        * { margin:0; padding:0; box-sizing:border-box; font-family:'Inter',system-ui; }
        body {
            min-height:100vh;
            background: linear-gradient(135deg, #e0f2fe 0%, #bfdbfe 100%);
            padding:1.5rem;
        }
        .container { max-width:550px; margin:0 auto; }
        .glass {
            background: rgba(255,255,255,0.8);
            backdrop-filter: blur(16px);
            border-radius: 2rem;
            padding: 2rem 1.8rem;
            box-shadow: 0 25px 40px -12px rgba(0,0,0,0.15);
        }
        h2 {
            font-size:1.8rem;
            font-weight:700;
            background: linear-gradient(120deg,#1e3a8a,#2563eb);
            background-clip:text;
            -webkit-background-clip:text;
            color:transparent;
            margin-bottom:0.5rem;
        }
        .sub {
            color:#475569;
            margin-bottom:2rem;
            border-left:3px solid #3b82f6;
            padding-left:0.8rem;
            font-size:0.9rem;
        }
        label {
            font-weight:600;
            color:#1e293b;
            display:block;
            margin-top:1.2rem;
            margin-bottom:0.4rem;
        }
        textarea, input {
            width:100%;
            padding:0.9rem 1rem;
            background:rgba(255,255,255,0.95);
            border:1px solid rgba(59,130,246,0.4);
            border-radius:1.5rem;
            font-size:0.95rem;
            outline:none;
        }
        textarea { min-height:100px; resize:vertical; }
        textarea:focus, input:focus {
            border-color:#3b82f6;
            box-shadow:0 0 0 3px rgba(59,130,246,0.2);
        }
        .btn-group {
            display:flex;
            gap:1rem;
            margin-top:2rem;
            flex-wrap:wrap;
        }
        .btn-save {
            flex:1;
            background:#2563eb;
            color:white;
            border:none;
            padding:0.9rem;
            border-radius:2rem;
            font-weight:600;
            cursor:pointer;
        }
        .btn-save:hover { background:#1d4ed8; transform:translateY(-2px); }
        .btn-logout {
            flex:1;
            background:rgba(220,38,38,0.85);
            text-align:center;
            text-decoration:none;
            padding:0.9rem;
            border-radius:2rem;
            font-weight:600;
            color:white;
        }
        .btn-logout:hover { background:#dc2626; transform:translateY(-2px); }
        .success {
            background:rgba(34,197,94,0.15);
            border:1px solid rgba(34,197,94,0.3);
            color:#15803d;
            padding:0.9rem;
            border-radius:1.5rem;
            margin-bottom:1.5rem;
            text-align:center;
        }
        @media (max-width:500px) {
            .glass { padding:1.5rem; }
            h2 { font-size:1.5rem; }
            .btn-group { flex-direction:column; }
        }
    </style>
</head>
<body>
<div class="container">
    <div class="glass">
        <h2>⚙️ কন্ট্রোল প্যানেল</h2>
        <div class="sub">আপনার অটো-রিপ্লাই কাস্টমাইজ করুন</div>
        {% if msg %}<div class="success">{{ msg }}</div>{% endif %}
        <form method="post">
            <label>📝 অটো রিপ্লাই টেক্সট</label>
            <textarea name="auto_reply_text" required>{{ settings.auto_reply_text }}</textarea>

            <label>⏱️ রিপ্লাই দেওয়ার পর অনলাইনে থাকার সময় (সেকেন্ড)</label>
            <input type="number" name="online_duration" value="{{ settings.online_duration }}" min="1" max="300" required>

            <div class="btn-group">
                <button type="submit" class="btn-save">💾 সংরক্ষণ</button>
                <a href="/logout" class="btn-logout">🚪 লগআউট</a>
            </div>
        </form>
    </div>
</div>
</body>
</html>
'''

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        return render_template_string(LOGIN_HTML, error="ভুল পাসওয়ার্ড!")
    if session.get("logged_in"):
        return redirect(url_for("dashboard"))
    return render_template_string(LOGIN_HTML, error=None)

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    msg = None
    if request.method == "POST":
        new_text = request.form.get("auto_reply_text", "").strip()
        new_duration = int(request.form.get("online_duration", 15))
        if new_text:
            save_settings({"auto_reply_text": new_text, "online_duration": new_duration})
            msg = "✅ সেটিংস সফলভাবে আপডেট হয়েছে!"
        else:
            msg = "⚠️ মেসেজ খালি রাখা যাবে না।"
    load_settings()
    return render_template_string(DASHBOARD_HTML, settings=settings, msg=msg)

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))

@app.route("/")
def home():
    return redirect(url_for("login"))

# ===================== মেইন =====================
if __name__ == "__main__":
    ensure_files()
    # ব্যাকগ্রাউন্ডে টেলিগ্রাম ক্লায়েন্ট চালু
    Thread(target=run_telegram_loop, daemon=True).start()
    # ফ্লাস্ক সার্ভার
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
