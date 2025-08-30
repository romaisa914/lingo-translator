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

        # Only show "Mark lesson complete" button (quiz button removed)
        if st.button("Mark lesson complete", key=f"complete_{lesson_id}"):
            st.session_state.completed.add(lesson_id)
            st.success("Lesson marked complete ✅")

    st.markdown("---")
    # ---- All lessons (expanders) ----
    st.subheader("All lessons")
    for l in lessons:
        with st.expander(f"Lesson {l['lesson_id']}: {l['title']}"):
            for idx, item in enumerate(l.get("content", []), start=1):
                st.write(f"{idx}. **{item['en']}** → *{item['de']}*")

            # Only show "Mark complete" button (quiz button removed)
            if st.button("Mark complete", key=f"exp_complete_{l['lesson_id']}"):
                st.session_state.completed.add(l["lesson_id"])
                st.success("Marked complete ✅")
                st.rerun()

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
    st.header("🤖 German Chatbot")
    st.write("Chatte mit einem freundlichen deutschen Sprachassistenten")

    # Initialize chat history
    if "gpt_chat_history" not in st.session_state:
        st.session_state.gpt_chat_history = []
    if "chat_input_key" not in st.session_state:
        st.session_state.chat_input_key = 0

    # Comprehensive rule-based responses in German (no external model needed)
    def get_german_response(user_input):
        user_input_lower = user_input.lower()
        
        # Greetings
        if any(word in user_input_lower for word in ["hallo", "hi", "hello", "guten tag", "moin", "guten morgen"]):
            return "Hallo! Wie geht es dir heute?"
        
        # How are you
        elif "wie geht" in user_input_lower:
            return "Mir geht es gut, danke der Nachfrage! Und dir?"
        
        # Thanks
        elif any(word in user_input_lower for word in ["danke", "dankeschön", "danke schön", "thanks", "thank you"]):
            return "Bitte sehr! Gern geschehen."
        
        # Goodbye
        elif any(word in user_input_lower for word in ["tschüss", "auf wiedersehen", "bye", "ciao", "tschau", "goodbye"]):
            return "Auf Wiedersehen! Bis zum nächsten Mal."
        
        # What's your name
        elif any(word in user_input_lower for word in ["wie heißt", "dein name", "wer bist", "name", "what's your name"]):
            return "Ich bin der Deutsch-Lernbot. Ich helfe dir beim Deutschlernen!"
        
        # Help
        elif any(word in user_input_lower for word in ["hilfe", "help", "was kannst", "what can you do"]):
            return "Ich kann mit dir auf Deutsch chatten, um deine Sprachkenntnisse zu üben. Probier doch mal einfache Begrüßungen oder Fragen!"
        
        # Questions about liking
        elif any(word in user_input_lower for word in ["gefall", "magst", "like", "do you like"]):
            return "Als KI habe ich keine persönlichen Vorlieben, aber ich helfe dir gerne beim Deutschlernen!"
        
        # Language questions
        elif any(word in user_input_lower for word in ["welche sprache", "which language", "sprichst du"]):
            return "Ich spreche Deutsch! Lass uns zusammen üben."
        
        # Free time activities
        elif any(word in user_input_lower for word in ["freizeit", "hobby", "hobbies", "was machst du gern", "what do you like to do"]):
            return "In meiner Freizeit helfe ich Menschen, Deutsch zu lernen! Was machst du gerne in deiner Freizeit?"
        
        # History questions (redirect to language learning)
        elif any(word in user_input_lower for word in ["geschichte", "history", "histor", "einstein", "vereinigten königreich", "uk", "british"]):
            return "Das ist ein interessantes Thema! Aber ich bin hier, um dir beim Deutschlernen zu helfen. Können wir stattdessen über etwas sprechen, das mit der deutschen Sprache zu tun hat?"
        
        # Science questions (redirect to language learning)
        elif any(word in user_input_lower for word in ["wissenschaft", "science", "physik", "physic", "biologie", "biology", "chemie", "chemistry"]):
            return "Wissenschaft ist faszinierend! Aber ich spezialisiere mich auf das Deutschlernen. Möchtest du stattdessen deutsche Vokabeln oder Grammatik üben?"
        
        # Language practice requests
        elif any(word in user_input_lower for word in ["üben", "practice", "lernen", "learn", "deutsch", "german"]):
            return "Großartig! Lass uns Deutsch üben. Was möchtest du sagen oder fragen?"
        
        # Questions about meaning
        elif any(word in user_input_lower for word in ["was bedeutet", "what does", "meaning", "bedeutung"]):
            return "Ich kann dir helfen, deutsche Wörter oder Phrasen zu verstehen. Was möchtest du wissen?"
        
        # Common questions
        elif "wie spät" in user_input_lower:
            return "Ich habe keine Uhr, aber ich hoffe, du bist pünktlich!"
        elif "woher komm" in user_input_lower:
            return "Ich komme aus der digitalen Welt des Internets!"
        elif "wie alt" in user_input_lower:
            return "Als KI habe ich kein Alter, aber ich lerne jeden Tag dazu!"
        elif "wo wohn" in user_input_lower:
            return "Ich wohne in der Cloud! 😊"
        elif "was machst" in user_input_lower:
            return "Ich helfe Menschen, Deutsch zu lernen! Und du?"
        
        # Feelings/emotions
        elif any(word in user_input_lower for word in ["glücklich", "happy", "freude", "freut mich"]):
            return "Das freut mich zu hören! 😊"
        elif any(word in user_input_lower for word in ["traurig", "sad", "schlecht", "müde", "tired"]):
            return "Das tut mir leid. Kann ich dir irgendwie helfen?"
        elif any(word in user_input_lower for word in ["hungrig", "hungry", "durstig", "thirsty"]):
            return "Vielleicht solltest du etwas essen oder trinken! 🍎🥤"
        
        # Language questions
        elif any(word in user_input_lower for word in ["wie sagt man", "how do you say"]):
            return "Ich kann dir helfen, Wörter zu übersetzen! Was möchtest du wissen?"
        elif "deutsch ist schwer" in user_input_lower:
            return "Deutsch kann am Anfang schwierig sein, aber mit Übung wird es besser! Du schaffst das! 💪"
        elif any(word in user_input_lower for word in ["leicht", "easy", "einfach"]):
            return "Das ist toll! Deutsch macht Spaß, nicht wahr?"
        
        # Default responses based on input content
        elif any(word in user_input_lower for word in ["warum", "why", "wieso"]):
            return "Das ist eine gute Frage! Was denkst du denn?"
        elif any(word in user_input_lower for word in ["wann", "when"]):
            return "Die Zeit ist relativ! Aber lass uns lieber Deutsch üben. 😊"
        elif any(word in user_input_lower for word in ["wo", "where"]):
            return "Überall dort, wo Menschen Deutsch lernen wollen!"
        elif any(word in user_input_lower for word in ["wie", "how"]):
            return "Indem ich dir helfe, Deutsch zu üben! Probier es doch mal."
        
        # Default responses based on input length
        else:
            word_count = len(user_input.split())
            if word_count <= 2:
                responses = [
                    "Könntest du das etwas ausführlicher sagen?",
                    "Interessant! Erzähl mir mehr dazu.",
                    "Das verstehe ich nicht ganz. Könntest du es anders formulieren?",
                    "Klingt spannend! Was meinst du genau?",
                    "Das ist kurz und knapp! Magst du mehr dazu erzählen?"
                ]
            elif word_count <= 5:
                responses = [
                    "Das ist eine gute Übung! Lass uns weiter auf Deutsch sprechen.",
                    "Verstanden! Was möchtest du als nächstes sagen?",
                    "Gut gemacht! Möchtest du noch mehr üben?",
                    "Interessant! Lass uns darüber auf Deutsch sprechen.",
                    "Das habe ich verstanden. Was ist deine nächste Frage?"
                ]
            else:
                responses = [
                    "Danke für die ausführliche Nachricht! Lass uns auf Deutsch weitermachen.",
                    "Ich verstehe. Was möchtest du als nächstes besprechen?",
                    "Interessant! Erzähl mir mehr darüber.",
                    "Das ist eine gute Übung für dein Deutsch! Weiter so!",
                    "Vielen Dank für deine Nachricht! Lass uns auf Deutsch chatten."
                ]
            
            import random
            return random.choice(responses)

    # Display chat history
    for idx, msg in enumerate(st.session_state.gpt_chat_history):
        if idx % 2 == 0:
            st.markdown(f"**You:** {msg}")
        else:
            st.markdown(f"**Bot:** {msg}")

    # User input at the bottom
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("You:", key=f"chat_input_{st.session_state.chat_input_key}")
        col1, col2 = st.columns([4, 1])
        with col1:
            submitted = st.form_submit_button("Send")
        with col2:
            clear_chat = st.form_submit_button("Clear Chat")
    
    if submitted and user_input.strip():
        # Append user message
        st.session_state.gpt_chat_history.append(user_input)
        # Generate bot reply
        bot_reply = get_german_response(user_input)
        st.session_state.gpt_chat_history.append(bot_reply)
        # Increment the key to reset the text input
        st.session_state.chat_input_key += 1
        st.rerun()
    
    if clear_chat:
        st.session_state.gpt_chat_history = []
        st.session_state.chat_input_key += 1
        st.rerun()

    # Add some conversation starters
    st.write("---")
    st.write("**Konversationsstarter:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Hallo! Wie geht's?"):
            st.session_state.gpt_chat_history.append("Hallo! Wie geht's?")
            st.session_state.gpt_chat_history.append("Hallo! Mir geht es gut, danke! Und dir?")
            st.rerun()
    with col2:
        if st.button("Was machst du?"):
            st.session_state.gpt_chat_history.append("Was machst du?")
            st.session_state.gpt_chat_history.append("Ich helfe Menschen, Deutsch zu lernen! Und du?")
            st.rerun()
    with col3:
        if st.button("Danke für die Hilfe"):
            st.session_state.gpt_chat_history.append("Danke für die Hilfe")
            st.session_state.gpt_chat_history.append("Gern geschehen! Viel Erfolg beim Deutschlernen!")
            st.rerun()

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



