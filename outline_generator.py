# outline_generator.py
import os
import json
from typing import List
from pydantic import BaseModel, ValidationError
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI()

# Pydantic models for validation
class SlideDistribution(BaseModel):
    sub_slide: int
    sub_slide_title: str | None = None
    sub_slide_subtitle: str | None = None
    key_points: List[str]

class SectionOutline(BaseModel):
    heading: str
    num_content_slides: int
    slide_distribution: List[SlideDistribution]

class DocumentOutline(BaseModel):
    title: str
    subtitle: str | None = None  # Make subtitle optional with default None
    sections: List[SectionOutline]

# Prompt template
PROMPT_TEMPLATE = """
  You are a slide-outline assistant.  
  Given the document title and separate lists of text summaries, produce a JSON object matching this schema:

  {{
    "title": <string>,           // main deck title
    "subtitle": <string>,        // optional subtitle or author
    "sections": [
      {{
        "heading": <string>,     // section heading
        "num_content_slides": <integer >= 1>,  
        "slide_distribution": [
          {{
            "sub_slide": <integer>,  // Sub slide number
            "sub_slide_title": <string>,  // Sub slide title
            "sub_slide_subtitle": <string>,  // Sub slide subtitle (optional)
            "key_points": [<string>, ...]  // 1-3 bullet points for this slide. If more than 3, move to next sub-slide
          }},
          ...
        ]
      }},
      …
    ]
  }}

  Use no extra keys. Constrain total slides (sum of num_content_slides) to be at most {max_slides}.
  Here are the inputs:

  Document Title:
  {title}

  Text Section Summaries:
  {summaries}
  """

def generate_outline(title: str, summaries: List[str], max_slides: int = 15) -> DocumentOutline:
    # Fill prompt
    prompt = PROMPT_TEMPLATE.format(
        title=title,
        summaries="\n".join(f"- {summary}" for summary in summaries),
        max_slides=max_slides
    )

    # Call the LLM
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1200,  # Increased token limit for longer responses
    )

    # Parse JSON
    content = resp.choices[0].message.content.strip()
    try:
        outline_dict = json.loads(content)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"LLM returned invalid JSON:\n{content}") from e

    # Validate with Pydantic
    try:
        outline = DocumentOutline.model_validate(outline_dict)
    except ValidationError as e:
        raise RuntimeError(f"Outline validation failed:\n{e}") from e

    return outline