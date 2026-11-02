
import streamlit as st
import requests
from datetime import datetime, timedelta, timezone
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

if "riddle" not in st.session_state:
    st.session_state.riddle = None

# ---------------------------------
# TITLE AND THEME CHOICE
# ---------------------------------

title_col, theme_col = st.columns([3, 1], vertical_alignment="bottom")

with title_col:
    st.title("🍦 ICECREAM BROWSER 🍦")

with theme_col:
    choice = st.selectbox(
        "🎨 Festival theme",
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

h1, h2, h3, h4, p, label, li {{
    color: {theme['text']} !important;
}}

/* Keep the header and chat bar in theme colours, even in dark mode */
header[data-testid="stHeader"],
div[data-testid="stBottom"] > div {{
    background-color: {theme['bg']};
}}

div[data-testid="stChatInput"],
div[data-testid="stChatInput"] > div {{
    background-color: {theme['panel']};
}}

div[data-testid="stChatInput"] textarea {{
    color: {theme['text']};
}}

div[data-baseweb="select"] > div {{
    background-color: {theme['panel']};
    color: {theme['text']};
}}

div[data-testid="stChatMessage"] {{
    background-color: {theme['panel']};
    border-radius: 15px;
    padding: 10px;
}}

/* Big, easy-to-tap tabs */
button[data-baseweb="tab"] p {{
    font-size: 1.15rem;
    font-weight: bold;
}}

div[data-baseweb="tab-highlight"] {{
    background-color: {theme['accent']};
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

.stLinkButton a {{
    background-color: {theme['button2']};
    border: none;
    border-radius: 12px;
}}

.stButton button p,
.stLinkButton a p {{
    color: white !important;
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

# ---------------------------------
# ICECREAM AI
# ---------------------------------


def get_secret(name, default=None):
    # st.secrets raises an error when no secrets are set up at all
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


# Online, the AI uses Google Gemini (key set in Streamlit secrets).
# On your own computer without a key, it falls back to Ollama.
gemini_key = get_secret("GEMINI_API_KEY")
gemini_model = get_secret("GEMINI_MODEL", "gemini-3.5-flash-lite")


def system_prompt():
    # India time (no daylight saving, so a fixed offset is fine)
    today = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    return (
        "You are Icecream AI, a friendly and cheerful helper on the "
        "Icecream Browser website. "
        f"Today is {today.strftime('%A, %d %B %Y')} (India time)."
    )


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
        json={
            "systemInstruction": {"parts": [{"text": system_prompt()}]},
            "contents": contents
        },
        timeout=90
    )
    response.raise_for_status()

    # Gemini sends no text when it decides not to answer a question
    candidates = response.json().get("candidates") or [{}]
    parts = candidates[0].get("content", {}).get("parts", [])
    answer = "".join(
        p.get("text", "") for p in parts if not p.get("thought")
    )
    return answer or (
        "Sorry, I can't answer that one. "
        "Try asking something else! 🍦"
    )


def ask_ollama(messages):
    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": "llama3.2:1b",
            "messages": (
                [{"role": "system", "content": system_prompt()}]
                + messages
            ),
            "stream": False
        },
        timeout=90
    )
    response.raise_for_status()
    return response.json()["message"]["content"]


def get_reply(messages):
    try:
        if gemini_key:
            return ask_gemini(messages)
        return ask_ollama(messages)

    except requests.exceptions.ConnectionError:
        if gemini_key:
            return "I cannot connect to the AI right now. Please try again."
        return (
            "I cannot connect to Ollama. "
            "Please check that it is running."
        )

    except requests.exceptions.HTTPError as error:
        status = error.response.status_code
        if status == 429:
            return (
                "Icecream AI is a bit busy right now. "
                "Please wait a minute and try again."
            )
        if gemini_key and status in (400, 401, 403):
            return (
                "The AI key isn't working. "
                "Please check GEMINI_API_KEY in the app's secrets."
            )
        return "Something went wrong while talking to the AI."

    except requests.exceptions.Timeout:
        return "The AI took too long to answer. Please try again."

    except (requests.exceptions.RequestException,
            KeyError, IndexError, ValueError):
        return "Something went wrong while talking to the AI."


def ask(question):
    st.session_state.messages.append({"role": "user", "content": question})


def google_url(text):
    return "https://www.google.com/search?q=" + quote_plus(text)


# ---------------------------------
# TABS: everything one tap away
# ---------------------------------

search_tab, fun_tab = st.tabs(["🔎 Search & Ask", "🍦 Ice Cream Fun"])

# ---------------------------------
# SEARCH & ASK: question, answer and Google results together
# ---------------------------------

with search_tab:
    messages = st.session_state.messages

    if not messages:
        st.write(
            "Type anything in the box below. Icecream AI answers right "
            "here, and you can open the Google results too. 🍦"
        )
        st.write("Not sure what to ask? Try one of these:")

        starters = [
            "🍨 Tell me a fun fact about ice cream",
            "🪔 Why do we celebrate Diwali?",
            "🧩 Give me an ice cream riddle",
        ]
        for column, starter in zip(st.columns(len(starters)), starters):
            with column:
                if st.button(starter, width="stretch"):
                    ask(starter)
                    st.rerun()

    # The conversation, with a Google button under each answer
    for i, message in enumerate(messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and i > 0:
                st.link_button(
                    "🔎 See Google results",
                    google_url(messages[i - 1]["content"]),
                    key=f"google_{i}"
                )

    # A question without a reply yet gets answered here. This also
    # catches replies cut off by tapping a button while the AI thinks.
    if messages and messages[-1]["role"] == "user":
        with st.chat_message("assistant"):
            with st.spinner("🌈 Icecream AI is thinking..."):
                answer = get_reply(messages)
        messages.append({"role": "assistant", "content": answer})
        st.session_state.scroll_to_answer = True
        st.rerun()

    # The box sits right under the conversation (not pinned to the
    # bottom of the screen), which also works better on phones
    with st.container():
        question = st.chat_input("Search or ask anything...")

    if question:
        ask(question)
        st.rerun()

    if messages and st.button("🧹 Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    # After a new answer, scroll so the latest question is at the top
    # of the screen with its answer right below it
    if st.session_state.pop("scroll_to_answer", False):
        st.iframe(
            f"""
            <script>
            // reply #{len(messages)}
            const doc = window.parent.document;
            const avatars = doc.querySelectorAll(
                '[data-testid="stChatMessageAvatarUser"]'
            );
            const last = avatars[avatars.length - 1];
            if (last) {{
                const q = last.closest('[data-testid="stChatMessage"]');
                // leave room for the header bar at the top
                q.style.scrollMarginTop = "70px";
                setTimeout(() => q.scrollIntoView(
                    {{behavior: "smooth", block: "start"}}
                ), 300);
            }}
            </script>
            """,
            height=1
        )

# ---------------------------------
# ICE CREAM FUN
# ---------------------------------

with fun_tab:
    riddle_col, magic_col = st.columns(2)

    # ICE CREAM RIDDLE
    with riddle_col:
        st.subheader("🧩 Ice Cream Riddle")

        if st.button("🧩 Give me a riddle!"):
            with st.spinner("🍦 Thinking of a tricky one..."):
                st.session_state.riddle = get_reply([{
                    "role": "user",
                    "content": (
                        "Make up one short, fun riddle for kids about "
                        "ice cream or desserts. Reply in exactly this "
                        "format:\nRiddle: <the riddle>\n"
                        "Answer: <the answer>"
                    )
                }])

        riddle = st.session_state.riddle
        if riddle:
            if "Answer:" in riddle:
                text, solution = riddle.split("Answer:", 1)
                st.markdown(
                    "### " + text.replace("Riddle:", "").strip()
                )
                with st.expander("🤔 Show answer"):
                    st.markdown("**" + solution.strip() + "**")
            else:
                st.markdown(riddle)

    # RAINBOW ICE CREAM ANIMATION
    with magic_col:
        st.subheader("🌈 Rainbow Magic")

        if st.button("🌈 Start / Stop Rainbow Magic"):
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
                border-color: #FF1493 #FFD700 #32CD32 #00BFFF;
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
