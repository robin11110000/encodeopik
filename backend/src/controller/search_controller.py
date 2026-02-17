from fastapi import Form, File, UploadFile, APIRouter
from pydantic import BaseModel
from opik import track

from src.model.Response import Response
from src.service.search_service.search_doc import search
from src.service.rag_service.agent import RAGAgent


router = APIRouter()

class AskRequest(BaseModel):
    case_id: str
    query: str


@router.get("/search-doc", response_model=Response)
@track(name="search_documents", capture_input=True, capture_output=True)
async def search_docs(uuid: str):

    search_response = search(uuid)

    if search_response == -1:
        return Response(
            status=404,
            message="Document Search results",
            data={"content": "No Data Found", "uuid": uuid},
            errors="No Data Found",
        )
    else:
        return Response(
            status=200,
            message="Document Search results",
            data={"content": search_response, "uuid": uuid},
            errors=None,
        )


@router.post("/ask", response_model=Response)
@track(name="rag_query", capture_input=True, capture_output=True)
async def ask(request: AskRequest):
    try:
        rag_agent = RAGAgent(case_id=request.case_id)
        response = rag_agent.ask(query=request.query)
        return Response(
            status=200,
            message="Query processed successfully",
            data={"response": response},
            errors=None,
        )
    except Exception as exc:
        return Response(
            status=500,
            message="Failed to process query",
            data=None,
            errors=str(exc),
        )
