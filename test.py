import pytesseract
from pytesseract import Output
from PIL import Image
import os

# Specify the path to Tesseract-OCR executable if not in PATH
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text_from_image(image_path):
    """
    Extracts text from an image file using Tesseract OCR.
    Args:
        image_path (str): Path to the image file.
    Returns:
        str: Extracted text.
    """
    text = image_path + "\n"

    # Open the image using PIL
    image = Image.open(image_path)

    # Convert to grayscale for better OCR accuracy
    image = image.convert('L')

    # OCR using Tesseract
    text += pytesseract.image_to_string(image, lang='eng')
    return text


def process_images_in_directory(directory):
    """
    Processes all images in a directory and extracts text.
    Args:
        directory (str): Path to the directory containing images.
    Returns:
        dict: A dictionary where keys are filenames and values are extracted text.
    """
    extracted_texts = {}
    for filename in os.listdir(directory):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
            image_path = os.path.join(directory, filename)
            print(f"Processing: {image_path}")
            text = extract_text_from_image(image_path)
            extracted_texts[filename] = text
    return extracted_texts

def save_extracted_texts(extracted_texts, output_file):
    """
    Saves the extracted texts to a file.
    Args:
        extracted_texts (dict): Dictionary of extracted texts.
        output_file (str): File path to save the extracted texts.
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        for filename, text in extracted_texts.items():
            f.write(f"--- {filename} ---\n")
            f.write(text)
            f.write("\n\n")

if __name__ == "__main__":
    # Directory containing the images
    image_directory = "/Users/ariel/Downloads/crossfit"

    # Output file to save the extracted text
    output_file = "extracted_texts.txt"

    # Extract text from images
    texts = process_images_in_directory(image_directory)

    # Save the extracted texts to a file
    save_extracted_texts(texts, output_file)

    print(f"Extraction complete. Texts saved to {output_file}")
