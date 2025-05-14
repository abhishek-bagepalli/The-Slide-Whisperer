# slide_tools.py

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
import os
import json
import datetime

def create_new_presentation():
    """Creates a new presentation with timestamp in filename"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    PPTX_PATH = f"presentation_{timestamp}.pptx"
    prs = Presentation()
    return prs, PPTX_PATH

def save_presentation(prs, path):
    prs.save(path)

def create_slide(prs, spec_arg):
    # Set slide dimensions
    prs.slide_width = Inches(spec_arg['slide_dimensions']['width'])
    prs.slide_height = Inches(spec_arg['slide_dimensions']['height'])
    slide_layout = prs.slide_layouts[5]  # Blank layout
    slide = prs.slides.add_slide(slide_layout)

    title = spec_arg.get("title")
    subtitle = spec_arg.get("subtitle")
    text_items = spec_arg.get("text", [])
    is_bulleted = spec_arg.get("bulleted", False)
    content_font_size = spec_arg.get("content_font_size", 16)

    # Get title and subtitle box specifications
    title_box = spec_arg.get("title_box", {})
    subtitle_box = spec_arg.get("subtitle_box", {})
    
    # Add title with specified formatting
    if title:
        title_shape = slide.shapes.title or slide.shapes.add_textbox(
            Inches(title_box['x']), 
            Inches(title_box['y']), 
            Inches(title_box['width']), 
            Inches(title_box['height'])
        )
        title_shape.text = title
        # Set title font size if specified
        if 'font_size' in title_box:
            for paragraph in title_shape.text_frame.paragraphs:
                paragraph.font.size = Pt(title_box['font_size'])
    
    # Add subtitle with specified formatting
    if subtitle:
        subtitle_shape = slide.shapes.add_textbox(
            Inches(subtitle_box['x']), 
            Inches(subtitle_box['y']), 
            Inches(subtitle_box['width']), 
            Inches(subtitle_box['height'])
        )
        subtitle_shape.text = subtitle
        # Set subtitle font size if specified
        if 'font_size' in subtitle_box:
            for paragraph in subtitle_shape.text_frame.paragraphs:
                paragraph.font.size = Pt(subtitle_box['font_size'])

    # Add text content
    if text_items:
        text_box = spec_arg.get("text_box", {})
        text_padding = text_box.get("padding", 0.2)
        
        x = Inches(text_box.get("x", 0.5) + text_padding)
        y = Inches(text_box.get("y", 1.8) + text_padding)
        w = Inches(text_box.get("width", 4.5) - 2 * text_padding)
        h = Inches(text_box.get("height", 3.5) - 2 * text_padding)
        
        text_shape = slide.shapes.add_textbox(x, y, w, h)
        tf = text_shape.text_frame
        tf.clear()
        
        for i, item in enumerate(text_items):
            p = tf.add_paragraph() if i > 0 else tf.paragraphs[0]
            p.text = item
            if is_bulleted:
                p.level = 0
                p.text = f"• {p.text}"
            p.font.size = Pt(content_font_size)
        tf.word_wrap = True

    # Add images
    image_paths = spec_arg.get("image_paths", [])
    image_boxes = spec_arg.get("image_boxes", [])
    
    # Ensure we have matching image boxes for each image path
    if len(image_boxes) < len(image_paths):
        # Create default image boxes for any missing ones
        default_box = {
            "x": 5.5,
            "y": 1.8,
            "width": 4,
            "height": 4,
            "padding": 0.2
        }
        image_boxes.extend([default_box] * (len(image_paths) - len(image_boxes)))
    
    for img_path, img_box in zip(image_paths, image_boxes):
        # Check if image exists in current directory or images folder
        if not os.path.exists(img_path):
            img_path = os.path.join("images", img_path)
        
        if os.path.exists(img_path):
            try:
                img_padding = img_box.get("padding", 0.2)
                x = Inches(img_box.get("x", 5.5) + img_padding)
                y = Inches(img_box.get("y", 1.8) + img_padding)
                w = Inches(img_box.get("width", 4) - 2 * img_padding)
                h = Inches(img_box.get("height", 4) - 2 * img_padding)
                
                slide.shapes.add_picture(img_path, x, y, width=w, height=h)
                print(f"✅ Added image: {img_path}")
            except Exception as e:
                print(f"⚠️ Error adding image {img_path}: {str(e)}")
        else:
            print(f"⚠️ Image not found: {img_path}")

    return {
        "status": "success",
        "message": "Slide created with layout positioning and formatting.",
        "title": title,
        "slide_number": len(prs.slides)
    }

def add_text_to_slide(prs, slide_number, text):
    slide = prs.slides[slide_number - 1]
    text_box = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(5), Inches(2))
    tf = text_box.text_frame
    tf.text = text
    return {"status": "success", "message": f"Text added to slide {slide_number}."}

def add_image_to_slide(prs, slide_number, image_path):
    slide = prs.slides[slide_number - 1]
    if not os.path.exists(image_path):
        image_path = os.path.join("images", image_path)
    
    if os.path.exists(image_path):
        try:
            slide.shapes.add_picture(image_path, Inches(5), Inches(1.5), width=Inches(4))
            return {"status": "success", "message": f"Image added to slide {slide_number}."}
        except Exception as e:
            return {"status": "error", "message": f"Error adding image: {str(e)}"}
    return {"status": "error", "message": f"Image not found: {image_path}"}

def add_chart_to_slide(prs, slide_number, chart_data_path):
    # Stub - requires COM or external chart rendering for real implementation
    # For now, this just puts a placeholder box
    slide = prs.slides[slide_number - 1]
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(2), Inches(3), Inches(5), Inches(2)
    )
    shape.text = f"[Chart Placeholder from {chart_data_path}]"
    shape.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    return {"status": "success", "message": f"Chart placeholder added to slide {slide_number}."}

