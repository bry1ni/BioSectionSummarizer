from agno.agent import Agent
from agno.tools import tool
from agno.models.mistral import MistralChat
from pydantic import BaseModel, Field

import pandas as pd

from src.utils import load_prompt


df = pd.read_csv("src/terms.csv")
AGENT_INSTRUCTION = load_prompt("src/prompt.md")
mistral = MistralChat(id="mistral-medium-latest")

@tool
def search_for_complexed_terms_definition(terms: list[str]) -> dict:
	"""
	Search for the definition of the terms in csv file.
	Args:
		terms: list of terms to search for
	Returns:
		dict of term definitions
	"""
	print(f"Searching for definitions of the following terms: {terms}")
	term_definitions = {}
	matches = df[df["Term"].isin(terms)]
	for term in terms:
		if term in matches["Term"].values:
			row = matches[matches["Term"] == term].iloc[0]
			term_definitions[term] = row["Definition"]
		else:
			term_definitions[term] = f"Definition not found for term: {term}"
	return term_definitions

class Summary(BaseModel):
	vulgar_summary: str = Field(description="A summary of the section in a way that is easy to understand for a non-expert. Include definitions of complexed terms.")
	technical_summary: str = Field(description="A summary of the section in a way that is easy to understand for an expert. Keep the technical terms.")

def create_bio_section_summarizer(section_content: str):
	bio_section_summarizer = Agent(
	name="BioSectionSummarizer",
	model=mistral,
	description=AGENT_INSTRUCTION.format(section_content=section_content),
    tools=[search_for_complexed_terms_definition],
	response_model=Summary,
    structured_outputs=True,
	markdown=True,
    stream=True
    )
	print(bio_section_summarizer.description)
	return bio_section_summarizer
	
def summarize_section(section_content: str, output_dir: str, target_title: str):
	bio_section_summarizer = create_bio_section_summarizer(section_content)
	response = bio_section_summarizer.run(markdown=True)
	summary = response.content\
	
	vulgar_summary_file = f"{output_dir}/{target_title}_vulgar_summary.md"
	technical_summary_file = f"{output_dir}/{target_title}_technical_summary.md"
	
	with open(vulgar_summary_file, "w", encoding="utf-8") as f:
		f.write(summary.vulgar_summary)
	with open(technical_summary_file, "w", encoding="utf-8") as f:
		f.write(summary.technical_summary)
		
	return vulgar_summary_file, technical_summary_file
	