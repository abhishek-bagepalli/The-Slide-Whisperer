from openai import OpenAI
from langchain.tools import tool
import os
import shutil
from multimodal_rag import get_text_embedding, build_image_index
import torch.nn.functional as F
import json
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
import torch
from pptx import Presentation
from pptx.util import Inches, Pt
from llama_parse import LlamaParse
from pdf_parser import rename_image_files
import copy

client = OpenAI()

def clear_images_folder(images_folder="./images"):
    """
    Clear all files in the specified images folder.
    
    Args:
        images_folder (str): Path to the images folder to clear
        
    Returns:
        None
    """
    if os.path.exists(images_folder):
        # Remove all files in the directory
        for filename in os.listdir(images_folder):
            file_path = os.path.join(images_folder, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")
        print("Cleared all files from images folder")
    else:
        print("Images folder does not exist")

def extract_chunks_from_llamaparse(parsed_json, min_length=50):
    sections = []

    for page in parsed_json[0]["pages"]:
        current_title = "Untitled Section"
        buffer = []

        for item in page["items"]:
            if item["type"] == "heading":
                # Save previous chunk if exists
                if buffer:
                    text = " ".join(buffer).strip()
                    if len(text) >= min_length:
                        sections.append({"title": current_title, "text": text})
                    buffer = []
                current_title = item["value"]

            elif item["type"] == "text":
                buffer.append(item["value"])

        # Final chunk on the page
        if buffer:
            text = " ".join(buffer).strip()
            if len(text) >= min_length:
                sections.append({"title": current_title, "text": text})

    return sections

def process_document(file_path, json_output_filename="document_parsed.json", image_download_dir="./images"):
    """
    Process a document to extract text and images.
    
    Args:
        file_path (str): Path to the document to process
        json_output_filename (str): Name of the output JSON file
        image_download_dir (str): Directory to save extracted images
        
    Returns:
        dict: JSON result containing parsed document data
    """

    LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")
    # Initialize the parser with your API key
    parser = LlamaParse(
        api_key=LLAMA_CLOUD_API_KEY,
        verbose=True,
        language="en"
    )
    
    # Parse document and get JSON result
    json_result = parser.get_json_result(file_path)

    # Create a more readable format with indentation
    formatted_json = json.dumps(json_result, indent=2)

    # Write to local file
    with open('document_parsed.json', 'w') as f:
        f.write(formatted_json)

    print('**************************************************')
    print("JSON data has been written to document_parsed.json")
    print('**************************************************')
    
    # Save JSON result
    formatted_json = json.dumps(json_result, indent=2)
    with open('document_parsed.json', 'w') as f:
        f.write(formatted_json)
    
    # Extract images
    parser.get_images(json_result,"./images")

    print('**************************************************')
    print("Images have been extracted and saved to ./images")
    print('**************************************************')

    #Rename images
    rename_image_files(json_result[0]['job_id'])

    #Match images with dimensions and save metadata
    image_metadata = []

    for page in json_result[0]['pages']:
        for img in page['images']:
            width = img['width']
            height = img['height']
            name = img['name']
            original_height = img['original_height']
            original_width = img['original_width']
            image_metadata.append({
                "name": name,
                "width": width,
                "height": height,
                "original_height": original_height,
                "original_width": original_width
            })

    # Save image metadata to JSON file
    with open('image_metadata.json', 'w') as f:
        json.dump(image_metadata, f, indent=2)
    
    print('**************************************************')
    print("Image metadata has been saved to image_metadata.json")
    print('**************************************************')
    
    return json_result

def summarize_text(text, model="gpt-3.5-turbo"):
    client = OpenAI()

    prompt = f"""
    You are a professional presentation writer.

    Summarize the following content into a concise paragraph suitable for one PowerPoint slide.

    Guidelines:
    - No bullet points
    - Maximum 70 words
    - Keep it engaging and easy to read
    - Do not describe visuals yet
    - Assume this is one of many slides in a deck

    Content:
    {text}
    """

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=300,
    )

    return response.choices[0].message.content.strip()
    # return "This is a test"

def get_best_image(text_query, image_index):
    
    query_emb = get_text_embedding(text_query)
    best_score = -1
    best_image = None
    for fname, img_emb in image_index:
        score = F.cosine_similarity(query_emb, img_emb, dim=0).item()
        if score > best_score:
            best_score = score
            best_image = fname
    return best_image, best_score

def get_image_dimensions(image_name):
    """
    Retrieve image dimensions from image_metadata.json
    
        Args:
            image_name (str): Name of the image file
            
        Returns:
            tuple: (width, height) of the image, or None if not found
        """
    try:
        with open('image_metadata.json', 'r') as f:
            metadata = json.load(f)
                
        for img in metadata:
            if img['name'] == image_name:
                print('milgya')
                return img['name'],img['width'], img['height']
                    
        return None
    except FileNotFoundError:
        print("Error: image_metadata.json not found")
        return None
    except json.JSONDecodeError:
        print("Error: Invalid JSON in image_metadata.json")
        return None

def get_all_image_dimensions(images_dir="images"):
    """
    Get dimensions of all images in the images folder
    
    Returns:
        list: List of dictionaries containing image metadata
    """
    import os
    from PIL import Image
    
    image_metadata = []
    
    # Check if images directory exists
    if not os.path.exists(images_dir):
        print(f"Error: {images_dir} directory not found")
        return []
    
    # Iterate through all files in images directory
    for filename in os.listdir(images_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            try:
                # Open image and get dimensions
                with Image.open(os.path.join(images_dir, filename)) as img:
                    width, height = img.size
                    
                    # Store metadata
                    image_metadata.append({
                        'name': filename,
                        'width': width,
                        'height': height
                    })
                    
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
    
    # Save metadata to JSON file
    try:
        with open('image_metadata.json', 'w') as f:
            json.dump(image_metadata, f, indent=2)
        print(f"✅ Saved metadata for {len(image_metadata)} images")
    except Exception as e:
        print(f"Error saving metadata: {str(e)}")
    
    return image_metadata

def update_slide_content_with_dimensions(slide_content):
    """
    Update slide content with image dimensions from image_metadata.json
    
    Args:
        slide_content (list): List of slide content dictionaries
        
    Returns:
        list: Updated slide content with image dimensions
    """
    updated_content = copy.deepcopy(slide_content)
    
    for slide in updated_content:
        if 'slide_content' in slide and 'image_paths' in slide['slide_content']:
            image_paths = slide['slide_content']['image_paths']
            dimensions = []
            
            for img_path in image_paths:
                img_info = get_image_dimensions(img_path)
                if img_info:
                    name, width, height = img_info
                    dimensions.append({
                        'path': img_path,
                        'width': width,
                        'height': height
                    })
            
            slide['slide_content']['image_dimensions'] = dimensions
    
    return updated_content


