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
# ---------- Home page ----------
if page == "Home":
    import json
    import streamlit as st
    from pathlib import Path

    DATA_DIR = Path(__file__).parent
    LESSONS_FILE = DATA_DIR / "lessons.json"

    # Load lessons directly
    with open(LESSONS_FILE, "r", encoding="utf-8") as f:
        lessons = json.load(f)

    # Initialize completed set if not present
    if "completed" not in st.session_state:
        st.session_state.completed = set()

    st.title("🇩🇪 Lingo Translator — Learn German")
    st.write("A lightweight learning app with lessons, translator, quizzes and a chatbot.")

    # Progress
    total = len(lessons)
    completed = len(st.session_state.completed)
    pct = int((completed / total) * 100) if total else 0
    st.metric("Progress", f"{completed}/{total}", delta=f"{pct}%")
    st.progress(pct)

    st.write("**Available lessons**")
    for l in lessons:
        status = "✅ Completed" if l["lesson_id"] in st.session_state.completed else "◻️ Not started"
        st.write(f"**Lesson {l['lesson_id']} — {l['title']}** — *{status}*")

    st.write("---")
    st.info("Tip: Go to the Lessons tab to open a lesson. Mark it complete after practicing.")


# ---------- Lessons page ----------
elif page == "Lessons":
    import json
    import streamlit as st

    # ================== LOAD LESSONS ==================
    with open("lessons.json", "r", encoding="utf-8") as f:
        lessons = json.load(f)   # ✅ load ALL lessons (no slicing)

    # Map lesson_id → lesson for quick lookup
    lesson_map = {l["lesson_id"]: l for l in lessons}

    # ================== SESSION STATE ==================
    if "completed" not in st.session_state:
        st.session_state.completed = set()
    if "quiz_for" not in st.session_state:
        st.session_state.quiz_for = None
    if "_selected_lesson" not in st.session_state:
        st.session_state._selected_lesson = None

    # ================== LESSONS PAGE ==================
    st.header("📚 Lessons")

    # Build lesson labels
    lesson_labels = [f"Lesson {l['lesson_id']}: {l['title']}" for l in lessons]
    label_to_id = {label: l["lesson_id"] for label, l in zip(lesson_labels, lessons)}

    # Handle preselection (from Home if needed)
    default_index = 0
    preselected = st.session_state.get("_selected_lesson")
    if preselected is not None:
        try:
            target_label = next(lbl for lbl in lesson_labels if label_to_id[lbl] == preselected)
            default_index = lesson_labels.index(target_label) + 1
        except StopIteration:
            default_index = 0
        finally:
            st.session_state._selected_lesson = None

    # ---- Single lesson dropdown ----
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

        # ✅ Show ALL items in lesson (no slicing)
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

    # ---- All lessons (expanders) ----
    st.subheader("All lessons")
    for l in lessons:
        with st.expander(f"Lesson {l['lesson_id']}: {l['title']}"):
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
    import requests
    st.header("🔁 Translator")

    # Input text (remember previous input)
    text_input = st.text_input("Enter text to translate", key="translator_input")

    # Direction
    lang = st.selectbox("Direction", ["English → German", "German → English"], key="translator_dir")
    target = "de" if lang.startswith("English") else "en"

    # Translation function using MyMemory API
    def translate_text(text: str, target: str = "de") -> str:
        text = text.strip()
        if not text:
            return ""
        try:
            resp = requests.get(
                "https://api.mymemory.translated.net/get",
                params={"q": text, "langpair": f"en|de" if target=="de" else f"de|en"},
                timeout=8
            )
            data = resp.json()
            translated = data.get("responseData", {}).get("translatedText")
            if translated:
                return translated
        except Exception:
            pass
        return "Translation failed."

    # Button to trigger translation
    if st.button("Translate"):
        if not text_input.strip():
            st.warning("Type something to translate.")
        else:
            with st.spinner("Translating..."):
                translated_text = translate_text(text_input, target)
                # Store in session_state so result persists after rerun
                st.session_state.translated_text = translated_text

    # Show translation if available
    if "translated_text" in st.session_state:
        st.subheader("Translation:")
        st.success(st.session_state.translated_text)


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
# ---------- Chatbot ----------
elif page == "Chatbot":
    import requests
    import streamlit as st

    st.header("🤖 German Chatbot")
    st.write("Chat with a free German AI assistant!")

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Function to send user message to OpenAssistant
    def send_message_to_openassistant(message: str):
        url = "https://api.openassistantgpt.io/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        data = {
            "messages": [{"role": "user", "content": message}],
            "model": "gpt-3.5-turbo",
            "language": "de"
        }
        try:
            response = requests.post(url, json=data, headers=headers, timeout=10)
            response.raise_for_status()
            result = response.json()
            # Safe access
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0].get("message", {}).get("content") or "No response from bot."
            elif "text" in result:
                return result["text"]
            else:
                return str(result)
        except Exception as e:
            return f"Error contacting chatbot API: {e}"

    # Input and button
    user_input = st.text_input("You:", key="chat_input")
    if st.button("Send") and user_input.strip():
        st.session_state.chat_history.append(("You", user_input))
        bot_reply = send_message_to_openassistant(user_input)
        st.session_state.chat_history.append(("Bot", bot_reply))
        st.experimental_rerun()

    # Display chat history
    for sender, message in st.session_state.chat_history:
        if sender == "You":
            st.markdown(f"**You:** {message}")
        else:
            st.markdown(f"**Bot:** {message}")


# ---------- Progress page ----------
# ---------- Progress page ----------
elif page == "Progress":
    import json
    import streamlit as st
    from pathlib import Path

    DATA_DIR = Path(__file__).parent
    LESSONS_FILE = DATA_DIR / "lessons.json"

    # Load lessons directly
    with open(LESSONS_FILE, "r", encoding="utf-8") as f:
        lessons = json.load(f)

    st.header("📈 Your Progress")

    total = len(lessons)  # now 10 lessons
    completed = len(st.session_state.completed)
    pct = int((completed / total) * 100) if total else 0

    st.metric("Lessons completed", f"{completed}/{total}", delta=f"{pct}%")
    st.progress(pct)

    st.markdown("---")
    st.subheader("Lesson Status")

    # Show each lesson and its status
    for l in lessons:
        status = "✅ Completed" if l["lesson_id"] in st.session_state.completed else "◻️ Not started"
        st.write(f"**Lesson {l['lesson_id']}: {l['title']}** — *{status}*")

    st.markdown("---")
    # Reset progress button
    if st.button("Reset progress"):
        st.session_state.completed = set()
        st.success("All lesson progress has been reset.")

    # Mark all lessons complete button
    if st.button("Mark all lessons as completed"):
        st.session_state.completed = {l["lesson_id"] for l in lessons}
        st.success("All lessons marked as completed ✅")



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
