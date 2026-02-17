import os
import json
from pathlib import Path
from typing import Optional, Dict

from src.service.doc_extractor.logger import get_logger

# Initialize logger for this module
logger = get_logger(__name__)

def get_document_files(document_type: str, base_path: str):
    """
    Reads and returns the markdown, txt, and json file contents 
    for a given document type and base path, with error handling.

    Args:
        document_type (str): Type of document (e.g., 'bank-statements')
        base_path (str): Base directory path

    Returns:
        dict: Dictionary containing file contents (or None if file missing)
    """
    base = Path(base_path) / document_type / "output"
    markdown_path = base / f"{document_type}_parsed.md"
    txt_path = base / f"{document_type}_parsed.txt"
    json_path = base / f"{document_type}.json"

    result = {"markdown": None, "txt": None, "json": None}

    try:
        if markdown_path.exists():
            result["markdown"] = markdown_path.read_text(encoding="utf-8")
        else:
            logger.info(f"⚠️ Markdown file not found: {markdown_path}")

        if txt_path.exists():
            result["txt"] = txt_path.read_text(encoding="utf-8")
        else:
            logger.info(f"⚠️ TXT file not found: {txt_path}")

        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                result["json"] = json.load(f)
        else:
            logger.info(f"⚠️ JSON file not found: {json_path}")

    except Exception as e:
        logger.error(f"❌ Error reading files for '{document_type}': {e}")

    return result



# files = get_document_files(
#     document_type='bank-statements',
#     base_path='/Users/rahulkushwaha/Desktop/kyc_ad/landing_ai_kyc/backend/resources/bc0f8f34-1933-448b-9259-de05b80a0814'
# )

def save_json_to_file( data: dict, base_path: str, document_type: str) -> Optional[str]:
    """Save JSON object to 'base_path/output/{document_type}.json'."""
    try:
        file_path = Path(base_path) /f"{document_type}"/ "output"/ f"{document_type}_kpis.json"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"JSON saved successfully at {file_path}")
        return str(file_path)
    except Exception as e:
        logger.exception(f"Error saving JSON file: {e}")
        return None
    

def get_document_kpis_files(document_type: str, base_path: str):
    """
    Reads and returns the json file contents 
    for a given document type and base path, with error handling.

    Args:
        document_type (str): Type of document (e.g., 'bank-statements')
        base_path (str): Base directory path

    Returns:
        dict: Dictionary containing file contents (or None if file missing)
    """
    base = Path(base_path) / document_type / "output"
    json_path = base / f"{document_type}_kpis.json"

    result = None
    try:

        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                result = json.load(f)
        else:
            logger.info(f"⚠️ JSON file not found: {json_path}")

    except Exception as e:
        logger.error(f"❌ Error reading files for '{document_type}': {e}")

    return result


def save_responses_to_folder(response_dict, final_decision, folder_path):
    """
    Save response_dict and final_decision as separate JSON files in the given folder.
    """
    folder = Path(folder_path) / "final_output"
    folder.mkdir(parents=True, exist_ok=True)  # create folder if it doesn't exist

    # Define file paths
    response_path = folder / "kpis_final.json"
    decision_path = folder / "final_decision.json"

    # Save response_dict
    with open(response_path, 'w') as f:
        json.dump(response_dict, f, indent=4)

    # Save final_decision
    with open(decision_path, 'w') as f:
        json.dump(final_decision, f, indent=4)

    logger.info(f"✅ Saved response_dict at: {response_path}")
    logger.info(f"✅ Saved final_decision at: {decision_path}")

def get_image_file_paths(folder_path):
    """
    Return a list of full paths of image files in the given folder.
    """
    image_extensions = {'.png', '.jpg', '.jpeg'}
    image_paths = []
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path) and os.path.splitext(file_name.lower())[1] in image_extensions:
            image_paths.append(file_path)

    return image_paths

def load_json(file_path):
    '''
    input: json file path
    output: text
    Reads a JSON file and returns a pretty string for model input. 
    '''

    with open(Path(file_path), "r") as f:
        json_text = json.load(f)
    return json.dumps(json_text, indent=2)