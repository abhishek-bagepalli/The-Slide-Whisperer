from openai import OpenAI

def summarize_text(text, model="gpt-4"):
    client = OpenAI()

    prompt = f"""
You are a professional presentation writer.

Summarize the following content into a concise paragraph suitable for one PowerPoint slide.

Guidelines:
- No bullet points
- Maximum 70 words
- Keep it engaging and easy to read
- Do not describe visuals yet
- Assume this is one of many slides in a deck

Content:
{text[:3000]}
"""

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=300,
    )

    return response.choices[0].message.content.strip()
