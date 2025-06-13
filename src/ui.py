import streamlit as st
from pathlib import Path
import os
import shutil
from src.document import (
    parse_document,
    save_images_and_markdown,
    get_markdown_outline,
    get_section_content,
    format_and_save_section_content
)
from src.agent import summarize_section

def clean_output_dir(output_dir: str):
    """Clean up the output directory by removing all its contents."""
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

def init_session_state():
    """Initialize session state variables."""
    if 'processed_files' not in st.session_state:
        st.session_state.processed_files = {}  # Store processed file info: {filename: {md_file, outline}}
    if 'selected_section' not in st.session_state:
        st.session_state.selected_section = None
    if 'current_file' not in st.session_state:
        st.session_state.current_file = None
    if 'summary_files' not in st.session_state:
        st.session_state.summary_files = {}
    
    # Clean up output directory at startup
    clean_output_dir("src/output")

def process_uploaded_file(uploaded_file):
    """Process uploaded PDF and save to output directory."""
    output_dir = "src/output"
    os.makedirs(output_dir, exist_ok=True)
    
    if uploaded_file.name in st.session_state.processed_files:
        st.session_state.current_file = uploaded_file.name
        return True
    
    pdf_path = os.path.join(output_dir, uploaded_file.name)
    with open(pdf_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    with st.spinner(f"Processing PDF {uploaded_file.name}..."):
        md_content, images_of_pages = parse_document(pdf_path)

    md_file = save_images_and_markdown(pdf_path, md_content, images_of_pages, output_dir)
    
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    outline = get_markdown_outline(md_content)
    
    st.session_state.processed_files[uploaded_file.name] = {
        'md_file': md_file,
        'outline': outline
    }
    st.session_state.current_file = uploaded_file.name
    
    return True

def display_outline():
    """Display the document outline in the sidebar."""
    st.sidebar.header("Document Outline")
    
    if st.session_state.current_file and st.session_state.current_file in st.session_state.processed_files:
        outline = st.session_state.processed_files[st.session_state.current_file]['outline']
        for idx, header in enumerate(outline):
            # Create a unique key by combining title and index
            button_key = f"{header['title']}_{idx}"
            if st.sidebar.button(header["title"], key=button_key):
                st.session_state.selected_section = header["title"]

def display_section_content():
    """Display the content of the selected section."""
    if not st.session_state.current_file or st.session_state.current_file not in st.session_state.processed_files:
        st.write("Please upload a PDF file first.")
        return
        
    if not st.session_state.selected_section:
        st.write("Select a section from the outline to view its content.")
        return
        
    file_info = st.session_state.processed_files[st.session_state.current_file]
    section = get_section_content(file_info['outline'], st.session_state.selected_section)
    
    if not section["found"]:
        st.write("Section not found.")
        return
        
    md_file = format_and_save_section_content(
        st.session_state.selected_section, 
        section,
        "src/output"
    )
    
    with open(md_file, "r", encoding="utf-8") as f:
        section_content = f.read()
    
    st.header(st.session_state.selected_section)
    st.markdown(section_content)
    
    if st.button("Summarize Section"):
        with st.spinner(f"Summarizing {st.session_state.selected_section} section..."):
            vulgar_file, technical_file = summarize_section(
                section_content=section_content,
                output_dir="src/output",
                target_title=st.session_state.selected_section.replace(" ", "_")
            )
        
        st.session_state.summary_files[st.session_state.selected_section] = {
            "vulgar": vulgar_file,
            "technical": technical_file
        }
        
        st.success("Section summarized successfully!")
        with st.expander("Vulgar Summary"):
            with open(vulgar_file, "r", encoding="utf-8") as f:
                st.markdown(f.read())
        with st.expander("Technical Summary"):
            with open(technical_file, "r", encoding="utf-8") as f:
                st.markdown(f.read())
