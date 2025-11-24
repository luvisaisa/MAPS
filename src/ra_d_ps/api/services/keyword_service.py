"""Keyword Service - Uses ra_d_ps.keyword_search_engine"""
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
import csv
import io

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

    async def import_definitions_csv(self, file) -> Dict:
        """Bulk import keyword definitions from CSV"""
        try:
            content = await file.read()
            csv_data = io.StringIO(content.decode('utf-8'))
            reader = csv.DictReader(csv_data)

            imported = 0
            errors = []

            for row in reader:
                try:
                    term = row.get('term')
                    definition = row.get('definition')
                    source_refs = row.get('source_refs', '')
                    vocabulary_source = row.get('vocabulary_source', '')

                    if not term or not definition:
                        errors.append(f"Missing required fields: {row}")
                        continue

                    # Insert or update canonical_keywords table
                    query = """
                    INSERT INTO canonical_keywords
                        (term, definition, source_refs, vocabulary_source)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (term)
                    DO UPDATE SET
                        definition = EXCLUDED.definition,
                        source_refs = EXCLUDED.source_refs,
                        vocabulary_source = EXCLUDED.vocabulary_source
                    """
                    self.db.execute(query, [term, definition, source_refs, vocabulary_source])
                    imported += 1

                except Exception as e:
                    errors.append(f"Error importing row {row}: {str(e)}")

            self.db.commit()
            return {
                "imported": imported,
                "errors": errors,
                "total_rows": imported + len(errors)
            }

        except Exception as e:
            self.db.rollback()
            return {"error": str(e), "imported": 0}

    def update_definition(self, keyword_id: str, data: Dict) -> Optional[Dict]:
        """Update keyword definition"""
        try:
            query = """
            UPDATE canonical_keywords
            SET definition = %s,
                source_refs = %s,
                vocabulary_source = %s
            WHERE keyword_id = %s
            RETURNING keyword_id, term, definition, source_refs, vocabulary_source
            """
            result = self.db.execute(query, [
                data.get('definition'),
                data.get('source_refs'),
                data.get('vocabulary_source'),
                keyword_id
            ])
            self.db.commit()

            row = result.fetchone()
            return dict(row) if row else None

        except Exception as e:
            self.db.rollback()
            return None

    def get_citations(self, keyword_id: str) -> Optional[Dict]:
        """Get citations for keyword definition"""
        try:
            query = """
            SELECT keyword_id, term, definition, source_refs, vocabulary_source
            FROM canonical_keywords
            WHERE keyword_id = %s
            """
            result = self.db.execute(query, [keyword_id])
            row = result.fetchone()

            if not row:
                return None

            return {
                "keyword_id": row[0],
                "term": row[1],
                "definition": row[2],
                "citations": row[3] or "",
                "vocabulary_source": row[4] or ""
            }

        except Exception as e:
            return None

    def add_alias(self, keyword_id: str, alias: str, synonym_type: str = "variant") -> Optional[Dict]:
        """Add synonym/alias to keyword"""
        try:
            query = """
            INSERT INTO canonical_keyword_aliases (keyword_id, alias, synonym_type)
            VALUES (%s, %s, %s)
            RETURNING alias_id, keyword_id, alias, synonym_type
            """
            result = self.db.execute(query, [keyword_id, alias, synonym_type])
            self.db.commit()

            row = result.fetchone()
            return dict(row) if row else None

        except Exception as e:
            self.db.rollback()
            return None
