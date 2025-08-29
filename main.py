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

    # Build label -> id map once
    lesson_labels = [f"Lesson {l['lesson_id']}: {l['title']}" for l in lessons]
    label_to_id = {label: l["lesson_id"] for label, l in zip(lesson_labels, lessons)}

    # If a lesson was chosen from Home, default to it
    default_index = 0
    preselected = st.session_state.get("_selected_lesson")
    if preselected is not None:
        try:
            # find the matching label index (+1 because of the "-- choose --" entry)
            target_label = next(lbl for lbl in lesson_labels
                                if label_to_id[lbl] == preselected)
            default_index = lesson_labels.index(target_label) + 1
        except StopIteration:
            default_index = 0
        finally:
            # clear it after using so it doesn't stick forever
            st.session_state._selected_lesson = None

    # ---- Single lesson view (top) ----
    sel = st.selectbox(
        "Select a lesson",
        ["-- choose --"] + lesson_labels,
        index=default_index
    )

    if sel and sel != "-- choose --":
        lesson_id = label_to_id[sel]
        lesson = lesson_map[lesson_id]

        st.subheader(f"Lesson {lesson_id} — {lesson['title']}")
        st.caption("Practice these words/phrases:")

        # ✅ Show ALL items (no slicing)
        for idx, item in enumerate(lesson.get("content", []), start=1):
            st.write(f"{idx}. **{item['en']}** → *{item['de']}*")

        col1, col2 = st.columns(2)
        if col1.button("Mark lesson complete", key=f"complete_{lesson_id}"):
            st.session_state.completed.add(lesson_id)
            st.success("Lesson marked complete ✅")
        if col2.button("Open lesson quiz", key=f"open_quiz_{lesson_id}"):
            st.session_state.quiz_for = lesson_id
            st.success("Quiz selected — open the Quiz tab.")
            st.experimental_rerun()

    st.markdown("---")

    # ---- All lessons view (expanders) ----
    st.subheader("All lessons")
    for l in lessons:
        with st.expander(f"Lesson {l['lesson_id']}: {l['title']}"):
            # ✅ Show ALL items (no slicing)
            for idx, item in enumerate(l.get("content", []), start=1):
                st.write(f"{idx}. **{item['en']}** → *{item['de']}*")
            c1, c2 = st.columns(2)
            if c1.button("Mark complete", key=f"exp_complete_{l['lesson_id']}"):
                st.session_state.completed.add(l["lesson_id"])
                st.success("Marked complete ✅")
            if c2.button("Open quiz", key=f"exp_open_quiz_{l['lesson_id']}"):
                st.session_state.quiz_for = l["lesson_id"]
                st.success("Quiz selected — open the Quiz tab.")
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

# ---------- Quiz page ----------
elif page == "Quiz":
    import json

    # Load quizzes from JSON file
    with open("quizzes.json", "r", encoding="utf-8") as f:
        quiz_data = json.load(f)

    quizzes = quiz_data["quizzes"]

    st.subheader("📝 Take a Quiz")

    # Create dropdown with all quiz titles (1–20)
    quiz_titles = [f"{q['quiz_id']}. {q['title']}" for q in quizzes]
    selected_quiz = st.selectbox("Choose a quiz:", quiz_titles)

    # Get the selected quiz object
    quiz_id = int(selected_quiz.split(".")[0])  # extract quiz_id
    quiz = next((q for q in quizzes if q["quiz_id"] == quiz_id), None)

    if quiz:
        st.markdown(f"### {quiz['title']}")
        score = 0
        total = len(quiz["questions"])

        for idx, q in enumerate(quiz["questions"], 1):
            st.write(f"**Q{idx}: {q['question']}**")
            answer = st.radio(
                f"Choose your answer for Q{idx}:",
                q["options"],
                key=f"q{quiz_id}_{idx}"
            )
            if st.button(f"Submit Q{idx}", key=f"submit_{quiz_id}_{idx}"):
                if answer == q["answer"]:
                    st.success("✅ Correct!")
                    score += 1
                else:
                    st.error(f"❌ Wrong! Correct answer: {q['answer']}")

        st.info(f"Your final score: {score}/{total}")




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
