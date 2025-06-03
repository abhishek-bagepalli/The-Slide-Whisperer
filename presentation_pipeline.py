import json
from slide_content_generator import build_prompt_with_placeholder_indices_and_dimensions
from create_slide import create_slide_from_content
from openai import OpenAI

def run_presentation_pipeline(template_path, output_path, slide_contents_path, layout_specs):
    """
    Run the complete presentation generation pipeline.
    
    Args:
        template_path (str): Path to the PowerPoint template
        output_path (str): Path where the final presentation will be saved
        slide_contents_path (str): Path to the JSON file containing slide contents
        layout_specs (list): List of available layout specifications
    """
    # Load slide contents
    with open(slide_contents_path, 'r') as f:
        slide_contents = json.load(f)
    
    layout_mappings = []
    
    # Process each slide content
    for content in slide_contents:
        # Build prompt for layout selection
        prompt = build_prompt_with_placeholder_indices_and_dimensions(content, layout_specs)
        
        layout_mapping = get_layout_mapping(prompt)
        
        # Clean up image paths in the mapping
        for item in layout_mapping['mapping']:
            if item['content_type'] == 'image_path':
                # Remove any 'images\' prefix from the path
                item['value'] = item['value'].replace('images\\', '').replace('images/', '')
        
        layout_mappings.append(layout_mapping)
        print(layout_mapping)
        print('--------------------------------')

    # Write layout mappings to a JSON file
    with open('layout_mappings.json', 'w') as f:
        json.dump(layout_mappings, f, indent=2)
    print(f"✅ Layout mappings saved to: layout_mappings.json")

    # Create the final presentation
    create_slide_from_content(template_path, output_path, layout_mappings)

def get_layout_mapping(prompt):
    client = OpenAI()
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a presentation expert who maps content to appropriate slide layouts."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1000
    )

    layout_mapping = response.choices[0].message.content.strip()
    layout_mapping = layout_mapping.replace('```json', '').replace('```', '').rstrip(',')
    layout_mapping = json.loads(layout_mapping)
    
    return layout_mapping

# if __name__ == "__main__":
#     # Example usage
#     template_path = "available_templates/A.pptx"
#     output_path = "generated_presentation.pptx"
#     slide_contents_path = "slide_contents.json"
    
#     # Get layout specs
#     from slide_content_generator import get_llm_friendly_layouts
#     layout_specs = get_llm_friendly_layouts(template_path)
    
#     # Run the pipeline
#     run_presentation_pipeline(template_path, output_path, slide_contents_path, layout_specs) 