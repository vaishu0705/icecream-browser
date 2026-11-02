
import streamlit as st
import requests
from urllib.parse import quote_plus

st.set_page_config(
    page_title="Icecream Browser",
    page_icon="🍦",
    layout="wide"
)

# ---------------------------------
# FESTIVAL THEMES
# ---------------------------------

themes = {
    "Everyday": {
        "bg": "#FFB6E6",
        "panel": "#FFF0FA",
        "text": "#8A0066",
        "accent": "#FF00A8",
        "button2": "#9B5DE5",
        "greeting": "🌸 🌈 Welcome to your colourful world! 🌈 🌸"
    },
    "Diwali": {
        "bg": "#651A38",
        "panel": "#8B3155",
        "text": "#FFF0B8",
        "accent": "#FFC247",
        "button2": "#FF7043",
        "greeting": "🪔 ✨ Happy Diwali! ✨ 🪔"
    },
    "Christmas": {
        "bg": "#0C4935",
        "panel": "#176448",
        "text": "#FFFFFF",
        "accent": "#E94B5A",
        "button2": "#28A745",
        "greeting": "🎄 🎁 Merry Christmas! 🎅"
    },
    "Holi": {
        "bg": "#FFD6A5",
        "panel": "#FFF0D8",
        "text": "#713C8C",
        "accent": "#E94B8A",
        "button2": "#00B4D8",
        "greeting": "🌈 🎨 Happy Holi! 🎨 🌈"
    }
}

# ---------------------------------
# SESSION MEMORY
# ---------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "spinner_on" not in st.session_state:
    st.session_state.spinner_on = False

if "theme" not in st.session_state:
    st.session_state.theme = "Everyday"

# ---------------------------------
# THEME CHOICE
# ---------------------------------

st.title("🍦 ICECREAM BROWSER 🍦")

choice = st.selectbox(
    "Choose your festival theme:",
    list(themes.keys()),
    index=list(themes.keys()).index(st.session_state.theme)
)

st.session_state.theme = choice
theme = themes[choice]

# ---------------------------------
# COLOURFUL WEBSITE DESIGN
# ---------------------------------

st.markdown(f"""
<style>
.stApp {{
    background-color: {theme['bg']};
    color: {theme['text']};
}}

h1, h2, h3, p, label {{
    color: {theme['text']} !important;
}}

div[data-testid="stChatMessage"] {{
    background-color: {theme['panel']};
    border-radius: 15px;
    padding: 10px;
}}

.stButton button {{
    background-color: {theme['accent']};
    color: white;
    border: none;
    border-radius: 12px;
    font-weight: bold;
}}

.stButton button:hover {{
    background-color: {theme['button2']};
    color: white;
}}

.stTextInput input {{
    background-color: {theme['panel']};
    color: {theme['text']};
}}
</style>
""", unsafe_allow_html=True)

st.markdown(
    f"<h3 style='text-align:center'>{theme['greeting']}</h3>",
    unsafe_allow_html=True
)

st.divider()

# ---------------------------------
# GOOGLE WEB SEARCH
# ---------------------------------

st.subheader("🔎 Search the Web")

search_query = st.text_input(
    "What would you like to search for?",
    key="search_box"
)

if st.button("🔎 Search Google"):
    if search_query.strip():
        search_url = (
            "https://www.google.com/search?q="
            + quote_plus(search_query)
        )
        st.link_button("Open Google Search", search_url)
    else:
        st.info("Please type something to search!")

st.divider()

# ---------------------------------
# ICECREAM AI CHAT
# ---------------------------------

st.subheader("🤖 Icecream AI Chat")


def get_secret(name, default=None):
    # st.secrets raises an error when no secrets are set up at all
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


# Online, the chat uses Google Gemini (key set in Streamlit secrets).
# On your own computer without a key, it falls back to Ollama.
gemini_key = get_secret("GEMINI_API_KEY")
gemini_model = get_secret("GEMINI_MODEL", "gemini-3.5-flash-lite")


