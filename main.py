import warnings
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.tools import Tool
from langchain_core.messages import HumanMessage
import json
from pdf_parser import process_document
from multimodal_rag import build_image_index
from langchain.agents import initialize_agent, AgentType
from outline_generator import generate_outline, pretty_print

from langchain.agents import Tool
from tools import extract_chunks_from_llamaparse, summarize_text, clear_images_folder
import json

def main():
    #Clear images folder
    clear_images_folder()
    
    file_path = "docs/loreal.docx"

    image_folder = "./images"

    json_result = process_document(file_path)

    image_index = build_image_index(image_folder)

    # Load parsed JSON
    with open("document_parsed.json", "r", encoding="utf-8") as f:
        parsed = json.load(f)

    # Extract section chunks
    sections = extract_chunks_from_llamaparse(parsed)


    # issues with summarization
    # pass previous summaries as context to every LLM call.

    slide_summaries = []
    for section in sections:
        summary = summarize_text(section["text"])
        slide_summaries.append({
            "title": section["title"],
            "summary": summary
        })

    print("Generated slide summaries:")
    # print(slide_summaries)

    outline = generate_outline(title="L'Oréal", summaries=slide_summaries)
    print("Generated outline:")
    pretty_print(outline)



if __name__ == "__main__":
    main()