# ---------- Export / Import Progress ----------
elif page == "Export":
    st.header("📤 Export / Import Progress")
    
    # Export section
    st.subheader("Export Your Progress")
    st.write("Download your learning progress to backup or transfer it to another device.")
    
    # Create progress data with additional metadata
    import datetime
    progress = {
        "version": "1.0",
        "export_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_lessons": len(lessons),
        "completed_lessons": len(st.session_state.completed),
        "completed": list(st.session_state.completed)
    }
    
    # Download button
    st.download_button(
        "📥 Download Progress (JSON)", 
        json.dumps(progress, indent=2, ensure_ascii=False), 
        file_name=f"german_learning_progress_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 
        mime="application/json",
        help="Download your complete learning progress as a JSON file"
    )
    
    # Display current progress stats
    st.write("---")
    st.subheader("Current Progress Overview")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Lessons", len(lessons))
    
    with col2:
        st.metric("Completed", len(st.session_state.completed))
    
    with col3:
        completion_rate = (len(st.session_state.completed) / len(lessons)) * 100 if lessons else 0
        st.metric("Completion Rate", f"{completion_rate:.1f}%")
    
    # Show completed lessons with names
    if st.session_state.completed:
        st.write("**Completed Lessons:**")
        for lesson_id in sorted(st.session_state.completed):
            lesson = next((l for l in lessons if l["lesson_id"] == lesson_id), None)
            if lesson:
                st.write(f"✅ Lesson {lesson_id}: {lesson['title']}")
    else:
        st.info("No lessons completed yet. Complete some lessons to see your progress here!")
    
    st.write("---")
    
    # Import section
    st.subheader("Import Progress")
    st.write("Upload a previously exported progress file to restore your learning progress.")
    
    uploaded = st.file_uploader(
        "Choose a progress JSON file", 
        type=["json"],
        help="Select a progress.json file that you previously exported from this app"
    )
    
    if uploaded:
        try:
            # Read and parse the uploaded file
            data = json.load(uploaded)
            
            # Validate the file structure
            if "completed" not in data:
                st.error("❌ Invalid progress file: 'completed' field not found.")
            elif not isinstance(data["completed"], list):
                st.error("❌ Invalid progress file: 'completed' should be a list.")
            else:
                # Validate each lesson ID exists
                valid_lesson_ids = [l["lesson_id"] for l in lessons]
                invalid_lessons = [lesson_id for lesson_id in data["completed"] 
                                  if lesson_id not in valid_lesson_ids]
                
                if invalid_lessons:
                    st.warning(f"⚠️ File contains invalid lesson IDs: {invalid_lessons}. These will be ignored.")
                    # Only keep valid lesson IDs
                    valid_lessons = [lesson_id for lesson_id in data["completed"] 
                                    if lesson_id in valid_lesson_ids]
                    st.session_state.completed = set(valid_lessons)
                else:
                    st.session_state.completed = set(data["completed"])
                
                # Show import results
                st.success("✅ Progress imported successfully!")
                
                # Show import statistics
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"**Lessons imported:** {len(st.session_state.completed)}")
                with col2:
                    st.info(f"**Total available:** {len(lessons)}")
                
                # Show what was imported
                if st.session_state.completed:
                    st.write("**Imported lessons:**")
                    for lesson_id in sorted(st.session_state.completed):
                        lesson = next((l for l in lessons if l["lesson_id"] == lesson_id), None)
                        if lesson:
                            st.write(f"📘 Lesson {lesson_id}: {lesson['title']}")
                
                # Force a rerun to update the UI everywhere
                st.rerun()
                
        except json.JSONDecodeError:
            st.error("❌ Error: The uploaded file is not a valid JSON file.")
        except Exception as e:
            st.error(f"❌ An unexpected error occurred: {str(e)}")
    
    # Reset progress option (with confirmation)
    st.write("---")
    st.subheader("Reset Progress")
    
    if st.button("🔄 Reset All Progress", help="Clear all your completed lessons"):
        if st.session_state.completed:
            # Confirm reset
            if st.checkbox("I understand this will delete all my progress permanently"):
                if st.button("Confirm Reset"):
                    st.session_state.completed = set()
                    st.success("✅ All progress has been reset!")
                    st.rerun()
        else:
            st.info("No progress to reset. You haven't completed any lessons yet.")
