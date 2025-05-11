
    for section in sections:
        summary = summarize_text(section["text"])
        slide_summaries.append({
            "title": section["title"],
            "summary": summary
        })

    print(slide_summaries)