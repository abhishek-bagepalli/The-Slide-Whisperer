from typing import List, Optional, Tuple, Union
import json
from pydantic import BaseModel
from openai import OpenAI
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.enum.shapes import PP_PLACEHOLDER

class ContentMapping(BaseModel):
    content_type: str
    value: Union[str, List[str]]
    placeholder_type: str
    placeholder_index: int

class SlideContent(BaseModel):
    bullets: List[str]
    speaker_notes: str
    image_paths: List[str] = []  # Default empty list to prevent validation error

class Slide(BaseModel):
    slide: int
    slide_title: str
    slide_content: SlideContent

class PresentationMetadata(BaseModel):
    title: str
    subtitle: str

class PresentationResponse(BaseModel):
    metadata: PresentationMetadata
    slides: List[Slide]

def generate_slide_content(presentation_data, minimum_slides=10) -> Tuple[List[Slide]]:
    client = OpenAI()
    prompt = f"""
    Strict Instructions:

    minimum_slides: {minimum_slides}

    First, create a title and subtitle for the presentation.

    Provide a title and subtitle for the presentation.

    Then, think about all the `detailed_summary` and details in the `retrieved_content_from_document` and how they can be arranged to determine the overall story of the presentation.
    Then, use the information in the `detailed_summary` and the `response` in the `retrieved_content_from_document` to create informative and clear bullet points for each slide. Each bullet point should be detailed in itself.
    Ensure there are a maximum of 3 bullets per slide, if there is only one text box. If there are multiple text boxes, then there should be a maximum of 4 bullets per slide.
    Then, map all the key visualizations to appropriate slides using the provided image paths, with captions explaining each visualization. No slide should have more than 1 image. Ensure the image paths are taken from the `retrived_image_paths_charts` and `retrived_image_paths_images`. Do not make up any image paths. Do not add anything to the image paths.
    Then, create a JSON object with the following structure:
    {{
        "metadata": {{
            "title": "Title of the presentation",
            "subtitle": "Subtitle of the presentation"
        }},

        "slides": [
            {{
                "slide": number,
                "slide_title": "Title of the slide",
                "slide_content": {{
                    "bullets": ["bullet point 1", "bullet point 2"], 
                    "speaker_notes": "Detailed speaker notes for this slide",
                    "image_paths": ["path_to_image1.png","path_to_image_2.png"]
                }}
            }}
        ]
    }}
    {json.dumps(presentation_data, indent=2)}
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a presentation expert who creates detailed, informative section content in JSON format with specific examples and thorough analysis."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=4000
    )
    try:
        content = response.choices[0].message.content.strip()
        content = content.replace('```json', '').replace('```', '').rstrip(',')
        raw_content = json.loads(content)
        
        # Validate metadata and slides using Pydantic
        slides = [Slide(**slide) for slide in raw_content["slides"]]
        metadata = PresentationMetadata(**raw_content["metadata"])
        return slides, metadata
        
    except json.JSONDecodeError as e:
        print(f"Error: Could not parse response as JSON. Error details: {str(e)}")
        print("Raw response content:", response.choices[0].message.content)
        return None, None
    except Exception as e:
        print(f"Error: Could not validate content. Error details: {str(e)}")
        return None, None

def generate_slide_content2(presentation_data, layout_specs) -> Tuple[List[Slide], PresentationMetadata]:
    client = OpenAI()
    
    # Process the content and determine slide structure
    slide_prompt = f"""
    Analyze this content and determine how to split it into appropriate slides (max 3 slides):
    {json.dumps(presentation_data, indent=2)}

    Available layouts:
    {json.dumps(layout_specs, indent=2)}

    For each slide, consider:
    1. Content length and complexity
    2. Number of bullet points (max 2-3 very detailed bullet points per slide)
    3. Whether there's an image
    4. Layout dimensions and placeholder types

    Important placeholder type mapping rules:
    - "title" content_type must map to "TITLE" placeholder_type
    - "bullets" content_type must map to "BODY" or "OBJECT" placeholder_type
    - "image_path" content_type must map to "PICTURE" placeholder_type
    - "speaker_notes" content_type must map to "BODY" placeholder_type
    - "caption" content_type must map to "SLIDE_NUMBER" placeholder_type

    Return a JSON object with this structure:
    {{
        "slides": [
            {{
                "slide_number": <int>,
                "layout_id": <chosen layout id>,
                "layout_name": "<chosen layout name>",
                "mapping": [
                    {{
                        "content_type": "title" | "bullets" | "image_path" | "speaker_notes" | "caption",
                        "value": "...",  // the actual content
                        "placeholder_type": "TITLE" | "BODY" | "PICTURE" | ...,
                        "placeholder_index": <int>
                    }},
                    ...
                ]
            }}
        ]
    }}

    Ensure the bullets are very detailed and informative.
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a presentation expert who creates well-structured slides with appropriate layouts."},
            {"role": "user", "content": slide_prompt}
        ],
        temperature=0.7,
        max_tokens=3000
    )

    try:
        content = response.choices[0].message.content.strip()
        # Find the first { and last } to extract just the JSON object
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        if start_idx == -1 or end_idx == 0:
            raise ValueError("No valid JSON object found in response")
        
        json_str = content[start_idx:end_idx]
        raw_content = json.loads(json_str)
        
        # Create slides from the response
        slides = [Slide(**slide) for slide in raw_content["slides"]]
        
        return slides
        
    except Exception as e:
        print(f"Error generating slides: {str(e)}")
        print("Raw response content:", content)
        return None

