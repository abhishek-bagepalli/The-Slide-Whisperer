# slide_tools.py

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
import os

# Create or load a presentation
PPTX_PATH = "output_presentation.pptx"
if os.path.exists(PPTX_PATH):
    prs = Presentation(PPTX_PATH)
else:
    prs = Presentation()

def save_presentation():
    prs.save(PPTX_PATH)

def create_slide(title, text=None, image_path=None, chart_data_path=None):
    slide_layout = prs.slide_layouts[5]  # Blank layout
    slide = prs.slides.add_slide(slide_layout)
    width = prs.slide_width
    height = prs.slide_height

    if title:
        title_shape = slide.shapes.title or slide.shapes.add_textbox(Inches(1), Inches(0.5), width - Inches(2), Inches(1))
        title_shape.text = title

    if text:
        text_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(4), Inches(2))
        tf = text_box.text_frame
        tf.text = text

    if image_path and os.path.exists(image_path):
        slide.shapes.add_picture(image_path, Inches(5), Inches(1.5), width=Inches(4))

    # Chart placeholder (Not implemented)
    # You could parse chart_data_path and add chart using a placeholder or COM automation

    save_presentation()
    return {"status": "success", "slide_number": len(prs.slides), "title": title}

def add_text_to_slide(slide_number, text):
    slide = prs.slides[slide_number - 1]
    text_box = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(5), Inches(2))
    tf = text_box.text_frame
    tf.text = text

    save_presentation()
    return {"status": "success", "message": f"Text added to slide {slide_number}."}

def add_image_to_slide(slide_number, image_path):
    slide = prs.slides[slide_number - 1]
    if os.path.exists(image_path):
        slide.shapes.add_picture(image_path, Inches(5), Inches(1.5), width=Inches(4))
        save_presentation()
        return {"status": "success", "message": f"Image added to slide {slide_number}."}
    return {"status": "error", "message": "Image path not found."}

def add_chart_to_slide(slide_number, chart_data_path):
    # Stub - requires COM or external chart rendering for real implementation
    # For now, this just puts a placeholder box
    slide = prs.slides[slide_number - 1]
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(2), Inches(3), Inches(5), Inches(2)
    )
    shape.text = f"[Chart Placeholder from {chart_data_path}]"
    shape.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

    save_presentation()
    return {"status": "success", "message": f"Chart placeholder added to slide {slide_number}."}
