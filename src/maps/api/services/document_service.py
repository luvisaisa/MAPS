"""Document Service"""
from typing import Optional, List
from sqlalchemy.orm import Session

class DocumentService:
    def __init__(self, db: Session):
        self.db = db

    def list_documents(self, limit: int, offset: int, parse_case: Optional[str]):
        """TODO: Query documents table"""
        return []

    def get_document(self, document_id: str):
        """TODO: Get specific document"""
        return None

    def delete_document(self, document_id: str) -> bool:
        """TODO: Delete document"""
        return False

    def filter_documents(self, parse_case, start_date, end_date, has_keywords, limit):
        """TODO: Advanced filtering"""
        return []
