from transformers import CLIPProcessor, CLIPModel
import torch
from PIL import Image
import torch.nn.functional as F
import os

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

def get_image_embedding(image_path):
    image = Image.open(image_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        embeddings = model.get_image_features(**inputs)
    return embeddings[0]  # shape: (512,)

def get_text_embedding(text):
    inputs = processor(text=[text], return_tensors="pt", padding=True)
    with torch.no_grad():
        embeddings = model.get_text_features(**inputs)
    return embeddings[0]

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

def build_image_index(image_folder):
    index = []
    for fname in sorted(os.listdir(image_folder)):
        if fname.lower().endswith(('.png', '.jpg', '.jpeg')):
            path = os.path.join(image_folder, fname)
            emb = get_image_embedding(path)
            index.append((fname, emb))
    return index

def return_best_image(query,image_folder="extracted_images"):
    image_index = build_image_index(image_folder)
    best_image, score = get_best_image(query, image_index)
    return best_image, score

