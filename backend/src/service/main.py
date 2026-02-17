"""
Document Extraction Pipeline
This script processes documents (bank statements, passports) using LandingAI's 
document extraction service to extract structured metadata and visualize field 
locations with bounding boxes.
"""

from pathlib import Path
import json
from landingai_ade import LandingAIADE
from src.service.doc_extractor.extractor import DocumentExtractor
from src.service.doc_extractor.schemas import (Account,
                                   IdentityDocument,
                                   TaxStatement,
                                   IncomeProof,
                                   UtilityBill,
                                   CreditReport)
from dotenv import load_dotenv
from src.service.doc_extractor.utils import (
    get_chunk_by_id,
    extract_bbox_from_response,
    draw_bounding_box,
    list_folders_with_files,
    get_files_in_folder
)
from src.service.doc_extractor.logger import get_logger

# Initialize logger for this module
logger = get_logger(__name__)

# Configuration constants
MODEL = "dpt-2-latest"

# Load environment variables from .env file
load_dotenv()

# Map document types to their corresponding schema classes
schema_mapping = {
    'bank-statements': Account,
    'identity-documents': IdentityDocument,
    'credit-reports': CreditReport,
    'income-proof': IncomeProof,
    'tax-statements': TaxStatement,
    'utility-bills': UtilityBill
}


def build_extractor(model: str, document_type: str) -> DocumentExtractor:
    """
    Initialize and configure a DocumentExtractor instance.
    
    Args:
        model: The model identifier to use for extraction
        document_type: Type of document to process (e.g., 'bank_statement', 'passport')
    
    Returns:
        Configured DocumentExtractor instance with the appropriate schema
    """
    logger.info(f"Building extractor with model: {model}")
    
    # Create extractor with LandingAI client
    extractor = DocumentExtractor(client=LandingAIADE(), model=model)
    
    # Register the schema for the specified document type
    extractor.add_schema(document_type, schema_mapping[document_type])
    
    return extractor


def compute_field_bboxes(extractor, document_type, parse_resp, extracted_metadata):
    """
    Compute bounding boxes for each extracted field in the document.
    
    This function maps extracted metadata fields to their physical locations
    in the document by retrieving chunk references and extracting bbox coordinates.
    
    Args:
        extractor: DocumentExtractor instance with registered schemas
        document_type: Type of document being processed
        parse_resp: Parsing response containing document chunks
        extracted_metadata: Dictionary of extracted field values with references
    
    Returns:
        Dictionary mapping field names to their bounding box coordinates
    """
    # Retrieve the schema for the document type
    schema = extractor.document_types.get(document_type)
    
    if schema is None:
        logger.warning(
            f"No schema registered for document_type '{document_type}'. "
            f"Registered: {list(extractor.document_types.keys())}"
        )
        return {}
    
    # Get document chunks from parse response
    chunks = parse_resp.chunks
    
    # Extract schema field names
    schema_keys = list(schema.model_fields.keys())
    
    # Create mapping of schema keys to their extracted values
    schema_values = {key: extracted_metadata.get(key) for key in schema_keys}
    
    # Compute bounding boxes for each field
    field_bboxes = {}
    
    for key in schema_keys:
        # Get metadata for this field
        meta = extracted_metadata.get(key)
        if meta is None:
            continue
        
        # Collect all references for this field
        references = []
        
        if isinstance(meta, dict):
            # Direct dictionary with references
            references = meta.get("references") or []
        elif isinstance(meta, list):
            # List of items, each potentially containing references
            for item in meta:
                if isinstance(item, dict):
                    refs = item.get("references")
                    if isinstance(refs, list):
                        references.extend(refs)
        
        # Skip if no references found
        if not references:
            continue
        
        # Use the first reference to locate the field
        first_ref = references[0]
        chunk_id = first_ref
        
        if not chunk_id:
            continue
        
        # Retrieve the chunk by its ID
        chunk = get_chunk_by_id(chunks, chunk_id)
        if not chunk:
            continue
        
        # Extract bounding box coordinates from the chunk
        bbox = extract_bbox_from_response(chunk)
        field_bboxes[key] = bbox
    
    return field_bboxes


def run(document_path: str | Path, document_type: str, output_dir: str | Path, model: str) -> dict:
    """
    Execute the document extraction pipeline for a single document.
    
    This function:
    1. Builds an extractor with the specified model
    2. Extracts structured data from the document
    3. Computes bounding boxes for each field
    4. Generates visualization images with bounding boxes
    5. Saves extracted data as JSON
    
    Args:
        document_path: Path to the input document file
        document_type: Type of document (must match schema_mapping keys)
        output_dir: Directory where outputs will be saved
        model: Model identifier for extraction
    
    Returns:
        Dictionary containing the extracted data
    """
    logger.info(
        f"Run start | doc: {document_path} | type: {document_type} | "
        f"out: {output_dir} | model: {model}"
    )
    
    # Initialize the extractor with appropriate schema
    extractor = build_extractor(model, document_type)
    
    # Ensure output directory exists
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run extraction process
    extraction, extracted_metadata, parse_resp = extractor.run(
        document_path=document_path,
        document_type=document_type,
        output_dir=output_dir,
    )
    
    # Draw bounding boxes for all chunks
    try:
        extractor.draw_bounding_boxes(parse_resp, document_path,document_type, output_dir)
    except Exception as e:
        logger.warning(f"Failed to draw bounding boxes: {e}")

    # Save extracted data as JSON file
    json_output_path = output_dir / f"{document_type}.json"
    json_output_path.write_text(json.dumps(extraction, indent=2))
    
    logger.info(f"Saved outputs to: {output_dir}")
    
    return extraction


def process_documents(folder_id: str,document_type: str, model: str = MODEL) -> list[dict]:
    """
    Processes a document of a given type under a specific folder ID.

    It finds the first file in the given document type folder,
    runs the extraction pipeline using the provided model,
    and returns the extracted results with metadata.

    Args:
        folder_id (str): Unique ID of the folder containing documents.
        document_type (str): Type of document to process (e.g., 'bank-statements').
        model (str, optional): Model name to use for extraction. Defaults to MODEL.

    Returns:
        dict: Contains folder_id, document_type, document_path, output_dir, and extraction results.
    """
    # Construct base path from folder_id 
    # Navigate up from backend/src/service/main.py to backend/, then append resources/folder_id
    base_path = str((Path(__file__).parent.parent.parent / "resources" / folder_id).resolve())
    
    logger.info(f"Processing document for folder_id: {folder_id}")
    logger.info(f"Base path: {base_path}")
        
    try:
        # Process each folder (document type) found in base path
        logger.info(f"Running for {document_type}")
        
        # Extract folder name and first file
        folder = document_type
        file_path = f"{base_path}/{document_type}"
        file = get_files_in_folder(file_path)[0]
        
        # Construct paths
        document_path = file 
        document_type = folder
        output_dir = f"{base_path}/{folder}/output"
        
        # Run extraction pipeline for this document
        extraction_result = run(document_path, document_type, output_dir, model)
        
        # Store result with metadata
        result = {
            'folder_id': folder_id,
            'document_type': document_type,
            'document_path': document_path,
            'output_dir': output_dir,
            'extraction': extraction_result
        }
            
    except Exception as exc:
        # Log the full exception traceback
        logger.exception("An error occurred while running the pipeline")
        raise
    
    logger.info(f"Successfully processed {document_type}")
    return result, folder_id, document_type, base_path
