import json
from typing import List, Literal, Optional
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field, ValidationError

# ------------------------------
# 🎯 Pydantic Models
# ------------------------------
class SlideContent(BaseModel):
    bullets: List[str] = Field(..., min_items=1, max_items=7)
    speaker_notes: str
    
    image_caption: List[str] = Field(default_factory=list)
    flowchart: Literal["True", "False"]
    flowchart_description: Optional[str] = None

class SlideOutput(BaseModel):
    section: str
    sub_slide: int
    slide_content: SlideContent



def safe_parse_response(response_str: str) -> Optional[SlideContent]:
    try:
        response_json = json.loads(response_str)
        return SlideContent.model_validate(response_json)
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"\n❌ Validation failed:\n{e}\n→ Raw response:\n{response_str}\n{'-'*60}")
        return None

def generate_slide_content(outline):

    # ------------------------------
    # 🧠 Prompt Template
    # ------------------------------
    prompt = ChatPromptTemplate.from_template("""
    You are an AI assistant generating PowerPoint slide content. Your goal is to make the presentation look professional and engaging. Avoid suggesting images with charts or graphs, unless the slide is about a chart or graph.

    Slide Title: {slide_title}
    Slide Subtitle: {slide_subtitle}
    Key Points:
    {key_ideas}

    Your task:
    1. Rewrite the key points into 3–5 concise bullet points suitable for a slide.
    2. Write speaker notes that expand on the bullet points.
    3. Determine if an image will help explain the slide.
        If yes, Set "image_caption" to a list containing a 1-sentence caption for the image (e.g., ["A skincare shelf in a Chinese department store"], ["Flowchart showing digital vs retail touchpoints"], ["Logo of Yue Sai brand"])
        Captions should be clear, descriptive, and useful for image search.
        If no, Set "image_caption" to an empty list.

    4. Decide if a flowchart is helpful. If yes:
    - Set "flowchart" to "True"
    - Provide a 1-sentence flowchart_description
    If not:
    - Set "flowchart" to "False"
    - flowchart_description may be null

    Return only a **valid JSON** with the following structure:

    {{
    "bullets": ["..."],
    "speaker_notes": "...",
    "image_caption": ["..."],     
    "flowchart": "True" or "False",
    "flowchart_description": "..."
    }}

    Do NOT use markdown formatting or backticks. Return raw JSON only.
                                            
    Return only a valid JSON object. Do not include extra text. Use double quotes. Ensure proper commas and no trailing commas.
    """)

    # ------------------------------
    # ⚙️ Initialize LangChain
    # ------------------------------
    llm = ChatOpenAI(temperature=0.4, model="gpt-4o")
    slide_chain = LLMChain(llm=llm, prompt=prompt)

    # ------------------------------
    # 📂 Load Outline
    # ------------------------------
    with open("outline.json", "r", encoding="utf-8") as f:
        outline = json.load(f)

    # ------------------------------
    # 🚀 Generate Slide Content
    # ------------------------------
    results = []

    for section in outline["sections"]:
        for slide in section["slide_distribution"]:
            slide_title = section["heading"]
            slide_subtitle = f"Slide {slide['sub_slide']}"
            key_ideas = "\n".join(f"- {pt}" for pt in slide["key_points"])

            try:
                # Run the LLM
                response_str = slide_chain.run({
                    "slide_title": slide_title,
                    "slide_subtitle": slide_subtitle,
                    "key_ideas": key_ideas
                })

                # Parse and validate
                slide_content = safe_parse_response(response_str)

                if slide_content:
                    result = SlideOutput(
                        section=slide_title,
                        sub_slide=slide["sub_slide"],
                        slide_content=slide_content
                    )
                    results.append(result.model_dump())

            except Exception as e:
                print(f"❌ Error on slide '{slide_title} - {slide['sub_slide']}': {e}")

    # ------------------------------
    # 💾 Save Results
    # ------------------------------
    with open("generated_slide_content.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(results)} slides to 'generated_slide_content.json'")

    return results


