from fastapi import Form, File, UploadFile, APIRouter
from opik import track

from src.model.Response import Response
from src.service.evaluator_service.evaluator import evaluate


router = APIRouter()


@router.get("/evaluate-doc", response_model=Response)
@track(name="evaluate_documents", capture_input=True, capture_output=True)
async def evaluate_docs(uuid: str):
    # uuid = "0eb98f46-908a-4734-a4e5-645b6d7db032"

    agg_summary, fraud_summary = evaluate(uuid)
    return Response(
        status=200,
        message="Document Evaluation done",
        data={
            "content": agg_summary,
            "uuid": uuid
        },
        errors=fraud_summary,
    )
