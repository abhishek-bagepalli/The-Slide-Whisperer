import os
import requests
from langchain_community.tools.tavily_search import TavilySearchResults
from dotenv import load_dotenv
import os
import requests
from tavily import TavilyClient
from typing import Optional
from tools import get_best_image, build_image_index
from typing import List, Dict
import requests
from PIL import Image
from io import BytesIO
from tools import get_best_image
from multimodal_rag import build_image_index
import copy
import json
load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")  # Or replace with your string
tavily = TavilyClient(api_key=TAVILY_API_KEY)

# ------------------------------
# 📥 Image Search + Download
# ------------------------------
def search_and_download_image_from_web(
    query: str,
    output_dir: str = "images",
    filename: Optional[str] = None,
    index: int = 0
) -> Optional[str]:
    """
    Search Tavily for an image and download the first result.

    Args:
        query (str): The image search query (e.g., image caption).
        output_dir (str): Directory to save the downloaded image.
        filename (str, optional): Filename for the image (defaults to slugified query).
        index (int): Which image result to download (0 = top result).

    Returns:
        str: Path to the saved image, or None if no image found.
    """
    try:
        print(f"🔍 Searching for image: {query}")
        results = tavily.search(query, include_images=True)

        if not results or not results.get("images"):
            print("⚠️ No images found for this query.")
            return None

        image_url = results["images"][index]
        print(f"📸 Found image URL: {image_url}")

        # Prepare save path
        os.makedirs(output_dir, exist_ok=True)
        safe_filename = filename or f"{query.lower().replace(' ', '_')[:50]}.jpg"
        image_path = safe_filename
        image_path2 = os.path.join(output_dir, safe_filename)

        # Download and save image
        img_data = requests.get(image_url).content
        with open(image_path2, "wb") as f:
            f.write(img_data)

        print(f"✅ Image saved at: {image_path2}")
        return image_path

    except Exception as e:
        print(f"❌ Failed to download image: {e}")
        return None

def update_slide_content(slide_content):    

    image_index = build_image_index("./images")
    used_images = set()

    # Create a deep copy of slide_content to avoid modifying the original
    updated_slide_content = copy.deepcopy(slide_content)

    for slide in updated_slide_content:
        captions = slide['slide_content']['image_caption']
        if not captions:
            continue
            
        for caption in captions:
            # Try to get image from RAG first
            image_path, confidence = get_best_image(caption, image_index)

            # if confidence is less than 0.30, get from web
            if confidence < 0.30:
                image_path = search_and_download_image_from_web(caption)
                
            if image_path:
                used_images.add(image_path)
                # Add image path to slide content
                if 'image_paths' not in slide['slide_content']:
                    slide['slide_content']['image_paths'] = []
                slide['slide_content']['image_paths'].append(image_path)
                print(f"Caption: {caption}")
                print(f"Image path: {image_path}\n")
                print(f"Confidence: {confidence}")

    # Save updated slide content to a new JSON file
    with open("updated_slide_content.json", "w", encoding="utf-8") as f:
        json.dump(updated_slide_content, f, indent=2, ensure_ascii=False)

    return updated_slide_content
