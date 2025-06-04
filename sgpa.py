import streamlit as st

# Title
st.set_page_config(page_title="SGPA Calculator", layout="centered")
st.title("📚 SGPA Calculator")

# Subject names and credit mapping (only non-zero credits included)
subjects = {
    "Deep Learning Techniques": 3.0,
    "Soft Computing": 3.0,
    "Software Project Management": 3.0,
    "Deep Learning Lab": 1.5,
    "Soft Computing Lab": 1.5,
    "AI & Neural Networks Lab": 1.5,
    "Digital Marketing": 3.0,
    "Design & Analysis of Algorithms": 3.0,
    "English Employability Skills": 2.0
}

# UI Input form
with st.form("sgpa_form"):
    st.markdown("### 📥 Enter your grade points (0 - 10):")
    grade_inputs = {}
    for subject, credit in subjects.items():
        grade = st.number_input(subject, min_value=0.0, max_value=10.0, step=0.1, format="%.1f", key=subject)
        grade_inputs[subject] = grade
    submitted = st.form_submit_button("✅ Check SGPA")

# Calculation logic
if submitted:
    try:
        total_weighted = sum(grade_inputs[sub] * credit for sub, credit in subjects.items())
        total_credits = sum(subjects.values())
        sgpa = total_weighted / total_credits
        st.success(f"🎯 Your SGPA is: **{sgpa:.2f}**")
    except Exception as e:
        st.error("⚠️ An error occurred. Please check your inputs.")
