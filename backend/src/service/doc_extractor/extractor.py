from pathlib import Path
import json

from landingai_ade import LandingAIADE
from landingai_ade.lib import pydantic_to_json_schema
from PIL import Image, ImageDraw
import pymupdf

from src.service.doc_extractor.logger import get_logger

# 🔹 Opik tracing
from src.service.opik_tracing import trace_with_metadata
import opik


# Define colors for each chunk type
CHUNK_TYPE_COLORS = {
    "chunkText": (40, 167, 69),
    "chunkTable": (0, 123, 255),
    "chunkMarginalia": (111, 66, 193),
    "chunkFigure": (255, 0, 255),
    "chunkLogo": (144, 238, 144),
    "chunkCard": (255, 165, 0),
    "chunkAttestation": (0, 255, 255),
    "chunkScanCode": (255, 193, 7),
    "chunkForm": (220, 20, 60),
    "tableCell": (173, 216, 230),
    "table": (70, 130, 180),
}


class DocumentExtractor:
    """Wrapper for parsing, extracting, and visualizing documents using Landing AI ADE."""

    def __init__(self, client: LandingAIADE, model="dpt-2-latest"):
        self.logger = get_logger(__name__)
        self.client = client
        self.model = model
        self.document_types = {}

    def add_schema(self, name, schema_model):
        self.logger.info(f"Registering schema '{name}'")
        self.document_types[name] = schema_model

    # ------------------------------------------------------------------
    # ADE PARSING
    # ------------------------------------------------------------------
    @trace_with_metadata(
        name="document_parsing",
        capture_input=True,
        capture_output=False
    )
    def parse(self, document_path: str):
        self.logger.info(f"Parsing document: {document_path} with model: {self.model}")

        with opik.start_as_current_span(name="ade_parsing") as span:
            resp = self.client.parse(
                document=Path(document_path),
                model=self.model
            )
            span.metadata = {
                "document_path": document_path,
                "model": self.model
            }

        self.logger.info("Parsing complete")
        return resp

    # ------------------------------------------------------------------
    # STRUCTURED EXTRACTION
    # ------------------------------------------------------------------
    @trace_with_metadata(
        name="structured_extraction",
        capture_input=True,
        capture_output=True
    )
    def extract(self, markdown: str, document_type: str):
        if document_type not in self.document_types:
            raise ValueError(
                f"Unknown document_type: {document_type}. "
                f"Registered: {list(self.document_types.keys())}"
            )

        with opik.start_as_current_span(name="schema_extraction") as span:
            schema = pydantic_to_json_schema(self.document_types[document_type])
            resp = self.client.extract(schema=schema, markdown=markdown)

            span.metadata = {
                "document_type": document_type,
                "fields_extracted": len(resp.extraction)
            }

        return resp.extraction, resp.extraction_metadata

    # ------------------------------------------------------------------
    # END-TO-END DOCUMENT EXTRACTION
    # ------------------------------------------------------------------
    @trace_with_metadata(
        name="document_extraction_pipeline",
        capture_input=True,
        capture_output=True
    )
    def run(self, document_path: str, document_type: str, output_dir: str):
        self.logger.info(
            f"Running extraction | doc={document_path} | type={document_type}"
        )

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        parse_resp = self.parse(document_path)

        base_name = Path(document_path).stem
        (output_dir / f"{document_type}_parsed.md").write_text(parse_resp.markdown)
        (output_dir / f"{document_type}_parsed.txt").write_text(parse_resp.markdown)

        extraction, metadata = self.extract(parse_resp.markdown, document_type)

        return extraction, metadata, parse_resp

    # ------------------------------------------------------------------
    # VISUALIZATION
    # ------------------------------------------------------------------
    @trace_with_metadata(
        name="draw_bounding_boxes",
        capture_input=False,
        capture_output=False
    )
    def draw_bounding_boxes(self, parse_response, document_path, document_type, output_dir=None):
        """Draw bounding boxes around extracted chunks."""

        def create_annotated_image(image, groundings, page_num=0):
            annotated_img = image.copy()
            draw = ImageDraw.Draw(annotated_img)
            img_width, img_height = image.size

            for gid, grounding in groundings.items():
                if hasattr(grounding, "page") and grounding.page != page_num:
                    continue

                box = grounding.box
                x1 = int(box.left * img_width)
                y1 = int(box.top * img_height)
                x2 = int(box.right * img_width)
                y2 = int(box.bottom * img_height)

                if x2 <= x1 or y2 <= y1:
                    continue

                color = CHUNK_TYPE_COLORS.get(
                    getattr(grounding, "type", "UNKNOWN"),
                    (128, 128, 128)
                )

                draw.rectangle([x1, y1, x2, y2], outline=color, width=3)

            return annotated_img

        document_path = Path(document_path)
        output_dir = Path(output_dir or document_path.parent)
        output_dir.mkdir(parents=True, exist_ok=True)

        if document_path.suffix.lower() == ".pdf":
            pdf = pymupdf.open(document_path)
            for page_num, page in enumerate(pdf):
                pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                annotated = create_annotated_image(
                    img,
                    parse_response.grounding,
                    page_num
                )
                annotated.save(output_dir / f"{document_type}_page_{page_num + 1}.png")
            pdf.close()
        else:
            img = Image.open(document_path).convert("RGB")
            annotated = create_annotated_image(img, parse_response.grounding)
            annotated.save(output_dir / f"{document_type}_page_1.png")
