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

def build_image_index(image_folder):

    print('**************************************************')

    print("Building image index...")

    print('**************************************************')

    index = []
    for fname in sorted(os.listdir(image_folder)):
        if fname.lower().endswith(('.png', '.jpg', '.jpeg')):
            path = os.path.join(image_folder, fname)
            emb = get_image_embedding(path)
            index.append((fname, emb))
    return index