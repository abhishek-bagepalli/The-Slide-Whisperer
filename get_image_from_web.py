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
    max_attempts: int = 5  # Try up to 5 different images
) -> Optional[str]:
    """
    Search Tavily for an image and download the first working result.

    Args:
        query (str): The image search query (e.g., image caption).
        output_dir (str): Directory to save the downloaded image.
        filename (str, optional): Filename for the image (defaults to slugified query).
        max_attempts (int): Maximum number of different images to try.

    Returns:
        str: Full path to the saved image, or None if no working image found.
    """
    try:
        print(f"🔍 Searching for image: {query}")
        results = tavily.search(query, include_images=True)

        if not results or not results.get("images"):
            print("⚠️ No images found for this query.")
            return None

        # Prepare save path
        os.makedirs(output_dir, exist_ok=True)
        safe_filename = filename or f"{query.lower().replace(' ', '_')[:50]}.jpg"
        image_path = os.path.join(output_dir, safe_filename)

        # Try multiple images until we find one that works
        for i, image_url in enumerate(results["images"][:max_attempts]):
            try:
                print(f"📸 Trying image {i+1}/{max_attempts}: {image_url}")
                
                # Download image
                img_data = requests.get(image_url).content
                
                # Try to open and verify the image
                img = Image.open(BytesIO(img_data))
                
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Save as JPEG
                img.save(image_path, 'JPEG', quality=95)
                print(f"✅ Successfully saved image at: {image_path}")
                return image_path
                
            except Exception as e:
                print(f"⚠️ Failed to process image {i+1}: {str(e)}")
                continue  # Try the next image

        print("❌ Could not find any working images after trying all attempts")
        return None

    except Exception as e:
        print(f"❌ Failed to search for images: {e}")
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
