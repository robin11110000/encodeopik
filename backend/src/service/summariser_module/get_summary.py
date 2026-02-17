import os
import json
import base64
from pathlib import Path
from src.service.loan_core.utils import load_json
from src.service.doc_extractor.logger import get_logger

# Initialize logger for this module
logger = get_logger(__name__)


def get_markdown(folder_id, folder_name):

    base_dir = os.getcwd()
    kpi_path = (
        base_dir + f"/resources/{folder_id}/{folder_name}/output/{folder_name}.json"
    )
    kpi_path = Path(kpi_path).resolve()
    logger.info(f"Loading KPI file from: {kpi_path}")
    with open(kpi_path) as fp:
        kpi_data = json.load(fp)

    summary_file_path = (
        base_dir
        + f"/resources/{folder_id}/{folder_name}/output/{folder_name}_summary.txt"
    )
    summary_file_path = Path(summary_file_path).resolve()

    with open(summary_file_path) as fp:
        summary = fp.read()

    return {"kpis": kpi_data, "summary": summary}


def get_document_data(folder_id, folder_name):

    base_dir = os.getcwd()
    output_path = Path(
        base_dir + f"/resources/{folder_id}/{folder_name}/output/"
    ).resolve()

    matched_files = [
        f
        for f in output_path.iterdir()
        if f.is_file() and f.name.endswith((".png", ".PNG",".jpg",".JPG")) and "page_" in f.name
    ]

    matched_files.sort(key=lambda f: int(f.stem.split("_")[-1]))

    images = list()

    for image_path in matched_files:

        image_path = Path(image_path)
        with open(image_path, "rb") as f:
            img_bytes = f.read()

        img_b64 = base64.b64encode(img_bytes).decode("utf-8")

        images.append(img_b64)

    metadata = get_markdown(folder_id, folder_name)

    resp = {"images": images}
    resp.update(metadata)

    return resp


def check_for_fraud_image(folder_id, folder_name):
    logger.info(f"Checking for fraud image in {folder_name} for folder ID: {folder_id}")
    base_dir = os.getcwd()
    output_path = Path(
        base_dir + f"/resources/{folder_id}/{folder_name}/output/"
    ).resolve()

    json_path = f"{output_path}/identity-documents_fraud_report.json"
    image_path = f"{output_path}/identity-documents_components_analyze.jpg"
    fraud_json = load_json(json_path)
    fraud_json = json.loads(fraud_json)
    is_authentic = fraud_json["is_authentic"]

    if is_authentic:
        logger.info("Document is authentic. No fraud image to return.")
        return None

    else:
        logger.info("Document is not authentic. Returning fraud image.")
        image_path = Path(image_path)
        with open(image_path, "rb") as f:
            img_bytes = f.read()

        img_b64 = base64.b64encode(img_bytes).decode("utf-8")

        return img_b64