def ask_gemini(messages):
    contents = [
        {
            "role": "model" if m["role"] == "assistant" else "user",
            "parts": [{"text": m["content"]}]
        }
        for m in messages
    ]
    response = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/"
        + gemini_model + ":generateContent",
        headers={"x-goog-api-key": gemini_key},
        json={"contents": contents},
        timeout=90
    )
    response.raise_for_status()
    return response.json()["candidates"][0]["content"]["parts"][0]["text"]


def ask_ollama(messages):
    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": "llama3.2:1b",
            "messages": messages,
            "stream": False
        },
        timeout=90
    )
    response.raise_for_status()
    return response.json()["message"]["content"]


st.write("Hello! Welcome to Icecream Browser! 🍦")
st.write("Ask me a question!")

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
question = st.chat_input("Type your message here...")

if question:
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    try:
        with st.spinner("🌈 Icecream AI is thinking..."):
            if gemini_key:
                answer = ask_gemini(st.session_state.messages)
            else:
                answer = ask_ollama(st.session_state.messages)

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

    except requests.exceptions.ConnectionError:
        if gemini_key:
            answer = "I cannot connect to the AI right now. Please try again."
        else:
            answer = (
                "I cannot connect to Ollama. "
                "Please check that it is running."
            )
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

    except requests.exceptions.HTTPError as error:
        status = error.response.status_code
        if status == 429:
            answer = (
                "Icecream AI is a bit busy right now. "
                "Please wait a minute and try again."
            )
        elif gemini_key and status in (400, 401, 403):
            answer = (
                "The AI key isn't working. "
                "Please check GEMINI_API_KEY in the app's secrets."
            )
        else:
            answer = "Something went wrong while talking to the AI."
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

    except requests.exceptions.Timeout:
        answer = "The AI took too long to answer. Please try again."
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

    except (requests.exceptions.RequestException, KeyError, ValueError):
        answer = "Something went wrong while talking to the AI."
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

    st.rerun()

if st.button("🧹 Clear Chat"):
    st.session_state.messages = []
    st.rerun()

st.divider()

# ---------------------------------
# RAINBOW ICE CREAM ANIMATION
# ---------------------------------

st.subheader("🌈 Rainbow Magic")

if st.button(
    "🌈 Start / Stop Rainbow Magic"
):
    st.session_state.spinner_on = not st.session_state.spinner_on

if st.session_state.spinner_on:
    st.markdown("""
    <style>
    @keyframes rainbowspin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    @keyframes scoopchange {
        0% { background: #FF1493; }
        20% { background: #FF4500; }
        40% { background: #FFD700; }
        60% { background: #32CD32; }
        80% { background: #00BFFF; }
        100% { background: #9932CC; }
    }

    .rainbow-ring {
        width: 100px;
        height: 100px;
        border: 10px dashed;
        border-color: #FF1493 #FF4500 #FFD700
                     #32CD32 #00BFFF #9932CC;
        border-radius: 50%;
        animation: rainbowspin 2s linear infinite;
        margin: auto;
    }

    .icecream-scoop {
        width: 65px;
        height: 65px;
        border-radius: 50%;
        animation: scoopchange 3s infinite;
        margin: -80px auto 15px auto;
        position: relative;
    }

    .icecream-cone {
        width: 0;
        height: 0;
        border-left: 30px solid transparent;
        border-right: 30px solid transparent;
        border-top: 65px solid #D99A50;
        margin: auto;
    }
    </style>

    <div style="text-align:center;padding:15px">
        <div class="rainbow-ring"></div>
        <div class="icecream-scoop"></div>
        <div class="icecream-cone"></div>
        <h3>🌈 Icecream Magic! 🍦</h3>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(
        "<h2 style='text-align:center'>🍦 Ready! 🍦</h2>",
        unsafe_allow_html=True
    )

st.divider()

st.markdown(
    "<h4 style='text-align:center'>"
    "Made with love and lots of ice cream! 🍦💗"
    "</h4>",
    unsafe_allow_html=True
)