def get_available_layouts(template_path = "templates/A.pptx"):
    
    prs = Presentation(template_path)
    
    # Iterate through slide layouts
    for i, layout in enumerate(prs.slide_layouts):
        print(f"Layout {i}: {layout.name}")
        for shape in layout.placeholders:
            if shape.is_placeholder:
                phf = shape.placeholder_format
                print(f"  - Name: {shape.name}")
                print(f"    Type: {phf.type}")  # e.g., TITLE, BODY, PICTURE
                print(f"    Index (idx): {phf.idx}")
                print(f"    Placeholder Type: {PP_PLACEHOLDER(phf.type).name}")

def emu_to_inches(emu):
    return round(emu / 914400, 2)

def get_llm_friendly_layouts(pptx_path):
    prs = Presentation(pptx_path)
    layouts_info = []

    for layout_id, layout in enumerate(prs.slide_layouts):
        layout_data = {
            "layout_id": layout_id,
            "layout_name": layout.name,
            "placeholders": []
        }

        for shape in layout.placeholders:
            if shape.is_placeholder:
                phf = shape.placeholder_format
                try:
                    ph_type = PP_PLACEHOLDER(phf.type).name
                except ValueError:
                    ph_type = "UNKNOWN"

                layout_data["placeholders"].append({
                    "name": shape.name,
                    "placeholder_type": ph_type,
                    "index": phf.idx,
                    "position": {
                        "left_in": emu_to_inches(shape.left),
                        "top_in": emu_to_inches(shape.top)
                    },
                    "size": {
                        "width_in": emu_to_inches(shape.width),
                        "height_in": emu_to_inches(shape.height)
                    }
                })

        layouts_info.append(layout_data)

    return layouts_info
# print(get_llm_friendly_layouts("available_templates/A.pptx"))

def build_prompt_with_placeholder_indices_and_dimensions(slide_content, layout_specs):
    return f"""
You are an expert presentation assistant. Consider the font size to be 24pt.

Your task is to:
1. Choose the most appropriate slide layout from the list below.
2. Assign each content element (e.g., title, bullets, image, speaker notes) to the best-fitting placeholder within that layout.

Each layout includes:
- `layout_id`: an integer used to reference the layout.
- `layout_name`: name of the layout.
- `placeholders`: a list of available content slots, each described with:
  - `name`: the internal name of the placeholder.
  - `placeholder_type`: one of TITLE, BODY, PICTURE, SUBTITLE, SLIDE_NUMBER, etc.
  - `index`: the internal ID used to refer to this placeholder.
  - `position`: its top-left location on the slide (in inches).
  - `size`: its width and height (in inches).

Please choose a layout and map each content element to a placeholder by matching its `placeholder_type`. Use the `size` to decide which layout has BODY that is most suitable to fit the bullets. Also try to preserve the aspect ratio of the image.

Respond with a JSON object in the following format:
{{
  "slide_number": <int>,
  "layout_id": <int>,
  "layout_name": "<layout_name>",
  "mapping": [
    {{
      "content_type": "title" | "bullets" | "image_path" | "speaker_notes" | "caption",
      "value": "...",  // the actual content
      "placeholder_type": "TITLE" | "BODY" | "PICTURE" | ...,
      "placeholder_index": <int>
    }},
    ...
  ]
}}

Here are the available slide layouts:
{json.dumps(layout_specs, indent=2)}

Here is the content for the slide:
{json.dumps(slide_content, indent=2)}
"""

