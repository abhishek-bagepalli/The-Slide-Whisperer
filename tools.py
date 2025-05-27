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
from document_parser import rename_image_files
import copy
from pydantic import BaseModel, Field
from typing import List, Dict

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

# def extract_chunks_from_llamaparse(parsed_json, min_length=50):
#     text_sections = []
#     table_sections = []

#     if not parsed_json or not isinstance(parsed_json, list) or not parsed_json[0].get("pages"):
#         return text_sections, table_sections # Return empty lists if structure is not as expected

#     for page in parsed_json[0]["pages"]:
#         current_title = "Untitled Section"  # Default title for content before any heading
#         buffer = []  # For accumulating text items

#         # Helper function to flush buffered text into a text section
#         def flush_text_buffer():
#             nonlocal buffer # To modify buffer in the outer scope
#             if buffer:
#                 text_content = " ".join(buffer).strip()
#                 if len(text_content) >= min_length:
#                     text_sections.append({"title": current_title, "text": text_content})
#                 buffer = []  # Clear buffer after flushing

#         for item in page["items"]:
#             item_type = item.get("type")

#             if item_type == "heading":
#                 flush_text_buffer()  # Flush any preceding text under the old title
#                 current_title = item.get("value", "Untitled Section") # Update to new title

#             elif item_type == "text":
#                 buffer.append(item.get("value", ""))

#             elif item_type == "table":
#                 flush_text_buffer()  # Flush any preceding text under the current title
                
#                 # Add table as a new table section
#                 table_rows = item.get("rows")
#                 if table_rows: # Ensure there are rows to add
#                     # Tables are added with their associated title.
#                     # The 'text' key for tables will store the rows, similar to original logic but in a separate list.
#                     table_sections.append({"title": current_title, "text": table_rows})
        
#         # After processing all items on a page, flush any remaining text in the buffer
#         flush_text_buffer()
            
#     return text_sections, table_sections

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

class PresentationIdeation(BaseModel):
    detailed_summary: str = Field(description="Detailed summary (at least 300 words) of the content")
    key_visualizations: Dict[str, List[str]] = Field(
        default_factory=lambda: {"charts": [], "generic_images": []},
        description="Dictionary containing lists of suggested visualizations"
    )
    additional_information_needed: Dict[str, List[str]] = Field(
        default_factory=lambda: {"document_queries": [], "external_research_from_web": []},
        description="Dictionary containing document queries and external research needed"
    )

class PresentationSummarizer:
    def __init__(self, model="gpt-3.5-turbo"):
        self.client = OpenAI()
        self.model = model
        self.conversation_history = []
        self.previous_summaries = []
        self.system_prompt = """You are a professional presentation ideator creating a cohesive PowerPoint presentation. 
        You will be given chunks of text from a document. Your job is to ideate on the best way to present the information in a way that is engaging and easy to understand. 

        For each chunk, you should provide a JSON response with the following structure:
        {
            "detailed_summary": "A comprehensive summary of the content that captures all important details and nuances",
            "key_visualizations": {"charts": ["visual1", "visual2", ...], "images": ["visual1", "visual2", ...]},
            "additional_information_needed": {
                "document_queries": ["exact quote or data needed from source", ...],
                "external_research_from_web": ["topic to research", "specific data point to verify", ...]
            }       
        }

        Strict Instructions:
        - Detailed summary should be at least 300 words
        - Detailed summary should contain key data points and dates.
        - Detailed summary should include direct quotes from the document if the chunk contains any.
        - document_queries can be used to get exact quotes or data points from the document.
        - external_research_from_web can be used to get more information from the web.
        - Key visualizations should be relevant to the detailed summary.
        - Key visualizations should be specific to the content. 
        - The name of the suggested vizualization should be descriptive.
        
        Remember: You are creating a single, cohesive presentation, not isolated slides. Think about the key details in the chunk that will be relevant to the presentation, the more details the better. Then think about the key themes conveyed by these details. Then think about how to connect the details and the themes in the a coherent and logical summary."""
        
        # Initialize conversation with system prompt
        self.conversation_history.append({
            "role": "system",
            "content": self.system_prompt
        })

    def summarize_text(self, text, previous_chunk=None):
        """
        Summarizes text while maintaining context from previous summaries and chunks.
        
        Args:
            text (str): The text content to summarize
            previous_chunk (str, optional): The previous chunk of text for additional context
            
        Returns:
            PresentationIdeation: A structured ideation object containing detailed summary, visualizations, and additional information
        """
        # Create context from previous summaries
        # context = ""
        # if self.previous_summaries:
        #     context = "Previous ideations in the presentation:\n"
        #     for i, prev_summary in enumerate(self.previous_summaries, 1):
        #         context += f"{i}. {prev_summary}\n"
        #     context += "\n"

        # Add previous chunk context if available
        chunk_context = ""
        if previous_chunk:
            chunk_context = f"Previous content chunk for context:\n{previous_chunk}\n\n"

        # Add the current text to conversation history
        prompt = f"""
        {chunk_context}
        
        Please provide your ideation in the following JSON format:
        {{
            "detailed_summary": "A comprehensive summary (max 400 words) of the content that captures all important details and nuances",
            "key_visualizations": {{"charts": ["visual1", "visual2", ...], "images": ["visual1", "visual2", ...]}},
            "additional_information_needed": {{
                "document_queries": ["exact quote or data needed from source", ...],
                "external_research_from_web": ["topic to research", "specific data point to verify", ...]
            }}
        }}

        Content to ideate on:
        {text}"""

        self.conversation_history.append({
            "role": "user",
            "content": prompt
        })

        # Get response from model
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.conversation_history,
            temperature=0.3,
            max_tokens=2000,
        )

        # Parse and validate the response
        summary = response.choices[0].message.content.strip()
        try:
            # Extract JSON from the response if it's wrapped in markdown code blocks
            if "```json" in summary:
                summary = summary.split("```json")[1].split("```")[0].strip()
            elif "```" in summary:
                summary = summary.split("```")[1].strip()
            
            # Parse the JSON string into a dictionary
            summary_dict = json.loads(summary)
            
            # Create PresentationIdeation object from dictionary
            ideation = PresentationIdeation(
                detailed_summary=summary_dict["detailed_summary"],
                key_visualizations=summary_dict["key_visualizations"],
                additional_information_needed=summary_dict["additional_information_needed"]
            )
            
            # Add the response to conversation history and previous summaries
            self.previous_summaries.append(summary)
            self.conversation_history.append({
                "role": "assistant",
                "content": summary
            })

            return ideation
        except Exception as e:
            raise ValueError(f"Failed to parse model response as valid ideation: {str(e)}")

    def clear_history(self):
        """Clear the conversation history while maintaining the system prompt."""
        self.conversation_history = [{
            "role": "system",
            "content": self.system_prompt
        }]
        self.previous_summaries = []

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

