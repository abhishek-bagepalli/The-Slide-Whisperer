from pydantic import BaseModel, Field
from typing import List
import json


class SlideContent(BaseModel):
    bullets: List[str]
    image_paths: List[str] = Field(default_factory=list)

class SlideContentForLayout(BaseModel):
    section: str
    sub_slide: int
    slide_content: SlideContent

class Layout(BaseModel):
    slide_dimensions: dict
    title_box: dict
    subtitle_box: dict
    bulleted: bool
    content_font_size: int
    text_box: dict
    image_paths: List[str]
    image_boxes: List[dict]
    title: str
    subtitle: str
    text: List[str]

layouts: List[Layout] = []

def generate_layout_for_slide(slide_data: dict) -> dict:
    """Generate layout for a single slide's data"""
    # Default slide dimensions (16:9 aspect ratio)
    slide_dimensions = {
        "width": 10,
        "height": 5.625
    }
    
    # Default title box
    title_box = {
        "x": 0.5,
        "y": 0.5,
        "width": 9,
        "height": 0.5,
        "font_size": 24,
        "padding": 0.1
    }
    
    # Default subtitle box
    subtitle_box = {
        "x": 0.5,
        "y": 1.2,
        "width": 9,
        "height": 0.5,
        "font_size": 18,
        "padding": 0.1
    }
    
    # Default text box
    text_box = {
        "layout": "left",
        "x": 0.5,
        "y": 1.8,
        "width": 4.5,
        "height": 3.5,
        "padding": 0.2
    }
    
    # Create image box if there are images
    image_boxes = []
    if slide_data["slide_content"]["image_paths"]:
        image_boxes.append({
            "layout": "right",
            "x": 5.5,
            "y": 1.8,
            "width": 4.5,
            "height": 3.5,
            "padding": 0.2
        })
    
    return {
        "slide_dimensions": slide_dimensions,
        "title_box": title_box,
        "subtitle_box": subtitle_box,
        "bulleted": True,
        "content_font_size": 16,
        "text_box": text_box,
        "image_paths": slide_data["slide_content"]["image_paths"],
        "image_boxes": image_boxes,
        "title": slide_data["section"],
        "subtitle": f"Sub-slide {slide_data['sub_slide']}",
        "text": slide_data["slide_content"]["bullets"]
    }

def get_slide_layout(slide_content):
    """
    Generate slide layouts based on the content.
    
    Args:
        slide_content (list): List of dictionaries containing slide content
    """
    layouts = []
    
    for slide in slide_content:
        layout = {
            "slide_number": slide.get("slide_number", 1),
            "layout_id": slide.get("layout_id", 1),
            "layout_name": slide.get("layout_name", "Title and content"),
            "title": slide.get("title", ""),
            "content": {
                "bullets": slide.get("content", {}).get("bullets", []),
                "image_path": slide.get("content", {}).get("image_path", ""),
                "speaker_notes": slide.get("content", {}).get("speaker_notes", "")
            }
        }
        layouts.append(layout)
    
    # Save the layouts to a JSON file
    with open("generated_layouts.json", "w") as f:
        json.dump(layouts, f, indent=2)
    
    print("✅ Slide layouts generated and saved to generated_layouts.json")
    return layouts