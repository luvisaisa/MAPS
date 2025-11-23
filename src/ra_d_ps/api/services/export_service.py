"""Export Service - Uses ra_d_ps.exporters"""
from sqlalchemy.orm import Session

class ExportService:
    def __init__(self, db: Session):
        self.db = db

    async def export_view(self, view_name: str, format: str, limit: int = None):
        """TODO: Use ra_d_ps.exporters.excel_exporter"""
        from ..models.responses import ExportResponse
        return ExportResponse(status="not_implemented", format=format, record_count=0)

    async def export_custom(self, **kwargs):
        """TODO: Custom export"""
        from ..models.responses import ExportResponse
        return ExportResponse(status="not_implemented", format="csv", record_count=0)
