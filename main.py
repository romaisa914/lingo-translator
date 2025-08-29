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
    st.header("🤖 German Chatbot")
    st.write("Chat with a German language model")

    # Initialize chat history
    if "gpt_chat_history" not in st.session_state:
        st.session_state.gpt_chat_history = []
    if "chat_input_key" not in st.session_state:
        st.session_state.chat_input_key = 0

    # Load model/tokenizer (cached for performance)
    @st.cache_resource
    def load_german_model():
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
            tokenizer = AutoTokenizer.from_pretrained("dbmdz/german-gpt2")
            model = AutoModelForCausalLM.from_pretrained("dbmdz/german-gpt2")
            # Add padding token if it doesn't exist
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            return tokenizer, model, torch
        except Exception as e:
            st.error(f"Error loading model: {e}")
            return None, None, None

    tokenizer, model, torch = load_german_model()

    # Function to clean and filter responses
    def clean_response(response):
        # Remove any code snippets, URLs, or technical content
        import re
        # Remove content between special characters
        response = re.sub(r'[\[\(<].*?[\]\)>]', '', response)
        # Remove URLs
        response = re.sub(r'http\S+', '', response)
        # Remove code-like content
        response = re.sub(r'\b\w+::\w+', '', response)
        response = re.sub(r'\b[A-Z]+\b', '', response)
        # Remove excessive punctuation
        response = re.sub(r'[!?]{2,}', '?', response)
        # Trim and clean up
        response = response.strip()
        if not response or len(response) < 3:
            return "Entschuldigung, ich habe das nicht verstanden. Könnten Sie das anders formulieren?"
        return response

    # Function to generate response
    def chat_german(prompt, chat_history=None, max_length=100):
        if tokenizer is None or model is None or torch is None:
            # Fallback to rule-based responses if model fails
            return get_fallback_response(prompt)
        
        try:
            # Create a proper conversation prompt
            conversation_prompt = "Unterhaltung:\n"
            if chat_history:
                for i, msg in enumerate(chat_history[-4:]):  # Last 4 messages for context
                    if i % 2 == 0:
                        conversation_prompt += f"Mensch: {msg}\n"
                    else:
                        conversation_prompt += f"KI: {msg}\n"
            
            conversation_prompt += f"Mensch: {prompt}\nKI:"
            
            inputs = tokenizer.encode(conversation_prompt, return_tensors="pt")
            
            # Ensure max_length does not exceed model capacity
            max_model_len = model.config.n_positions
            if inputs.shape[1] + max_length > max_model_len:
                max_length = max_model_len - inputs.shape[1] - 1
            
            if max_length <= 0:
                return "Eingabe zu lang. Bitte versuchen Sie eine kürzere Nachricht."
            
            with torch.no_grad():
                outputs = model.generate(
                    inputs,
                    max_length=inputs.shape[1] + max_length,
                    pad_token_id=tokenizer.eos_token_id,
                    do_sample=True,
                    temperature=0.8,
                    top_p=0.9,
                    repetition_penalty=1.2,
                    no_repeat_ngram_size=3
                )
            
            full_response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Extract only the new response part
            response = full_response[len(conversation_prompt):].strip()
            
            # Clean the response
            cleaned_response = clean_response(response)
            
            # If response is still problematic, use fallback
            if len(cleaned_response.split()) < 2 or any(word in cleaned_response.lower() for word in ["http", "www", ".com", ".de"]):
                return get_fallback_response(prompt)
                
            return cleaned_response
            
        except Exception as e:
            return f"Entschuldigung, ich hatte ein Problem: {str(e)}"

    # Fallback rule-based responses
    def get_fallback_response(user_input):
        user_input_lower = user_input.lower()
        
        # Greetings
        if any(word in user_input_lower for word in ["hallo", "hi", "hello", "guten tag", "moin"]):
            return "Hallo! Wie geht es Ihnen heute?"
        
        # How are you
        elif "wie geht" in user_input_lower:
            return "Mir geht es gut, danke der Nachfrage! Und Ihnen?"
        
        # Thanks
        elif any(word in user_input_lower for word in ["danke", "dankeschön", "danke schön", "thanks"]):
            return "Bitte sehr! Gern geschehen."
        
        # Goodbye
        elif any(word in user_input_lower for word in ["tschüss", "auf wiedersehen", "bye", "ciao", "tschau"]):
            return "Auf Wiedersehen! Bis zum nächsten Mal."
        
        # What's your name
        elif any(word in user_input_lower for word in ["wie heißt", "dein name", "wer bist", "name"]):
            return "Ich bin der Deutsch-Lernbot. Ich helfe Ihnen beim Deutschlernen!"
        
        # Help
        elif any(word in user_input_lower for word in ["hilfe", "help", "was kannst"]):
            return "Ich kann mit Ihnen auf Deutsch chatten, um Ihre Sprachkenntnisse zu üben. Probieren Sie doch mal einfache Begrüßungen oder Fragen!"
        
        # Questions about liking
        elif any(word in user_input_lower for word in ["gefall", "magst", "like"]):
            return "Als KI habe ich keine persönlichen Vorlieben, aber ich helfe Ihnen gerne beim Deutschlernen!"
        
        # Default response
        else:
            responses = [
                "Das verstehe ich nicht ganz. Könnten Sie das anders formulieren?",
                "Interessant! Erzählen Sie mir mehr.",
                "Das ist eine gute Übung für mein Deutsch!",
                "Könnten Sie das bitte wiederholen?",
                "Ich lerne noch. Könnten Sie das einfacher sagen?",
                "Entschuldigung, ich bin mir nicht sicher, was Sie meinen.",
                "Das ist eine interessante Frage. Könnten Sie etwas mehr Kontext geben?"
            ]
            import random
            return random.choice(responses)

    # Display chat history
    for idx, msg in enumerate(st.session_state.gpt_chat_history):
        if idx % 2 == 0:
            st.markdown(f"**You:** {msg}")
        else:
            st.markdown(f"**Bot:** {msg}")

    # User input at the bottom - use a form to handle input properly
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
        with st.spinner("Denke nach..."):
            bot_reply = chat_german(user_input, st.session_state.gpt_chat_history)
        st.session_state.gpt_chat_history.append(bot_reply)
        # Increment the key to reset the text input
        st.session_state.chat_input_key += 1
        st.rerun()
    
    if clear_chat:
        st.session_state.gpt_chat_history = []
        st.session_state.chat_input_key += 1
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
