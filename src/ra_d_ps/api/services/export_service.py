"""Export Service - Uses pandas for export"""
from sqlalchemy.orm import Session
import pandas as pd
from ..models.responses import ExportResponse


class ExportService:
    def __init__(self, db: Session):
        self.db = db

    async def export_view(self, view_name: str, format: str, limit: int = None):
        """Export Supabase view to file"""
        try:
            # Query view
            query = f"SELECT * FROM {view_name}"
            if limit:
                query += f" LIMIT {limit}"

            result = self.db.execute(query)
            data = [dict(row) for row in result.fetchall()]
            df = pd.DataFrame(data)

            if format == "csv":
                filename = f"{view_name}.csv"
                df.to_csv(filename, index=False)
            elif format == "excel":
                filename = f"{view_name}.xlsx"
                df.to_excel(filename, index=False, engine='openpyxl')
            else:
                filename = f"{view_name}.json"
                df.to_json(filename, orient="records")

            return ExportResponse(
                status="success",
                format=format,
                filename=filename,
                record_count=len(data)
            )
        except Exception as e:
            return ExportResponse(
                status="error",
                format=format,
                record_count=0
            )

    async def export_custom(self, **kwargs):
        """Custom export with filtering"""
        return await self.export_view(
            kwargs.get("view_name", "documents"),
            kwargs.get("format", "csv")
        )
