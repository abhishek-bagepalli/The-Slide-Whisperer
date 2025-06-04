import requests
import os
from PIL import Image
import io
import base64
from typing import List, Tuple

#random change
# Hugging Face API configuration
API_URL = "https://api-inference.huggingface.co/models/openai/clip-vit-base-patch32"
headers = {"Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_KEY')}"}

def get_image_embedding(image_path: str) -> List[float]:
    """
    Get image embedding using Hugging Face Inference API.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        List[float]: 512-dimensional embedding vector
    """
    # Read and encode image
    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode('utf-8')
    
    # Prepare payload for image embedding
    payload = {
        "inputs": {
            "image": image_data
        }
    }
    
    # Make API request
    response = requests.post(API_URL, headers=headers, json=payload)
    response.raise_for_status()  # Raise exception for bad status codes
    
    return response.json()

def get_text_embedding(text: str) -> List[float]:
    """
    Get text embedding using Hugging Face Inference API.
    
    Args:
        text (str): Input text
        
    Returns:
        List[float]: 512-dimensional embedding vector
    """
    # Prepare payload for text embedding
    payload = {
        "inputs": text
    }
    
    # Make API request
    response = requests.post(API_URL, headers=headers, json=payload)
    response.raise_for_status()  # Raise exception for bad status codes
    
    return response.json()

def build_image_index(image_folder: str) -> List[Tuple[str, List[float]]]:
    """
    Build an index of images using Hugging Face Inference API.
    
    Args:
        image_folder (str): Path to folder containing images
        
    Returns:
        List[Tuple[str, List[float]]]: List of (filename, embedding) pairs
    """
    print('**************************************************')
    print("Building image index using Hugging Face API...")
    print('**************************************************')
    
    index = []
    for fname in sorted(os.listdir(image_folder)):
        if fname.lower().endswith(('.png', '.jpg', '.jpeg')):
            path = os.path.join(image_folder, fname)
            try:
                emb = get_image_embedding(path)
                index.append((fname, emb))
            except Exception as e:
                print(f"Error processing {fname}: {str(e)}")
                continue
    
    return index

def find_similar_images(query_text: str, image_index: List[Tuple[str, List[float]]], top_k: int = 5) -> List[str]:
    """
    Find images similar to the query text using Hugging Face Inference API.
    
    Args:
        query_text (str): Text query to find similar images
        image_index (List[Tuple[str, List[float]]]): List of (filename, embedding) pairs
        top_k (int): Number of similar images to return
        
    Returns:
        List[str]: List of filenames of similar images
    """
    # Get query embedding
    query_embedding = get_text_embedding(query_text)
    
    # Calculate similarities and sort
    similarities = []
    for fname, img_embedding in image_index:
        # Calculate cosine similarity
        similarity = cosine_similarity(query_embedding, img_embedding)
        similarities.append((fname, similarity))
    
    # Sort by similarity and return top k
    similarities.sort(key=lambda x: x[1], reverse=True)
    return [fname for fname, _ in similarities[:top_k]]

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1 (List[float]): First vector
        vec2 (List[float]): Second vector
        
    Returns:
        float: Cosine similarity between vectors
    """
    import numpy as np
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)) 