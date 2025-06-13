from src.document import parse_document, save_images_and_markdown, get_markdown_outline, get_section_content
from src.agent import create_bio_section_summarizer

if __name__ == "__main__":
    output_dir = "src/output"
    filepath = "src/s12859-025-06144-x.pdf"
    md_content, images_of_pages = parse_document(filepath)
    save_images_and_markdown(filepath, md_content, images_of_pages, output_dir)
    outline = get_markdown_outline(md_content)
    target_title = "Methods"
    section_content = get_section_content(outline, target_title)
    bio_section_summarizer = create_bio_section_summarizer(section_content)
    reponse = bio_section_summarizer.run(
        markdown=True,
        )
    summary = reponse.content
    with open(f"{output_dir}/{target_title}_vulgar_summary.md", "w", encoding="utf-8") as f:
        f.write(summary.vulgar_summary)
    with open(f"{output_dir}/{target_title}_technical_summary.md", "w", encoding="utf-8") as f:
        f.write(summary.technical_summary)