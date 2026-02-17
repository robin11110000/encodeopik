import os
from pathlib import Path
from typing import Any, Dict

import fitz  # PyMuPDF
from PIL import Image, ImageDraw


def get_chunk_by_id(chunks, chunk_id):
    """
    Retrieve a specific chunk from a list of Chunk objects by its ID.

    Args:
        chunks (list): List of Chunk objects.
        chunk_id (str): ID of the chunk to retrieve.

    Returns:
        Chunk: The matching chunk object if found, else None.
    """
    for chunk in chunks:
        if getattr(chunk, "id", None) == chunk_id:
            return chunk
    print(f"⚠️ No chunk found with id: {chunk_id}")
    return None


def extract_bbox_from_response(chunk):
    """
    Extracts normalized bounding box coordinates from a response object.
    Works for both PDFs and images (page attribute is always available).

    Args:
        response: The model or API response containing chunk grounding info.
        chunk_index (int): The index of the chunk to extract (default: 0).

    Returns:
        dict: Bounding box in the form:
              {'page': int, 'left': float, 'right': float, 'top': float, 'bottom': float}
    """
    grounding = chunk.grounding

    bbox = {
        'page': grounding.page,
        'left': grounding.box.left,
        'right': grounding.box.right,
        'top': grounding.box.top,
        'bottom': grounding.box.bottom,
    }
    return bbox

def draw_bounding_box(input_path: str, output_path: str, bbox: Dict[str, float], color=(255, 0, 0), width=3):
    ext = os.path.splitext(input_path)[1].lower()

    if ext == ".pdf":
        doc = fitz.open(input_path)
        page_index = int(bbox["page"])  # ensure int
        if page_index < 0 or page_index >= len(doc):
            raise ValueError(f"Page index {page_index} out of range for PDF with {len(doc)} pages")
        page = doc[page_index]

        page_width, page_height = page.rect.width, page.rect.height
        x0 = bbox["left"] * page_width
        x1 = bbox["right"] * page_width
        y0 = bbox["top"] * page_height
        y1 = bbox["bottom"] * page_height

        rect = fitz.Rect(x0, y0, x1, y1)
        page.draw_rect(rect, color=tuple(c / 255 for c in color), width=width)

        doc.save(output_path)
        doc.close()
        return

    elif ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"]:
        img = Image.open(input_path)
        draw = ImageDraw.Draw(img)
        width_img, height_img = img.size

        x0 = bbox["left"] * width_img
        x1 = bbox["right"] * width_img
        y0 = bbox["top"] * height_img
        y1 = bbox["bottom"] * height_img

        for i in range(width):
            draw.rectangle([x0 - i, y0 - i, x1 + i, y1 + i], outline=color)

        img.save(output_path)
        return

    else:
        raise ValueError("Unsupported file format. Use PDF or common image formats.")


def list_folders_with_files(base_path: str):
    """
    Lists each folder in the given directory along with its files.

    Args:
        base_path (str): Path to the main folder.

    Returns:
        list[dict]: [
            {
                "folder_name": str,
                "files": [list of file names]
            }, ...
        ]
    """
    folder_list = []

    for entry in os.listdir(base_path):
        folder_path = os.path.join(base_path, entry)

        if os.path.isdir(folder_path):
            files = [
                f for f in os.listdir(folder_path)
                if os.path.isfile(os.path.join(folder_path, f))
            ]
            folder_list.append({
                "folder_name": entry,
                "files": files
            })

    return folder_list


def get_files_in_folder(folder_path: str):
    """
    Returns a list of full file paths inside the given folder.

    Args:
        folder_path (str): Path to the folder.

    Returns:
        list[str]: List of full file paths.
    """
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    if not os.path.isdir(folder_path):
        raise NotADirectoryError(f"Provided path is not a folder: {folder_path}")

    files = [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, f))
    ]

    return files
