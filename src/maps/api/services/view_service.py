"""View Service - Access Supabase views"""
from sqlalchemy.orm import Session

class ViewService:
    def __init__(self, db: Session):
        self.db = db

    def get_view(self, view_name: str, limit: int = 100, offset: int = 0, filters=None):
        """Query Supabase materialized view"""
        try:
            query = f"SELECT * FROM {view_name}"
            
            if filters:
                conditions = [f"{k} = %s" for k in filters.keys()]
                query += " WHERE " + " AND ".join(conditions)
                
            query += f" LIMIT {limit} OFFSET {offset}"
            
            params = list(filters.values()) if filters else []
            result = self.db.execute(query, params)
            data = [dict(row) for row in result.fetchall()]
            
            return {
                "view_name": view_name,
                "data": data,
                "total": len(data),
                "limit": limit,
                "offset": offset
            }
        except Exception as e:
            return {
                "view_name": view_name,
                "data": [],
                "total": 0,
                "error": str(e)
            }
