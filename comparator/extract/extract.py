import PyPDF2
from PIL import Image
import pytesseract
import io
import sys


# def extract_text(file_path, output_file_path):
#     text = ""
#     try:
#         if file_path.lower().endswith(".pdf"):
#             text = extract_text_from_pdf(file_path)
#         else:
#             print("Unsupported file format")

#         with open(output_file_path, "w") as output_file:
#             print("Run output")
#             for line in text.splitlines():
#                 print(line)
#             output_file.write(text)
#         print(f"Extracted text saved to {output_file_path}")

#     except Exception as e:
#         print("An error occurred:", e)


# def extract_text_from_image(file_path):
#     image_path = file_path
#     img = Image.open(image_path)
#     text = pytesseract.image_to_string(img)
#     print(text[:-1])


import PyPDF2

def extract_text_from_pdf(pdf_file_path):
    extracted_text = ""
    try:
        with open(pdf_file_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            for i in range(num_pages):
                page = pdf_reader.pages[i]
                page_text = page.extract_text()
                if "ABSTRACT" in page_text:
                    extracted_text += page_text + "\n"
                    break
        return extracted_text
    except Exception as e:
        print("An error occurred:", e)
        return None

# if __name__ == "__main__":
#     import PyPDF2

#     file_path = "./report.pdf"
#     output_file_path = "./extracted_text.txt"
#     extract_text_from_pdf(file_path, output_file_path)