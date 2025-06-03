from typing import List, Optional, Tuple, Union
import json
from pydantic import BaseModel
from openai import OpenAI

class ContentMapping(BaseModel):
    content_type: str
    value: Union[str, List[str]]
    placeholder_type: str
    placeholder_index: int

class SlideContent(BaseModel):
    bullets: List[str]
    speaker_notes: str
    image_paths: List[str] = []

class Slide(BaseModel):
    slide: int
    slide_title: str
    slide_content: SlideContent

class PresentationMetadata(BaseModel):
    title: str
    subtitle: str

def generate_presentation_metadata(presentation_data: List[dict]) -> PresentationMetadata:
    """
    Generate the presentation title and subtitle by analyzing all summaries.
    """
    client = OpenAI()
    
    # Extract all detailed summaries
    summaries = [item["detailed_summary"] for item in presentation_data]
    
    prompt = f"""
    Analyze these detailed summaries and create a concise but descriptive title and subtitle for the presentation.
    The title should capture the main theme, and the subtitle should provide additional context.
    
    Summaries:
    {json.dumps(summaries, indent=2)}
    
    Return a JSON object with this structure:
    {{
        "title": "Main title of the presentation",
        "subtitle": "Supporting subtitle that provides context"
    }}
    """
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a presentation expert who creates clear and engaging titles."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=500
    )
    
    try:
        content = response.choices[0].message.content.strip()
        content = content.replace('```json', '').replace('```', '').strip()
        metadata_dict = json.loads(content)
        return PresentationMetadata(**metadata_dict)
    except Exception as e:
        print(f"Error generating metadata: {str(e)}")
        # Fallback to a generic title if generation fails
        return PresentationMetadata(
            title="Presentation",
            subtitle="Generated Presentation"
        )

def get_context_summaries(presentation_data: List[dict], current_index: int) -> Tuple[Optional[str], str, Optional[str]]:
    """
    Get the previous, current, and next summaries for context.
    Returns (previous_summary, current_summary, next_summary)
    """
    current_summary = presentation_data[current_index]["detailed_summary"]
    previous_summary = presentation_data[current_index - 1]["detailed_summary"] if current_index > 0 else None
    next_summary = presentation_data[current_index + 1]["detailed_summary"] if current_index < len(presentation_data) - 1 else None
    
    return previous_summary, current_summary, next_summary

def generate_single_slide_content(
    presentation_data: List[dict],
    current_index: int,
    metadata: PresentationMetadata,
    minimum_slides: int = 10
) -> Slide:
    """
    Generate content for a single slide using the current summary and context from adjacent summaries.
    """
    client = OpenAI()
    
    # Get context summaries
    previous_summary, current_summary, next_summary = get_context_summaries(presentation_data, current_index)
    
    # Get current slide's data
    current_data = presentation_data[current_index]
    
    # Build context string
    context = "Previous slide context:\n" + previous_summary + "\n\n" if previous_summary else ""
    context += "Next slide context:\n" + next_summary + "\n\n" if next_summary else ""
    
    prompt = f"""
    Strict Instructions:
    
    You are creating slide {current_index + 1} of {len(presentation_data)} slides.
    The presentation title is: {metadata.title}
    The presentation subtitle is: {metadata.subtitle}
    
    Consider the following context from adjacent slides:
    {context}
    
    Current slide content to process:
    {json.dumps(current_data, indent=2)}
    
    Create a slide with:
    1. A clear, concise title
    2. Maximum 3 bullet points if there's only one text box, or 4 if there are multiple text boxes
    3. Detailed speaker notes
    4. Appropriate image paths from the provided options
    
    Return a JSON object with this structure:
    {{
        "slide": {current_index + 1},
        "slide_title": "Title of the slide",
        "slide_content": {{
            "bullets": ["bullet point 1", "bullet point 2"],
            "speaker_notes": "Detailed speaker notes for this slide",
            "image_paths": ["path_to_image1.png"]
        }}
    }}
    """
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a presentation expert who creates detailed, informative slide content."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1000
    )
    
    try:
        content = response.choices[0].message.content.strip()
        content = content.replace('```json', '').replace('```', '').strip()
        slide_dict = json.loads(content)
        
        # Clean up image paths
        if "slide_content" in slide_dict and "image_paths" in slide_dict["slide_content"]:
            cleaned_paths = []
            for path in slide_dict["slide_content"]["image_paths"]:
                cleaned_path = path.replace('images\\', '').replace('images/', '')
                cleaned_paths.append(cleaned_path)
            slide_dict["slide_content"]["image_paths"] = cleaned_paths
        
        return Slide(**slide_dict)
    except Exception as e:
        print(f"Error generating slide {current_index + 1}: {str(e)}")
        # Return a basic slide if generation fails
        return Slide(
            slide=current_index + 1,
            slide_title=f"Slide {current_index + 1}",
            slide_content=SlideContent(
                bullets=["Content generation failed"],
                speaker_notes="Error in content generation",
                image_paths=[]
            )
        )

def generate_slide_content(presentation_data: List[dict], minimum_slides: int = 10) -> Tuple[List[Slide], PresentationMetadata]:
    """
    Generate slide content slide by slide, maintaining context between slides.
    """
    # First, generate the presentation metadata
    metadata = generate_presentation_metadata(presentation_data)
    
    # Then generate each slide
    slides = []
    for i in range(len(presentation_data)):
        slide = generate_single_slide_content(presentation_data, i, metadata, minimum_slides)
        slides.append(slide)
    
    return slides, metadata 