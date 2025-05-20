from openai import OpenAI
import json
 
client = OpenAI()
 
def generate_slide_content(presentation_data):
    # Prepare the prompt with all available information
    prompt = f"""
    Please refer to the context provided and to the rules, and then based on the following presentation data, generate a presentation deck in JSON format matching this structure:
    [
      {{
        "slide_number": number,
        "slide_title": "Title of the slide",
        "slide_subtitle": "Subtitle of the slide",
        "slide_content": {{
          "bullets": ["bullet point 1", "bullet point 2"],
          "speaker_notes": "Detailed speaker notes for this slide",
          "image_caption": ["Caption for image if present"],
          "image_paths": ["path_to_image.png"]
        }}
      }}
    ]
   
    Presentation Data:
    {json.dumps(presentation_data, indent=2)}

    Context:

    The presentation data contains the following information -

    1. key points - a list of key themes from the document
    2. key visualizations - a list of images that are relevant to the key points
    3. retrieved content - a list of retrieved content from the document based on the document queries, the query gives context about what is being retrieved and the response is the retrieved content to be used in the slide content
    4. image paths - a list of image paths corresponding to the key visualizations
    
    Rules:

    1. Generate a presentation that has one title slide for the entire deck with a compelling title and subtitle, it should be the first slide and will not have any content
    2. Combine and organize the information in the prentationation data into slides with with a coherent flow between slides
    3. Ensure that each slide has five bullet points in the content section, each bullet point is a proper sentence of 12 words
    4. Ensure that the bullet points are detailed with specific examples and data
    5. Make sure the slides include specific data points and quotes from the presentation data
    6. Map all key visualizations to appropriate slides using the provided image paths, with captions explaining each visualization
    7. Ensure that all key points have been covered in the presentation
    8. End with a strong conclusion slide summarizing key takeaways

    """
   
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a presentation expert who creates detailed, informative slide content in JSON format with required images and data points."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
   
    # Parse the response as JSON
    try:
        # Extract the content from the response
        content = response.choices[0].message.content.strip()
       
        # Clean the content to ensure it's valid JSON
        # Remove any markdown code block indicators
        content = content.replace('```json', '').replace('```', '')
       
        # Parse the cleaned content
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Error: Could not parse response as JSON. Error details: {str(e)}")
        print("Raw response content:", response.choices[0].message.content)
        return None
 
# Load presentation data from JSON file
with open('presentation_data.json', 'r') as f:
    presentation_data = json.load(f)
 
# Generate slide deck and save to JSON file
slide_content = generate_slide_content(presentation_data)
if slide_content:
    with open('updated_slide_content.json', 'w') as f:
        json.dump(slide_content, f, indent=2)
    print("Slide content saved to updated_slide_content.json")