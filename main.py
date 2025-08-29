import streamlit as st
import json
import random

# ---------------- LOAD LESSONS & QUIZZES ----------------
with open("lessons.json", "r", encoding="utf-8") as f:
    lessons = json.load(f)

with open("quizzes.json", "r", encoding="utf-8") as f:
    quizzes = json.load(f)

# ---------------- SESSION STATE SETUP ----------------
if "page" not in st.session_state:
    st.session_state.page = "home"

if "quiz_index" not in st.session_state:
    st.session_state.quiz_index = 0

if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = []

# ---------------- NAVIGATION ----------------
def go_to(page):
    st.session_state.page = page
    if page.startswith("quiz_"):
        st.session_state.quiz_index = 0
        st.session_state.quiz_answers = []

# ---------------- HOME PAGE ----------------
if st.session_state.page == "home":
    st.title("🇩🇪 Lingo Translator")
    st.subheader("Choose what you want to do:")

    if st.button("📚 Open Lessons"):
        go_to("lessons")

    if st.button("📝 Take Quiz 1 (Basic Greetings)"):
        go_to("quiz_1")

    if st.button("📝 Take Quiz 2 (Basic Phrases)"):
        go_to("quiz_2")

# ---------------- LESSONS ----------------
elif st.session_state.page == "lessons":
    st.title("📚 Lessons")

    for lesson in lessons["lessons"]:
        if st.button(lesson["title"]):
            st.subheader(lesson["title"])
            for word in lesson["content"]:
                st.write(f"**{word['german']}** → {word['english']}")

    if st.button("⬅ Back"):
        go_to("home")

# ---------------- QUIZ HANDLER ----------------
elif st.session_state.page.startswith("quiz_"):
    quiz_num = int(st.session_state.page.split("_")[1])
    quiz_data = quizzes[f"quiz{quiz_num}"]

    st.title(f"📝 Quiz {quiz_num}")

    idx = st.session_state.quiz_index
    if idx < len(quiz_data):
        q = quiz_data[idx]
        st.subheader(q["question"])

        choice = st.radio("Choose an answer:", q["options"], key=f"q{idx}")

        if st.button("Submit"):
            if choice == q["answer"]:
                st.success("✅ Correct!")
                st.session_state.quiz_answers.append(True)
            else:
                st.error(f"❌ Wrong! Correct answer: {q['answer']}")
                st.session_state.quiz_answers.append(False)

        if st.session_state.quiz_index < len(quiz_data) - 1:
            if st.button("Next ➡"):
                st.session_state.quiz_index += 1
                st.experimental_rerun()
        else:
            if st.button("Finish ✅"):
                go_to("home")
    else:
        st.success("🎉 Quiz Completed!")
        st.write(f"Your Score: {sum(st.session_state.quiz_answers)} / {len(quiz_data)}")
        if st.button("⬅ Back to Home"):
            go_to("home")
