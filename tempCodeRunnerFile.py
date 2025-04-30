# Parse your document
parsed_document = parser.load_data("docs/loreal.docx")  # or PDF

# Now parsed_document will have sections, images, maybe tables
print(parsed_document)