from pdf_parser import process_document
from multimodal_rag import build_image_index, get_best_image

def main():
    file_path = "docs/loreal.docx"

    image_folder = "./images"

    json_result = process_document(file_path)

    image_index = build_image_index(image_folder)

    query = "Loreal"

    best_image, score = get_best_image(query, image_index)

    print(f"Best image: {best_image}, Score: {score}")


if __name__ == "__main__":
    main()
