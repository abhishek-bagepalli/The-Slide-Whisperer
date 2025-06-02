import nest_asyncio
from PIL import Image
import json
import os
from llama_parse import LlamaParse
from llama_index.core import SimpleDirectoryReader
from transformers import CLIPProcessor, CLIPModel
import torch
from dotenv import load_dotenv


load_dotenv()

nest_asyncio.apply()

def rename_image_files(job_id, images_dir="./images"):
    """
    Rename image files by removing the job_id prefix.
    
    Args:
        job_id (str): The job ID to remove from filenames
        images_dir (str): Directory containing the image files
        
    Returns:
        None
    """
    # Iterate through all files in the images directory
    for filename in os.listdir(images_dir):
        # Check if the filename contains the job_id
        if job_id in filename:
            # Create the old and new file paths
            old_path = os.path.join(images_dir, filename)
            new_filename = filename.replace(job_id + "-", "")
            new_path = os.path.join(images_dir, new_filename)
            
            # Rename the file
            os.rename(old_path, new_path)
            print(f"Renamed {filename} to {new_filename}")

    print("Finished renaming all files")

def process_document(file_path, json_output_filename="document_parsed.json", image_download_dir="./images", save_json=True):
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
    
    if save_json:
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
            })

    # Save image metadata to JSON file
    if save_json:
        with open('image_metadata.json', 'w') as f:
            json.dump(image_metadata, f, indent=2)
        
    print('**************************************************')
    print("Image metadata has been saved to image_metadata.json")
    print('**************************************************')
    
    return json_result

def extract_text_and_tables(document_content):
    text = []
    for page in document_content[0]["pages"]:
        for item in page['items']:
            if item['type'] == 'heading':
                text.append(item['value'])
            if item['type'] == 'text':
                text.append(item['value'])
            if item['type'] == 'table':
                text.append(item['rows'])
    return text
