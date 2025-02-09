import streamlit as st
import time
import json
import os
import hashlib
import requests
from datetime import datetime, timedelta

# Securely load Hugging Face API Key from environment variable or Streamlit secrets
api_key = os.getenv("HUGGINGFACE_API_KEY") or st.secrets.get("HUGGINGFACE_API_KEY")
if not api_key:
    st.error("⚠️ Hugging Face API Key is missing! Set it in environment variables or Streamlit secrets.")
    st.stop()

# Store the question count limit per day
if "question_count" not in st.session_state:
    st.session_state["question_count"] = 0
if "last_reset" not in st.session_state:
    st.session_state["last_reset"] = datetime.now().strftime("%Y-%m-%d")

def reset_question_limit():
    """Resets the question count every 24 hours."""
    current_date = datetime.now().strftime("%Y-%m-%d")
    if st.session_state["last_reset"] != current_date:
        st.session_state["question_count"] = 0
        st.session_state["last_reset"] = current_date

def generate_questions(topic, num_questions):
    """Generates multiple-choice questions related to UPSC using Hugging Face's API."""
    reset_question_limit()
    if st.session_state["question_count"] + num_questions > 300:
        st.error("⚠️ Daily limit reached! You can generate only 300 questions per day. Try again tomorrow.")
        return []
    
    model = "bigscience/bloom-1b7"
    api_url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {api_key}"}
    prompt = f"Generate {num_questions} UPSC-level multiple-choice questions on {topic}. The questions should have 4 options and one correct answer. Format the output as JSON with fields: question, options, answer (A/B/C/D)."
    
    try:
        response = requests.post(api_url, headers=headers, json={"inputs": prompt})
        if response.status_code != 200:
            st.error(f"⚠️ Hugging Face API request failed. Status code: {response.status_code}")
            return []
        
        response_json = response.json()
        if not response_json:
            st.error("⚠️ Received an empty response from Hugging Face API. Please try again later.")
            return []
        
        if isinstance(response_json, list) and len(response_json) > 0:
            generated_text = response_json[0].get("generated_text", "")
        elif isinstance(response_json, dict):
            generated_text = response_json.get("generated_text", "")
        else:
            st.error("⚠️ Unexpected response format from Hugging Face API.")
            return []
        
        if generated_text:
            try:
                questions = json.loads(generated_text)
                st.session_state["question_count"] += num_questions
                return questions
            except json.JSONDecodeError:
                st.error("⚠️ Error decoding JSON response. The API may not have returned structured data.")
                return []
        else:
            st.error("⚠️ No questions generated. Please try again later.")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"⚠️ API request error: {e}")
        return []

def conduct_quiz():
    """Runs an AI-generated interactive UPSC quiz using Streamlit."""
    st.set_page_config(page_title="UPSC AI Quiz 🏛️", layout="wide")
    
    st.title("🏛️ UPSC AI-Generated Quiz")
    st.write("### Test your UPSC preparation with AI-generated MCQs!")
    
    player_name = st.text_input("👤 Enter your name and press Enter:")
    topic = st.text_input("📚 Enter your UPSC topic (e.g., History, Polity, Economy, Geography, Science & Tech, Current Affairs):")
    num_questions = st.slider("🔢 Select the number of questions:", 10, 50, 10)
    
    reset_question_limit()
    st.write(f"📊 Questions generated today: {st.session_state['question_count']}/300")
    
    if player_name and topic and st.button("🎯 Start Quiz"):
        questions = generate_questions(topic, num_questions)
        if not questions:
            st.warning("⚠️ Unable to generate questions at this time. Please try again later.")
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
