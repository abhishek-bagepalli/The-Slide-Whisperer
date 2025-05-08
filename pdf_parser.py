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

    # image_index = []
    # for image_doc in image_documents:
    #     image_path = image_doc.metadata.get("file_path")
    #     if image_path:
    #         try:
    #             image = Image.open(image_path).convert("RGB")
    #             inputs = processor(images=image, return_tensors="pt")
    #             with torch.no_grad():
    #                 embeddings = model.get_image_features(**inputs)
    #             image_index.append((image_path, embeddings[0]))
    #         except Exception as e:
    #             print(f"Error processing image {image_path}: {e}")
    
    return json_result
