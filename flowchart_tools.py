import subprocess
import os
import tempfile
import uuid
import re

def create_advanced_mermaid_flowchart(title, nodes, edges, output_path="flowchart.md"):
    """
    Create a Mermaid flowchart with custom nodes and edges.

    Args:
        title (str): Title of the flowchart
        nodes (dict): Node ID -> (Label, Shape) where Shape can be 'rect', 'round', 'diamond'
        edges (list of tuples): Each tuple (from_node_id, to_node_id, optional_label)
        output_path (str): Path to save markdown file
    """
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"[INFO] Created directory: {output_dir}")

    shape_map = {
        "rect": "[{}]",   # Rectangle
        "round": "({})",  # Rounded rectangle
        "diamond": "{{{}}}" # Diamond
    }

    mermaid_text = "```mermaid\n"
    mermaid_text += "flowchart TD\n"

    # Define nodes
    for node_id, (label, shape) in nodes.items():
        label_safe = label.replace(" ", "_")
        shape_syntax = shape_map.get(shape, "[{}]").format(label_safe)
        mermaid_text += f"    {node_id}{shape_syntax}\n"

    # Define edges
    for edge in edges:
        if len(edge) == 2:
            from_node, to_node = edge
            mermaid_text += f"    {from_node} --> {to_node}\n"
        elif len(edge) == 3:
            from_node, to_node, label = edge
            mermaid_text += f"    {from_node} -- \"{label}\" --> {to_node}\n"

    mermaid_text += "```"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(mermaid_text)
    
    print(f"[INFO] Advanced Mermaid flowchart saved at {output_path}")


def generate_mermaid_png_from_markdown(markdown_file_path: str, output_path: str):
    """
    Parses a Markdown file, extracts the first Mermaid diagram block, 
    and generates a PNG using the mmdc CLI tool.

    Args:
        markdown_file_path (str): Path to the input Markdown (.md) file.
        output_path (str): Path where the output PNG file should be saved.

    Raises:
        ValueError: If no Mermaid diagram is found in the Markdown file.
        FileNotFoundError: If mmdc is not installed or not found in PATH.
        subprocess.CalledProcessError: If mmdc fails during execution.
    """

    # Step 1: Read the markdown file
    if not os.path.exists(markdown_file_path):
        raise FileNotFoundError(f"Markdown file not found: {markdown_file_path}")

    with open(markdown_file_path, 'r', encoding='utf-8') as f:
        markdown_text = f.read()

    # Step 2: Extract the first mermaid fenced block
    mermaid_match = re.search(r"```mermaid(.*?)```", markdown_text, re.DOTALL)
    
    if not mermaid_match:
        raise ValueError("No Mermaid diagram found inside the markdown file.")

    mermaid_code = mermaid_match.group(1).strip()

    # Step 3: Save the extracted Mermaid code into a temporary .mmd file
    temp_dir = tempfile.gettempdir()
    temp_file_path = os.path.join(temp_dir, f"temp_{uuid.uuid4().hex}.mmd")

    with open(temp_file_path, 'w', encoding='utf-8') as f:
        f.write(mermaid_code)

    try:
        # Step 4: Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # Step 5: Run mmdc
        subprocess.run(
            [   "powershell",
                "mmdc",
                "-i", temp_file_path,
                "-o", output_path,
                "--backgroundColor", "white"
            ],
            check=True
        )
        print(f"✅ Mermaid diagram successfully saved to {output_path}")

    except FileNotFoundError:
        raise FileNotFoundError(
            "The 'mmdc' command was not found. "
            "Please ensure Mermaid CLI is installed globally using 'npm install -g @mermaid-js/mermaid-cli'."
        )

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"mmdc execution failed: {e}")

    finally:
        # Step 6: Clean up temp file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)



create_advanced_mermaid_flowchart(
    title="Loan Application Workflow",
    nodes={
        "A": ("Receive Application", "rect"),
        "B": ("Verify Documents", "round"),
        "C": ("Check Credit Score", "diamond"),
        "D": ("Approve Loan", "rect"),
        "E": ("Reject Loan", "rect"),
        "F": ("Disburse Funds", "round")
    },
    edges=[
        ("A", "B"),
        ("B", "C"),
        ("C", "D", "Yes"),
        ("C", "E", "No"),
        ("D", "F")
    ],
    output_path="loan_flowchart.md"
)

generate_mermaid_png_from_markdown(
    markdown_file_path="loan_flowchart.md",
    output_path="loan_flowchart.png"
)