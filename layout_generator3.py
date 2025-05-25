from pptx import Presentation
from openai import OpenAI
import json

template_path = "available_templates/A.pptx"
prs = Presentation(template_path)

def get_layout_specs(prs):
    layout_specs = []
    for i, layout in enumerate(prs.slide_layouts):
        supported = set()
        for shape in layout.placeholders:
            name = shape.name.lower()
            if 'title' in name:
                supported.add('title')
            if 'content' in name:
                supported.add('bullets')
            if 'picture' in name or 'image' in name:
                supported.add('image_path')
            if 'caption' in name:
                supported.add('caption')
            if 'notes' in name:
                supported.add('speaker_notes')

        layout_specs.append({
            "layout_id": i,
            "name": layout.name,
            "supports": list(supported)
        })
    return layout_specs

outputs = []

def generate_layout(slide_content):
    layout_specs = get_layout_specs(prs)
    for slide in slide_content:
        print(slide)

        prompt = f"""
            You are an expert presentation assistant. Based on the following available slide layouts, choose the best layout and return structured JSON output.

            Here are the layout options:
            {json.dumps(layout_specs, indent=2)}

            Slide content to reformat:
            {json.dumps(slide, indent=2)}
        """

        client = OpenAI()

        response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You format slides based on layout specifications."},
            {"role": "user", "content": prompt}
        ],
        functions=[
            {
                "name": "choose_slide_layout_and_format",
                "description": "Choose the best layout and reformat the content accordingly",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "slide_number": {"type": "integer"},
                        "layout_id": {"type": "integer"},
                        "layout_name": {"type": "string"},
                        "title": {"type": "string"},
                        "content": {
                            "type": "object",
                            "properties": {
                                "bullets": {"type": "array", "items": {"type": "string"}},
                                "image_path": {"type": "string"},
                                "speaker_notes": {"type": "string"},
                                "caption": {"type": "string"}
                            },
                            "additionalProperties": False
                        }
                    },
                    "required": ["slide_number", "layout_id", "layout_name", "title", "content"]
                }
            }
        ],
        function_call={"name": "choose_slide_layout_and_format"}
    )
        
        # To extract the structured output:
        function_args = response.choices[0].message.function_call.arguments
        parsed_output = json.loads(function_args)

        outputs.append(parsed_output)

    return outputs



