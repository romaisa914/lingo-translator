import streamlit as st
import json

# ------------------ Load Lessons ------------------
with open("lessons.json", "r", encoding="utf-8") as f:
    lessons = json.load(f)

# ------------------ Load Quizzes ------------------
with open("quizzes.json", "r", encoding="utf-8") as f:
    quizzes = json.load(f)

# ------------------ Pages ------------------
def home():
    st.title("🇩🇪 Lingo Translator")
    st.subheader("Learn German with Interactive Lessons & Quizzes")

    st.write("📖 **Lessons Section**")
    if st.button("Open Lessons"):
        st.session_state.page = "lessons"

    st.write("📝 **Quizzes Section**")
    if st.button("Take a Quiz"):
        st.session_state.page = "quizzes"

def lessons_page():
    st.title("📖 Lessons")
    lesson_choice = st.selectbox("Choose a Lesson:", list(lessons.keys()))
    lesson = lessons[lesson_choice]
    st.subheader(lesson["title"])
    for i, item in enumerate(lesson["content"], start=1):
        st.write(f"{i}. {item['german']} → {item['english']}")

    if st.button("⬅️ Back to Home"):
        st.session_state.page = "home"

def quiz_page():
    st.title("📝 German Quizzes")

    quiz_choice = st.selectbox("Choose a Quiz:", list(quizzes.keys()))
    quiz = quizzes[quiz_choice]
    st.subheader(quiz["title"])

    # Session states for quiz progress
    if "current_q" not in st.session_state:
        st.session_state.current_q = 0
        st.session_state.score = 0
        st.session_state.feedback = ""
        st.session_state.selected_quiz = quiz_choice

    # Reset if user changes quiz
    if st.session_state.selected_quiz != quiz_choice:
        st.session_state.current_q = 0
        st.session_state.score = 0
        st.session_state.feedback = ""
        st.session_state.selected_quiz = quiz_choice

    questions = quiz["questions"]
    q_index = st.session_state.current_q

    if q_index < len(questions):
        q = questions[q_index]
        st.write(f"**Q{q_index+1}: {q['question']}**")

        user_answer = st.radio("Select your answer:", q["options"], key=f"q{q_index}")

        if st.button("Submit", key=f"submit{q_index}"):
            if user_answer == q["answer"]:
                st.session_state.score += 1
                st.session_state.feedback = "✅ Correct!"
            else:
                st.session_state.feedback = f"❌ Wrong! Correct answer: {q['answer']}"

        st.write(st.session_state.feedback)

        if st.session_state.feedback:
            if st.button("Next", key=f"next{q_index}"):
                st.session_state.current_q += 1
                st.session_state.feedback = ""
                st.experimental_rerun()
    else:
        st.success(f"🎉 Quiz finished! Your score: {st.session_state.score}/{len(questions)}")
        if st.button("Restart Quiz"):
            st.session_state.current_q = 0
            st.session_state.score = 0
            st.session_state.feedback = ""
            st.experimental_rerun()

    if st.button("⬅️ Back to Home"):
        st.session_state.page = "home"

# ------------------ Main App ------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

if st.session_state.page == "home":
    home()
elif st.session_state.page == "lessons":
    lessons_page()
elif st.session_state.page == "quizzes":
    quiz_page()
