from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.vector import qa_response, qa_hybrid_search_vec_rff,doc_hybrid_search_vec_rff,doc_hybrid_search_bm25_vec
from app.service.search_service import SearchService
from pydantic import BaseModel
from app.schema.base import BaseResponse
import logging

logging.basicConfig(level=logging.INFO)
router = APIRouter(prefix='/knowledge-search', tags=['knowledge-search'])
from app.config.database import get_db
from app.service.rbac import require_admin,require_any_role
from app.schema.auth import UserReadWithRole

class SearchRequest(BaseModel):
    query: str

@router.post("/", response_model=BaseResponse)
def search(request: SearchRequest, db: Session = Depends(get_db),
           _: UserReadWithRole = Depends(require_any_role)):
    query = request.query
    # QA 一次命中
    qa = SearchService.qa_response(query=query,score=0.95, top_n=1) #qa_response(query)
    # 混合搜索

    qa_hybrid =SearchService.qa_hybrid_search_vec_rff(query=query) #qa_hybrid_search_vec_rff(query)
    doc_hybrid_rff = SearchService.doc_hybrid_search_vec_rff(query=query) #doc_hybrid_search_vec_rff(query)
    doc_hybrid_bm25 = SearchService.doc_hybrid_search_vec_rff_with_fallback(query=query,top_n=5, use_rerank=True) #doc_hybrid_search_bm25_vec(query)
    item = {
        'qa': qa,
        'qa_hybrid': qa_hybrid,
        'doc_hybrid_rff': doc_hybrid_rff,
        'doc_hybrid_bm25': doc_hybrid_bm25
    }
    return BaseResponse(data=item)


@router.post("/qa")
async def qa_result(query: str, db: Session = Depends(get_db),
                   _: UserReadWithRole = Depends(require_admin)):
    return qa_response(query)

@router.post("/qa_hybridsearch")
def qa_hybridsearch(query: str, db: Session = Depends(get_db),
                    _: UserReadWithRole = Depends(require_admin)):
    return qa_hybrid_search_vec_rff(query)


@router.post("/doc_hybridsearch")
def doc_hybridsearch(query: str, db: Session = Depends(get_db),
                     _: UserReadWithRole = Depends(require_admin)):
    return doc_hybrid_search_vec_rff(query)




@router.post("/doc_hybrid_search_bm25")
def doc_hybrid_search_bm25(query: str, db: Session = Depends(get_db),
                           _: UserReadWithRole = Depends(require_admin)):
    return doc_hybrid_search_bm25_vec(query)


