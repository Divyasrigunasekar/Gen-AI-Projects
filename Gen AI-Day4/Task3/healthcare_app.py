import streamlit as st
import os
from dotenv import load_dotenv
from main import run_healthcare_crew

# Load environment variables
load_dotenv()

# App Configuration
st.set_page_config(
    page_title="Hospital Portal: Patient Education Generator",
    page_icon="🏥",
    layout="wide"
)

# Custom CSS for "Hospital Portal" aesthetic (Blues and Whites)
st.markdown("""
    <style>
    .stApp {
        background-color: #F0F4F8; /* Soft light blue/grey background */
    }
    .main-header {
        color: #0A3A69; /* Deep medical blue */
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        text-align: center;
        padding-top: 20px;
        padding-bottom: 5px;
    }
    .sub-header {
        color: #1565C0; /* Primary blue */
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        text-align: center;
        padding-bottom: 20px;
    }
    .stButton>button {
        background-color: #1976D2;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #115293;
        color: white;
    }
    .stSlider > div > div > div > div {
        background-color: #1976D2;
    }
    .card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# UI Elements
st.markdown("<h1 class='main-header'>🏥 General Hospital Staff Portal</h1>", unsafe_allow_html=True)
st.markdown("<h3 class='sub-header'>Patient Education Guide Generator</h3>", unsafe_allow_html=True)

# Layout
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.write("Generate customized, empathetic educational materials for your patients using AI.")
    
    # Topic Input
    topic = st.text_input("Enter Health Condition or Wellness Topic:", placeholder="e.g., Type 2 Diabetes, Hypertension, Stress Management")
    
    # Complexity Slider
    st.write("Select Reading Complexity:")
    selected_complexity = st.select_slider(
        "Low = Simple Words, High = Technical Terms",
        options=["Low", "Medium", "High"],
        value="Medium"
    )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    generate_submit = st.button("Generate Patient Guide", use_container_width=True)

# Execution Logic
if generate_submit:
    if not os.getenv("OPENAI_API_KEY"):
        st.error("Error: OPENAI_API_KEY is not set in the .env file. Please add it and try again.")
    elif not topic:
        st.warning("Please enter a topic to generate a guide.")
    else:
        with st.spinner(f"Agents are currently researching and drafting a guide on '{topic}' at {selected_complexity} complexity..."):
            try:
                # Call CrewAI Process
                final_guide = run_healthcare_crew(topic, selected_complexity)
                
                st.success("Patient Guide Generated Successfully!")
                
                # Display Results
                st.markdown("<h2 style='color:#0A3A69;'>Generated Guide:</h2>", unsafe_allow_html=True)
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown(final_guide)
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Check for output file
                guide_path = os.path.join(os.getcwd(), 'Patient_Guide.md')
                if os.path.exists(guide_path):
                    with open(guide_path, 'r') as f:
                        file_data = f.read()
                    col1_dl, col2_dl, col3_dl = st.columns([1, 2, 1])
                    with col2_dl:
                        st.download_button(
                            label="Download Patient_Guide.md",
                            data=file_data,
                            file_name="Patient_Guide.md",
                            mime="text/markdown",
                            use_container_width=True
                        )
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
