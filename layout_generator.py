from openai import OpenAI
import json
from tools import get_image_dimensions

def get_slide_layout(slide_content):
    client = OpenAI()
    
    # Check if slide has images
    has_images = bool(slide_content['slide_content'].get('image_paths', []))
    
    prompt = f"""
    You are a professional presentation designer. Design a layout for this slide content. ENSURE THERE IS NO OVERLAP OF TEXT AND IMAGES.
    
    Guidelines:
    - Create a balanced layout that emphasizes key points
    - Position text and images strategically
    - Use appropriate font sizes (12-24)
    - Consider visual hierarchy
    - Ensure readability
    - {'Maintain image aspect ratio' if has_images else 'Center text in the slide since there are no images'}
    - Standard PowerPoint slide dimensions are (10x5.625 inches)
    - Ensure the text does not overflow the slide.
    
    Slide Content:
    Section: {slide_content['section']}
    Sub-slide: {slide_content['sub_slide']}
    Bullets: {slide_content['slide_content']['bullets']}
    {f"Image Caption: {slide_content['slide_content'].get('image_caption', [])}" if has_images else ""}
    {f"Image Paths: {slide_content['slide_content'].get('image_paths', [])}" if has_images else ""}
    {f"Image Dimensions: {slide_content['slide_content'].get('image_dimensions', [])}" if has_images else ""}
    
    Return the layout in this JSON format:
    {{
        "slide_dimensions": {{
            "width": 10,
            "height": 5.625
        }},
        "title_box": {{
            "x": number,
            "y": number,
            "width": number,
            "height": number,
            "font_size": number,
            "padding": number
        }},
        "subtitle_box": {{
            "x": number,
            "y": number,
            "width": number,
            "height": number,
            "font_size": number,
            "padding": number
        }},
        "bulleted": boolean,
        "content_font_size": number,
        "text_box": {{
            "layout": "left/right/top/bottom",
            "x": number,
            "y": number,
            "width": number,
            "height": number,
            "padding": number
        }},
        "image_paths": ["string"],
        "image_boxes": [
            {{
                "layout": "left/right/top/bottom",
                "x": number,
                "y": number,
                "width": number,
                "height": number,
                "padding": number
            }}
        ]
    }}
    """
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1000,
    )
    
    try:
        layout = json.loads(response.choices[0].message.content.strip())
        # Add title and text from slide_content
        layout["title"] = slide_content['section']
        layout["subtitle"] = f"Sub-slide {slide_content['sub_slide']}" if slide_content['sub_slide'] > 1 else ""
        layout["text"] = slide_content['slide_content']['bullets']
        return layout
    except json.JSONDecodeError:
        print(f"Error parsing layout for slide {slide_content['section']} {slide_content['sub_slide']}")
        return None


