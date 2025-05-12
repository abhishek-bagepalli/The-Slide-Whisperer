# main.py

from openai import OpenAI
import json
from typing import Dict, Any, List
from slide_tools import create_slide, add_text_to_slide, add_image_to_slide #, add_chart_to_slide

my_api_key = ""
client = OpenAI(api_key = my_api_key)

# Define tools

tools = [
    {
        "type": "function",
        "function": {
            "name": "create_slide",
            "description": "Create a new slide with optional title, text, image, and chart.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "text": {"type": "string"},
                    "image_path": {"type": "string"},
                    "chart_data_path": {"type": "string"}
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_text_to_slide",
            "description": "Add or modify text content on an existing slide.",
            "parameters": {
                "type": "object",
                "properties": {
                    "slide_number": {"type": "integer"},
                    "text": {"type": "string"}
                },
                "required": ["slide_number", "text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_image_to_slide",
            "description": "Insert an image on a specific slide.",
            "parameters": {
                "type": "object",
                "properties": {
                    "slide_number": {"type": "integer"},
                    "image_path": {"type": "string"}
                },
                "required": ["slide_number", "image_path"]
            }
        }
    }#,
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "add_chart_to_slide",
    #         "description": "Add a chart to a given slide based on chart data.",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "slide_number": {"type": "integer"},
    #                 "chart_data_path": {"type": "string"}
    #             },
    #             "required": ["slide_number", "chart_data_path"]
    #         }
    #     }
    # }
]

# Initialize messages and memory

with open("document_parsed.json", "r", encoding="utf-8") as f:
    slide_data = json.load(f)

print(slide_data[:10000])

memory = []
messages = [
    {
        "role": "system",
        "content": (
            "You are a helpful presentation assistant. Your job is to create well-structured PowerPoint slides using tools. "
            "After executing a tool, reflect on whether the user’s overall goal is complete. If not, continue using the appropriate tools. "
            "Always think step-by-step. If the task is multi-part (e.g., Q1, Q2, Q3), you may continue creating slides until the task is done. "
            # "If uncertain, you may ask the user. Keep track of what has been done already via tool results."
        )
    },
    {
        "role": "user",
        "content": (
            """
                    Please create a visually appealing powerpoint presentation based on the json input given below. 
                    The json file was created using LlamaParse. 
                    It contains a list of objects where each object contains the contents of each page of a document. 
                    Using the contents of the json file, create a powerpoint presentation with the text and images where appropriate. 
                    The images are present in the images folder, and contain two files called yue_sai_logo.png which is the logo of Yue Sai, 
                    and loreal_logo.png which is the logo of Loreal. Please use this information to pass the image path to the add_image_to_slide tool.
                        json input:
                        {slide_data[:10000]}
            """    
        )
    }
]

# Agentic loop
# Agentic loop with memory
while True:
    response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=messages,
    tools=tools,
    tool_choice="auto"
    )

    message = response.choices[0].message
    memory.append(message)

    if message.tool_calls:
        for tool_call in message.tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            print(f"\n[INFO] Tool called: {function_name}")
            print(f"[INFO] Arguments: {json.dumps(arguments, indent=2)}")

            # Call appropriate tool
            if function_name == "create_slide":
                result = create_slide(**arguments)
            elif function_name == "add_text_to_slide":
                result = add_text_to_slide(**arguments)
            elif function_name == "add_image_to_slide":
                result = add_image_to_slide(**arguments)
            # elif function_name == "add_chart_to_slide":
            #     result = add_chart_to_slide(**arguments)
            else:
                result = {"status": "error", "message": f"Unknown function: {function_name}"}

            function_message = {
                "role": "function",
                "name": function_name,
                "content": json.dumps(result)
            }
            messages.append(function_message)
            memory.append(function_message)

    else:
        print("\n[INFO] Final LLM output:")
        print(message.content)

        # Summarize memory log at end
        print("\n[SUMMARY OF SESSION MEMORY]:")
        for m in memory:
            role = getattr(m, "role", "unknown")
            name = getattr(m, "name", None)
            content = getattr(m, "content", "")
            print(f"[{role.upper()}]{f' ({name})' if name else ''}: {content[:200]}{'...' if len(content) > 200 else ''}")

