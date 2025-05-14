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
from outline_generator import generate_outline

from langchain.agents import Tool
from tools import extract_chunks_from_llamaparse, summarize_text, clear_images_folder
import json
from content_generator import generate_slide_content
from get_image_from_web import update_slide_content
from tools import update_slide_content_with_dimensions, get_all_image_dimensions
from ppt_creator import create_new_presentation, save_presentation, create_slide
from layout_generator import get_slide_layout

def main():
    """
    Main function to generate a presentation from a document.
    Processes the document, generates summaries, creates an outline,
    generates slide content, adds images, and creates the final presentation.
    """
    print("🚀 Starting presentation generation process...")
    
    # Clear images folder before starting
    print("🗑️ Clearing images folder...")
    clear_images_folder()
    
    file_path = "docs/loreal.docx"
    image_folder = "./images"

    # Process the input document
    print("📄 Processing input document...")
    json_result = process_document(file_path)

    # Load and parse the document
    print("📂 Loading parsed document...")
    with open("document_parsed.json", "r", encoding="utf-8") as f:
        parsed = json.load(f)

    # Extract and process sections
    print("📑 Extracting document sections...")
    sections = extract_chunks_from_llamaparse(parsed)

    # Generate summaries for each section
    print("📝 Generating section summaries...")
    slide_summaries = []
    for section in sections:
        summary = summarize_text(section["text"])
        slide_summaries.append({
            "title": section["title"],
            "summary": summary
        })
        print(f"✓ Summarized section: {section['title']}")

    # Generate presentation outline
    print("\n📋 Generating presentation outline...")
    outline = generate_outline(title="L'Oréal", summaries=slide_summaries)
    print("✓ Outline generated successfully")
    
    # Generate slide content
    print("\n🎨 Generating slide content...")
    slide_content = generate_slide_content(outline)
    print("✓ Slide content generated")

    # Update content with images
    print("\n🖼️ Adding images to slides...")
    updated_slide_content = update_slide_content(slide_content)
    get_all_image_dimensions()
    updated_slide_content = update_slide_content_with_dimensions(updated_slide_content)
    print("✓ Images added and dimensions updated")

    # Save updated content
    print("\n💾 Saving updated slide content...")
    with open("updated_slide_content.json", "w", encoding="utf-8") as f:
        json.dump(updated_slide_content, f, indent=2, ensure_ascii=False)
    print("✓ Content saved to updated_slide_content.json")

    # Generate layouts
    print("\n📐 Generating slide layouts...")
    slide_layouts = []
    for slide in updated_slide_content:
        layout = get_slide_layout(slide)
        if layout:
            slide_layouts.append(layout)
    print("✓ Layouts generated")

    # Save layouts
    print("\n💾 Saving slide layouts...")
    with open("slide_layouts.json", "w", encoding="utf-8") as f:
        json.dump(slide_layouts, f, indent=2, ensure_ascii=False)
    print("✓ Layouts saved to slide_layouts.json")

    # Create presentation
    print("\n🎯 Creating presentation...")
    with open("slide_layouts.json", "r") as f:
        slide_specs = json.load(f)

    prs, pptx_path = create_new_presentation()
    
    # Create individual slides
    for spec in slide_specs:
        result = create_slide(prs, spec)
        print(f"✓ Slide created: {result}")

    # Save final presentation
    print("\n💾 Saving final presentation...")
    save_presentation(prs, pptx_path)
    print(f"✅ Presentation successfully saved as: {pptx_path}")
    print("\n🎉 Presentation generation complete!")

if __name__ == "__main__":
    main()