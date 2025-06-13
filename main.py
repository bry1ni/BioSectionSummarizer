import streamlit as st
from src.ui import init_session_state, process_uploaded_file, display_outline, display_section_content

def main():
    st.set_page_config(
        page_title="BioSectionSummarizer",
        page_icon="📚",
        layout="wide"
    )
    
    st.title("BioSectionSummarizer")
    
    init_session_state()
    
    uploaded_file = st.file_uploader("Upload a PDF file", type=['pdf'])
    
    if uploaded_file is not None:
        if uploaded_file.name != st.session_state.current_file:
            if process_uploaded_file(uploaded_file):
                st.success("PDF processed successfully!")
            else:
                st.error("Error processing PDF file.")
        
        display_outline()
        display_section_content()

if __name__ == "__main__":
    main()
