"""View Service - Access Supabase views"""
from sqlalchemy.orm import Session

class ViewService:
    def __init__(self, db: Session):
        self.db = db

    def get_view(self, view_name: str, limit: int = 100, offset: int = 0, filters=None):
        """TODO: Query Supabase materialized views"""
        return {"view_name": view_name, "data": [], "total": 0}
