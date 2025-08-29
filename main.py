import streamlit as st
import json
import requests
from pathlib import Path

DATA_DIR = Path(__file__).parent
LESSONS_FILE = DATA_DIR / "lessons.json"
QUIZZES_FILE = DATA_DIR / "quizzes.json"

# ---------- Load data ----------
@st.cache_data
def load_lessons():
    with open(LESSONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data
def load_quizzes():
    with open(QUIZZES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

lessons = load_lessons()             # list of lesson dicts
quizzes = load_quizzes()             # list of quiz dicts
lesson_map = {l["lesson_id"]: l for l in lessons}

# ---------- Session state ----------
if "completed" not in st.session_state:
    st.session_state.completed = set()        # store completed lesson_ids
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []       # list of (user,bot)

# ---------- Layout / Navigation ----------
st.set_page_config(page_title="Lingo Translator", layout="wide")
page = st.sidebar.selectbox("Navigate", ["Home", "Lessons", "Translator", "Quiz", "Chatbot", "Progress", "Export"])

# ---------- Helper: translate (API + fallback) ----------
LOCAL_DICT = {
    "hello": "hallo",
    "good morning": "guten morgen",
    "thank you": "danke",
    "please": "bitte",
    "goodbye": "auf wiedersehen",
    "how are you?": "wie geht's?",
    "i am fine": "mir geht es gut",
    "see you soon": "bis bald",
    "yes": "ja",
    "no": "nein"
}

def translate_text(text: str, target: str = "de") -> str:
    text = text.strip()
    if not text:
        return ""
    # Try LibreTranslate public instance
    try:
        resp = requests.post(
            "https://libretranslate.com/translate",
            json={"q": text, "source": "auto", "target": target, "format": "text"},
            timeout=8
        )
        if resp.ok:
            translated = resp.json().get("translatedText")
            if translated:
                return translated
    except Exception:
        pass
    # Fallback: simple local dictionary
    if target == "de":
        return LOCAL_DICT.get(text.lower(), "Translation not found in local dictionary")
    else:
        rev = {v: k for k, v in LOCAL_DICT.items()}
        return rev.get(text.lower(), "Translation not found in local dictionary")

# ---------- Pages ----------
if page == "Home":
    st.title("🇩🇪 Lingo Translator — Learn German")
    st.write("A lightweight learning app with lessons, translator, quizzes and a chatbot.")
    total = len(lessons)
    completed = len(st.session_state.completed)
    pct = int((completed / total) * 100) if total else 0
    st.metric("Progress", f"{completed}/{total}", delta=f"{pct}%")
    st.progress(pct)
    st.write("**Available lessons**")
    for l in lessons:
        status = "✅ Completed" if l["lesson_id"] in st.session_state.completed else "◻️ Not started"
        st.write(f"**Lesson {l['lesson_id']}** — {l['title']} — *{status}*")
    st.write("---")
    st.info("Tip: Go to the Lessons tab to open a lesson. Mark it complete after practicing.")

# ---------- Lessons page ----------
elif page == "Lessons":
    st.header("📚 Lessons")
    lesson_choices = [f"Lesson {l['lesson_id']}: {l['title']}" for l in lessons]
    sel = st.selectbox("Select a lesson", ["-- choose --"] + lesson_choices)
    if sel and sel != "-- choose --":
        lesson_id = int(sel.split()[1].strip(':'))
        lesson = lesson_map[lesson_id]
        st.subheader(f"Lesson {lesson_id} — {lesson['title']}")
        st.write("Practice these words/phrases:")
        for item in lesson["content"]:
            st.write(f"- **{item['en']}** → *{item['de']}*")
        st.write("")
        if st.button("Mark lesson complete"):
            st.session_state.completed.add(lesson_id)
            st.success("Lesson marked complete ✅")
        if st.button("Open lesson quiz"):
            st.session_state.quiz_for = lesson_id
            st.experimental_rerun()

# ---------- Translator ----------
elif page == "Translator":
    st.header("🔁 Translator")
    text_input = st.text_input("Enter text to translate")
    lang = st.selectbox("Direction", ["English → German", "German → English"])
    target = "de" if lang.startswith("English") else "en"
    if st.button("Translate"):
        if not text_input.strip():
            st.warning("Type something to translate.")
        else:
            with st.spinner("Translating..."):
                out = translate_text(text_input, target)
                st.success(out)
# ---------- quiz ----------
elif page == "Quiz":
    st.header("🧪 Quiz")

    # list of single-question quizzes
    quiz_options = [sq["quiz_id"] for sq in single_quizzes]

    sel_id = st.selectbox("Choose quiz", [None] + quiz_options)

    if sel_id:
        quiz = next(sq for sq in single_quizzes if sq["quiz_id"] == sel_id)
        qdata = quiz["content"][0]

        st.subheader(f"Quiz — Lesson {quiz['lesson_id']} — {sel_id}")

        with st.form("quiz_form"):
            answer = None

            if qdata["type"] == "mcq":
                answer = st.radio(
                    "Choose your answer",
                    qdata["options"],
                    key=f"{sel_id}_mcq"
                )

            elif qdata["type"] == "fill":
                answer = st.text_input("Your answer", key=f"{sel_id}_fill")

            elif qdata["type"] == "truefalse":
                answer = st.selectbox(
                    "True or False?",
                    ["True", "False"],
                    key=f"{sel_id}_tf"
                )

            submitted = st.form_submit_button("Submit Quiz")

        if submitted:
            user_a = str(answer).strip().lower()
            correct_a = str(qdata["answer"]).strip().lower()

            if qdata["type"] == "truefalse":
                correct_a = "true" if qdata["answer"] else "false"

            if user_a == correct_a:
                st.success(f"✅ Correct — {qdata['question']}")
                st.session_state.completed.add(quiz["lesson_id"])
            else:
                st.error(f"❌ Wrong — {qdata['question']}")
                st.info(f"Correct answer: **{qdata['answer']}**")





# ---------- Chatbot ----------
elif page == "Chatbot":
    st.header("🤖 German Chatbot")
    st.write("Simple rule-based chatbot — type in German (e.g., 'hallo', 'danke', 'hilfe').")
    col1, col2 = st.columns([3,1])
    with col1:
        user_msg = st.text_input("You:", key="chat_input")
    with col2:
        if st.button("Send"):
            if user_msg.strip():
                # simple reply logic
                msg = user_msg.lower()
                if "hallo" in msg:
                    reply = "Hallo! Wie geht's?"
                elif "danke" in msg:
                    reply = "Gern geschehen!"
                elif "tschau" in msg or "bye" in msg:
                    reply = "Auf Wiedersehen!"
                elif "hilfe" in msg:
                    reply = "Ich kann dir bei Deutschübungen helfen!"
                else:
                    reply = "Ich verstehe nicht. Bitte versuche es noch einmal."
                st.session_state.chat_history.append(("You", user_msg))
                st.session_state.chat_history.append(("Bot", reply))
                st.experimental_rerun()
    # show chat history
    for who, text in st.session_state.chat_history:
        if who == "You":
            st.markdown(f"**You:** {text}")
        else:
            st.markdown(f"**Bot:** {text}")

# ---------- Progress page ----------
elif page == "Progress":
    st.header("📈 Progress")
    total = len(lessons)
    completed = len(st.session_state.completed)
    pct = int((completed / total) * 100) if total else 0
    st.write(f"Lessons completed: **{completed} / {total}** ({pct}%)")
    st.progress(pct)
    if st.button("Reset progress"):
        st.session_state.completed = set()
        st.success("Progress reset.")

# ---------- Export progress ----------
elif page == "Export":
    st.header("📤 Export / Import Progress")
    # Download completed list as JSON
    progress = {"completed": list(st.session_state.completed)}
    st.download_button("Download progress (JSON)", json.dumps(progress), file_name="progress.json", mime="application/json")
    st.write("---")
    uploaded = st.file_uploader("Upload progress JSON to import", type=["json"])
    if uploaded:
        data = json.load(uploaded)
        comp = data.get("completed", [])
        st.session_state.completed = set(comp)
        st.success("Progress imported.")
