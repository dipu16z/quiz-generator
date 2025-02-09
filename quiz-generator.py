import streamlit as st
import time
import json
import os
import random
from datetime import datetime

# Load questions from JSON files
QUESTION_PATH = "questions/"

# Function to load questions from a JSON file
def load_questions(subject, subsection):
    file_path = os.path.join(QUESTION_PATH, f"{subject}_{subsection}.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return []

# UPSC Subjects and their subsections
UPSC_SUBJECTS = {
    "History": ["Ancient India", "Medieval India", "Modern India", "World History"],
    "Polity": ["Indian Constitution", "Governance", "Political Theories"],
    "Economy": ["Microeconomics", "Macroeconomics", "Banking & Finance"],
    "Geography": ["Physical Geography", "Indian Geography", "World Geography"],
    "Science & Tech": ["Physics", "Biology", "Space Technology"],
    "Current Affairs": ["International Relations", "National Issues", "Economic Developments"]
}

# Function to get random questions
def get_random_questions(subject, subsection, num_questions=25):
    questions = load_questions(subject, subsection)
    return random.sample(questions, min(num_questions, len(questions)))

def conduct_quiz():
    """Runs a UPSC quiz with pre-stored questions in JSON files."""
    st.set_page_config(page_title="UPSC Quiz 🏛️", layout="wide")
    
    st.title("🏛️ UPSC Subject-Specific Quiz")
    st.write("### Test your UPSC preparation with randomly selected MCQs!")
    
    player_name = st.text_input("👤 Enter your name and press Enter:")
    subject = st.selectbox("📚 Select a Subject:", list(UPSC_SUBJECTS.keys()))
    subsection = st.selectbox("📖 Select a Subsection:", UPSC_SUBJECTS[subject])
    num_questions = 25  # Fixed to 25 questions per attempt
    
    if player_name and st.button("🎯 Start Quiz"):
        questions = get_random_questions(subject, subsection, num_questions)
        if not questions:
            st.warning("⚠️ No questions available for this subsection. Please try another.")
            return
        
        total_time = num_questions * 15
        start_time = time.time()
        end_time = start_time + total_time
        st.session_state["submitted"] = False
        
        timer_placeholder = st.empty()
        responses = {}
        
        st.write("### 📖 Answer the following UPSC-level questions:")
        
        for index, q in enumerate(questions, start=1):
            with st.container():
                st.markdown(f"**{index}. {q['question']}**")
                responses[f"q{index}"] = st.radio(
                    "",
                    [f"{chr(65 + i)}. {option}" for i, option in enumerate(q['options'])],
                    index=None,
                    key=f"q{index}",
                    disabled=st.session_state["submitted"]
                )
        
        if not st.session_state["submitted"]:
            submit_clicked = st.button("✅ Submit Quiz")
            
            while time.time() < end_time and not st.session_state["submitted"]:
                remaining_time = int(end_time - time.time())
                minutes, seconds = divmod(remaining_time, 60)
                timer_placeholder.markdown(f"⏳ Time Remaining: {minutes:02}:{seconds:02}")
                time.sleep(1)
                if submit_clicked:
                    st.session_state["submitted"] = True
                    break
            
            if time.time() >= end_time and not st.session_state["submitted"]:
                st.warning("⏳ Time's Up! Auto-submitting your answers.")
                time.sleep(2)
                st.session_state["submitted"] = True
        
        if st.session_state["submitted"]:
            score = 0
            st.write("### 📊 Quiz Results")
            
            for index, q in enumerate(questions, start=1):
                answer = responses[f"q{index}"]
                correct_option = q['answer']
                
                if answer:
                    selected_option = answer[0]
                    if selected_option == correct_option:
                        score += 2
                        st.success(f"✅ {index}. {q['question']} (Correct!)")
                    else:
                        score -= 0.66
                        st.error(f"❌ {index}. {q['question']} (Wrong!)")
                        st.write(f"✔️ Correct Answer: {correct_option}")
                else:
                    st.warning(f"⚠️ {index}. {q['question']} (Unanswered)")
                    st.write(f"✔️ Correct Answer: {correct_option}")
            
            st.write(f"### 🎯 {player_name}, your final score is: **{score}/{num_questions * 2}**")
            
if __name__ == "__main__":
    conduct_quiz()
