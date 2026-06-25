import os
from pathlib import Path
from PIL import Image
from pypdf import PdfWriter, PdfReader


def image_to_pdf(image_path: str, output_path: str) -> None:
    img = Image.open(image_path).convert("RGB")
    img.save(output_path, "PDF", resolution=150)


def merge_to_pdf(file_paths: list[str], output_path: str) -> None:
    writer = PdfWriter()

    for path in file_paths:
        ext = Path(path).suffix.lower()

        if ext in (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"):
            tmp_pdf = path + "_converted.pdf"
            image_to_pdf(path, tmp_pdf)
            reader = PdfReader(tmp_pdf)
            for page in reader.pages:
                writer.add_page(page)
            os.remove(tmp_pdf)

        elif ext == ".pdf":
            reader = PdfReader(path)
            for page in reader.pages:
                writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)
