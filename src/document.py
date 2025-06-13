import os
from pathlib import Path

from mistralai import DocumentURLChunk, Mistral
from mistralai.models import OCRResponse
from langchain_text_splitters import MarkdownHeaderTextSplitter

import json
import base64
from PIL import Image
import io
import re

MISTRAL_CLIENT= Mistral(api_key=os.getenv("MISTRAL_API_KEY"))


def ocr_to_markdown(ocr_response: OCRResponse) -> str:
    markdowns: list[str] = []
    images = []
    print("Converting OCR response to markdown...")
    for page in ocr_response.pages:
        markdowns.append(page.markdown)
        images.append(page.images)
    
    return "\n\n".join(markdowns), images

def parse_document(filepath: str):
    with open(filepath, "rb") as f:
        pdf_bytes = f.read()
    file_name = Path(filepath).name

    print(f"Uploading file: {file_name}")
    uploaded_file = MISTRAL_CLIENT.files.upload(
        file={
            "file_name": file_name,
            "content": pdf_bytes,
        },
        purpose="ocr",
    )

    signed_url = MISTRAL_CLIENT.files.get_signed_url(file_id=uploaded_file.id, expiry=1)

    print("Processing document with Mistral OCR...")
    pdf_response = MISTRAL_CLIENT.ocr.process(
        document=DocumentURLChunk(document_url=signed_url.url), 
        model="mistral-ocr-latest", 
        include_image_base64=True,
    )
    
    md_content, images = ocr_to_markdown(pdf_response)
    return md_content, images


def save_images_and_markdown(filepath: str, md_content: str, images_of_pages: list, output_dir: str):
    file_name = Path(filepath).name
    file_name = file_name.replace(".pdf", "")
    os.makedirs(output_dir, exist_ok=True)

    md_file = f"{output_dir}/{file_name}.md"

    for images in images_of_pages:
        for image in images:
            image_id = image.id
            base64_str = image.image_base64
            base64_data = re.sub(r'^data:image/.+;base64,', '', base64_str)
            image_bytes = base64.b64decode(base64_data)
            image = Image.open(io.BytesIO(image_bytes))
            image.save(f"{output_dir}/{image_id}", format="JPEG")

    with open(md_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    return md_file

def get_markdown_outline(md_content: str) -> list:
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
        ("####", "Header 4"),
        ("#####", "Header 5"),
        ("######", "Header 6"),
    ]
    splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    sections = splitter.split_text(md_content)
    
    content_by_path = {}
    for section in sections:
        metadata = section.metadata
        path = []
        for i in range(1, 7):
            header_key = f"Header {i}"
            if header_key in metadata:
                path.append(metadata[header_key])
        if path:
            content_by_path[tuple(path)] = section.page_content.strip()
    
    headers = []
    current_path = []
    
    for line in md_content.split('\n'):
        header_match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
        if header_match:
            level = len(header_match.group(1))
            title = header_match.group(2).strip()
            
            while len(current_path) >= level:
                current_path.pop()
            current_path.append(title)
            
            content = content_by_path.get(tuple(current_path), "")
            
            headers.append({
                "level": level,
                "title": title,
                "path": current_path.copy(),
                "content": content
            })
    
    return headers

def get_section_content(headers: list, target_title: str) -> dict:
    """
    Search for a section by title and return its content along with all its subsections.
    
    Args:
        headers (list): List of header dictionaries from get_markdown_outline
        target_title (str): The title to search for
        
    Returns:
        dict: A dictionary containing:
            - 'main_content': The content of the main section
            - 'subsections': A list of dictionaries containing subsection titles and their content
            - 'found': Boolean indicating if the section was found
    """
    result = {
        'main_content': '',
        'subsections': [],
        'found': False
    }
    
    target_index = -1
    target_level = -1
    
    for i, header in enumerate(headers):
        if header["title"].lower() == target_title.lower():
            target_index = i
            target_level = header["level"]
            result['main_content'] = header["content"]
            result['found'] = True
            break
    
    if target_index == -1:
        for i, header in enumerate(headers):
            if target_title.lower() in header["title"].lower():
                target_index = i
                target_level = header["level"]
                result['main_content'] = header["content"]
                result['found'] = True
                break
    
    if target_index != -1:
        for header in headers[target_index + 1:]:
            if header["level"] <= target_level:
                break
            if header["level"] == target_level + 1:
                result['subsections'].append({
                    'title': header["title"],
                    'content': header["content"]
                })
    
    return result

def format_and_save_section_content(target_title: str, section_result: dict, output_dir: str) -> str:
    """
    Format and save section content including subsections to a markdown file.
    
    Args:
        target_title (str): The title of the section
        section_result (dict): Dictionary containing main content and subsections from get_section_content
        output_dir (str): Directory to save the markdown file
        
    Returns:
        str: Path to the saved markdown file
    """
    md_content = f"# {target_title}\n\n"
    md_content += section_result['main_content']
    
    if section_result['subsections']:
        md_content += "\n\n"
        for subsection in section_result['subsections']:
            md_content += f"## {subsection['title']}\n\n"
            md_content += subsection['content']
            md_content += "\n\n"
    
    output_file = f"{output_dir}/{target_title.replace(' ', '_')}.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    return output_file

if __name__ == "__main__":
    output_dir = "src/output"
    filepath = "src/s12859-025-06165-6.pdf"
    
    # Process the document
    # md_content, images_of_pages = parse_document(filepath)
    # save_images_and_markdown(filepath, md_content, images_of_pages, output_dir)
    
    md_content = open(f"{output_dir}/s12859-025-06165-6.md", "r", encoding="utf-8").read()
    outline = get_markdown_outline(md_content)
    for header in outline:
        print(header["title"])
        print(header["level"])
        print("-" * 100)