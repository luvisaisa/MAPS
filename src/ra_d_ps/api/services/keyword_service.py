"""Keyword Service - Uses ra_d_ps.keyword_search_engine"""
from typing import Optional, List
from sqlalchemy.orm import Session

class KeywordService:
    def __init__(self, db: Session):
        self.db = db
        
    def list_keywords(self, limit: int, offset: int, category: Optional[str]):
        """Query keywords from database"""
        try:
            query = """
            SELECT keyword_id, term, category, subject_category, 
                   topic_tags, occurrence_count, citations
            FROM keyword_directory
            """
            
            params = []
            if category:
                query += " WHERE subject_category = %s"
                params.append(category)
                
            query += " ORDER BY occurrence_count DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            result = self.db.execute(query, params)
            return [dict(row) for row in result.fetchall()]
        except Exception as e:
            return []
    
    def get_directory(self):
        """Get complete keyword catalog"""
        query = "SELECT * FROM keyword_directory ORDER BY total_occurrences DESC"
        result = self.db.execute(query)
        return {"keywords": [dict(row) for row in result.fetchall()]}
    
    def search(self, query: str, limit: int):
        """Search keywords by term"""
        sql = """
        SELECT * FROM keyword_directory
        WHERE term ILIKE %s
        ORDER BY total_occurrences DESC
        LIMIT %s
        """
        result = self.db.execute(sql, [f"%{query}%", limit])
        return [dict(row) for row in result.fetchall()]
    
    def get_keyword(self, keyword_id: str):
        """Get keyword details"""
        query = "SELECT * FROM keyword_directory WHERE keyword_id = %s"
        result = self.db.execute(query, [keyword_id])
        row = result.fetchone()
        return dict(row) if row else None
    
    def get_occurrences(self, keyword_id: str):
        """Get keyword occurrences"""
        query = """
        SELECT * FROM keyword_occurrence_map
        WHERE keyword_id = %s
        """
        result = self.db.execute(query, [keyword_id])
        return [dict(row) for row in result.fetchall()]
    
    def list_categories(self):
        """List keyword categories"""
        query = "SELECT DISTINCT subject_category FROM keyword_directory"
        result = self.db.execute(query)
        return [row[0] for row in result.fetchall()]
    
    def list_tags(self):
        """List topic tags"""
        query = "SELECT DISTINCT unnest(topic_tags) as tag FROM keyword_directory"
        result = self.db.execute(query)
        return [row[0] for row in result.fetchall()]
    
    def extract(self, text: str):
        """Extract keywords from text"""
        # TODO: Use keyword_search_engine or keyword_normalizer
        return {"keywords": []}
