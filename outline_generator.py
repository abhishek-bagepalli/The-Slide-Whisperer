# outline_generator.py
import os
import json
from typing import List
from pydantic import BaseModel, ValidationError
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI()

# Pydantic models for validation
class SectionOutline(BaseModel):
    heading: str
    num_content_slides: int
    key_points: List[str]

class DocumentOutline(BaseModel):
    title: str
    subtitle: str | None = None  # Make subtitle optional with default None
    sections: List[SectionOutline]

# Prompt template
PROMPT_TEMPLATE = """
You are a slide-outline assistant.  
Given the document title and a list of section summaries, produce a JSON object matching this schema:

{{
  "title": <string>,           // main deck title
  "subtitle": <string>,        // optional subtitle or author
  "sections": [
    {{
      "heading": <string>,     // section heading
      "num_content_slides": <integer >= 1>,  
      "key_points": [<string>, …]   // 3–5 bullets that will become slide bullets
    }},
    …
  ]
}}

Use no extra keys. Constrain total slides (sum of num_content_slides) to be at most {max_slides}.  
Here are the inputs:

Document Title:
{title}

Section Summaries:
{summaries}
"""

def generate_outline(title: str, summaries: List[dict], max_slides: int = 15) -> DocumentOutline:
    # Fill prompt
    prompt = PROMPT_TEMPLATE.format(
        title=title,
        summaries="\n".join(f"- {s['title']}: {s['summary']}" for s in summaries),  # Include section titles
        max_slides=max_slides
    )

    # Call the LLM
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1000,  # Increased token limit for longer responses
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

def pretty_print(outline: DocumentOutline):
    print(f"\nDeck Title: {outline.title}")
    if outline.subtitle:
        print(f"Subtitle: {outline.subtitle}\n")
    total = 0
    for sec in outline.sections:
        print(f"Section: {sec.heading}  •  Slides: {sec.num_content_slides}")
        for pt in sec.key_points:
            print(f"   – {pt}")
        total += sec.num_content_slides
        print()
    print(f"Total slides planned: {total}\n")

# if __name__ == "__main__":
#     # Example usage; replace with your real summaries
#     doc_title = "Q2 Marketing Strategy Review"
#     section_summaries = [{'title': 'Brief Assessment:', 'summary': 'Yue Sai, a once prestigious Chinese cosmetics brand, lost relevance due to failed repositionings, leading to low awareness among younger consumers. L’Oréal faces the challenge of reviving the brand in a competitive market shaped by rising local players and digital consumption. Younger Chinese consumers prefer skin care rooted in tradition. Competitors like Herborist succeed with modern branding rooted in traditional Chinese medicine. Digital platforms and experiential retail offer better engagement than TV ads. L’Oréal must align its city-tier strategy with a clear brand identity to meet evolving consumer expectations.'}, {'title': 'Decision Problem:', 'summary': "To reposition Yue Sai in China's cosmetics market, L'Oréal must conduct thorough market research to understand current trends and consumer preferences. By leveraging Yue Sai's heritage and reputation, L'Oréal can revamp the brand's image to appeal to modern Chinese consumers. Implementing innovative marketing strategies and product offerings tailored to the local market will be crucial in regaining relevance and increasing market share."}, {'title': 'Criteria:', 'summary': "This slide examines Yue Sai's sales performance and product-market fit. Sales data is analyzed to project revenue, while market research assesses how well products align with target segment needs. Factors like local relevance and demographic responsiveness are considered to ensure products meet customer preferences."}, {'title': '3. Strategic Fit', 'summary': "This slide evaluates the alignment of alternatives with L'Oréal's brand vision and mission. Each alternative is scored based on its compatibility with the company's brand values."}, {'title': '4. Risk of Attrition', 'summary': "Learn how to measure customer loyalty and growth with a focus on retaining existing customers and attracting new ones. Evaluate customer retention metrics, purchase behavior, and changes in demographics to ensure the product's success in the market."}, {'title': '5. Execution Complexity', 'summary': 'This slide evaluates the implementation difficulty of the proposed alternative by assessing costs related to resources, budget constraints, production, and logistics. It highlights the importance of considering these factors when making decisions.'}, {'title': 'Moderate Risk', 'summary': 'In a highly competitive digital space, the brand risks alienating older loyalists while facing strong local rivals like Herborist and Chando.'}, {'title': 'Attrition Risk', 'summary': 'Appealing to a broader audience can lead to increased retention rates, but may also dilute brand prestige.'}, {'title': 'Execution', 'summary': 'To achieve moderate growth, implement targeted digital campaigns, invest in TCM research and development, and expand offerings in premium tiers.'}, {'title': 'Very High', 'summary': 'Managing multiple channels can significantly raise complexity and costs.'}, {'title': 'Recommendation: Alternative 1 - Yue Sai for Modern Young Women', 'summary': "Alternative 1 offers a clear strategy for Yue Sai to rebuild its brand with luxury appeal and cultural relevance through TCM, targeting modern, health-conscious young women in China. This unique position within L'Oreal's portfolio distinguishes Yue Sai from other luxury brands, ensuring long-term growth and market relevance."}]
#     outline = generate_outline(doc_title, section_summaries, max_slides=12)
#     pretty_print(outline)