# def get_image_dimensions(image_name):
#     """
#     Retrieve image dimensions from image_metadata.json
    
#         Args:
#             image_name (str): Name of the image file
            
#         Returns:
#             tuple: (width, height) of the image, or None if not found
#         """
#     try:
#         with open('image_metadata.json', 'r') as f:
#             metadata = json.load(f)
                
#         for img in metadata:
#             if img['name'] == image_name:
#                 print('milgya')
#                 return img['name'],img['width'], img['height']
                    
#         return None
#     except FileNotFoundError:
#         print("Error: image_metadata.json not found")
#         return None
#     except json.JSONDecodeError:
#         print("Error: Invalid JSON in image_metadata.json")
#         return None

# def get_all_image_dimensions(images_dir="images"):
#     """
#     Get dimensions of all images in the images folder
    
#     Returns:
#         list: List of dictionaries containing image metadata
#     """
#     import os
#     from PIL import Image
    
#     image_metadata = []
    
#     # Check if images directory exists
#     if not os.path.exists(images_dir):
#         print(f"Error: {images_dir} directory not found")
#         return []
    
#     # Iterate through all files in images directory
#     for filename in os.listdir(images_dir):
#         if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
#             try:
#                 # Open image and get dimensions
#                 with Image.open(os.path.join(images_dir, filename)) as img:
#                     width, height = img.size
                    
#                     # Store metadata
#                     image_metadata.append({
#                         'name': filename,
#                         'width': width,
#                         'height': height
#                     })
                    
#             except Exception as e:
#                 print(f"Error processing {filename}: {str(e)}")
    
#     # Save metadata to JSON file
#     try:
#         with open('image_metadata.json', 'w') as f:
#             json.dump(image_metadata, f, indent=2)
#         print(f"✅ Saved metadata for {len(image_metadata)} images")
#     except Exception as e:
#         print(f"Error saving metadata: {str(e)}")
    
#     return image_metadata

# def update_slide_content_with_dimensions(slide_content):
#     """
#     Update slide content with image dimensions from image_metadata.json
    
#     Args:
#         slide_content (list): List of slide content dictionaries
        
#     Returns:
#         list: Updated slide content with image dimensions
#     """
#     updated_content = copy.deepcopy(slide_content)
    
#     for slide in updated_content:
#         if 'slide_content' in slide and 'image_paths' in slide['slide_content']:
#             image_paths = slide['slide_content']['image_paths']
#             dimensions = []
            
#             for img_path in image_paths:
#                 img_info = get_image_dimensions(img_path)
#                 if img_info:
#                     name, width, height = img_info
#                     dimensions.append({
#                         'path': img_path,
#                         'width': width,
#                         'height': height
#                     })
            
#             slide['slide_content']['image_dimensions'] = dimensions
    
#     return updated_content

def update_image_dimensions(slide_content):
    """
    Updates the image dimensions for each slide in the slide content.
    
    Args:
        slide_content (list): List of slides containing image paths
        
    Returns:
        list: Updated slide content with image dimensions
    """
    import os
    from PIL import Image
    
    for slide in slide_content:
        if 'slide_content' in slide and 'image_paths' in slide['slide_content']:
            image_dimensions = []
            for image_path in slide['slide_content']['image_paths']:
                try:
                    full_path = os.path.join('images', image_path)
                    with Image.open(full_path) as img:
                        width, height = img.size
                        image_dimensions.append({
                            'path': image_path,
                            'width': width,
                            'height': height
                        })
                except Exception as e:
                    print(f"Error getting dimensions for {image_path}: {str(e)}")
                    image_dimensions.append({
                        'path': image_path,
                        'width': None,
                        'height': None
                    })
            slide['slide_content']['image_dimensions'] = image_dimensions
    
    # Save updated slide_content back to file
    with open('slide_content.json', 'w') as f:
        json.dump(slide_content, f, indent=2)
        
    return slide_content
