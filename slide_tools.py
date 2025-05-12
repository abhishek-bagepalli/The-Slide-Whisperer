# slide_tools.py

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
import os
import json

# Create or load a presentation
PPTX_PATH = "loreal_presentation_v1.pptx"
if os.path.exists(PPTX_PATH):
    prs = Presentation(PPTX_PATH)
else:
    prs = Presentation()

SLIDE_WIDTH = prs.slide_width.inches
SLIDE_HEIGHT = prs.slide_height.inches

def save_presentation():
    prs.save(PPTX_PATH)

def create_slide(spec_arg):
    prs.slide_height = Inches(spec_arg['slide_dimensions']['width'])
    prs.slide_height = Inches(spec_arg['slide_dimensions']['height'])
    slide_layout = prs.slide_layouts[5]  # Blank layout
    slide = prs.slides.add_slide(slide_layout)

    title = spec_arg.get("title")
    subtitle = spec_arg.get("subtitle")
    text_items = spec_arg.get("text", [])
    is_bulleted = spec_arg.get("bulleted", False)
    font_size = spec_arg.get("font_size", 24)

    text_box = spec_arg.get("text_box", {})
    image_path = spec_arg.get("image_path")
    image_box = spec_arg.get("image_box", {})

    padding = 0.2  # default padding
    text_padding = text_box.get("padding", padding)
    image_padding = image_box.get("padding", padding)

    title_box = spec_arg.get("title_box", {})
    subtitle_box = spec_arg.get("subtitle_box", {})
    title_padding = 0.2

    if title:
        title_shape = slide.shapes.title or slide.shapes.add_textbox(Inches(title_box['x']), Inches(title_box['y']), Inches(title_box['width']), Inches(title_box['height']))
        title_shape.text = title
    
    if subtitle:
        subtitle_shape = slide.shapes.add_textbox(Inches(subtitle_box['x']), Inches(subtitle_box['y']), Inches(subtitle_box['width']), Inches(subtitle_box['height']))
        subtitle_shape.text = subtitle

    if text_items:
        x = Inches(text_box.get("x") + text_padding)
        y = Inches(text_box.get("y") + text_padding)
        w = Inches(text_box.get("width") - 2 * text_padding)
        h = Inches(text_box.get("height") - 2 * text_padding)
        text_shape = slide.shapes.add_textbox(x, y, w, h)

        # estimated_line_height = font_size * 1.2 / 72  # in inches
        # total_estimated_height = estimated_line_height * len(text_items)

        # if total_estimated_height > h.inches:
        #     w = w + 0.5

        tf = text_shape.text_frame
        tf.clear()
        for i, item in enumerate(text_items):
            p = tf.add_paragraph() if i > 0 else tf.paragraphs[0]
            p.text = item
            if is_bulleted:
                p.level = 0
                p.text = f"• {p.text}"
            p.font.size = Pt(font_size)
        tf.word_wrap = True

    if image_path and os.path.exists(image_path):
        x = Inches(image_box.get("x") + image_padding)
        y = Inches(image_box.get("y") + image_padding)
        w = Inches(image_box.get("width") - 2 * image_padding)
        h = Inches(image_box.get("height") - 2 * image_padding)
        slide.shapes.add_picture(image_path, x, y, width=w, height=h)

    save_presentation()
    return {
        "status": "success",
        "message": "Slide created with layout positioning and formatting.",
        "title": title,
        "slide_number": len(prs.slides)
    }


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


with open("slide_layouts.json", "r") as f:
    slide_specs = json.load(f)

print(slide_specs)

for spec in slide_specs:
    result = create_slide(spec)
    print(f"✅ Slide created: {result}")