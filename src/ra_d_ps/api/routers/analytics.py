"""
Analytics Router

Endpoints for analytics and statistics.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import logging

from ..models.responses import AnalyticsResponse
from ..dependencies import get_db
from ..services.analytics_service import AnalyticsService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/summary")
async def get_summary(db: Session = Depends(get_db)):
    """Database overview statistics"""
    service = AnalyticsService(db)
    return service.get_summary()


@router.get("/parse-cases")
async def get_parse_case_distribution(db: Session = Depends(get_db)):
    """Parse case distribution"""
    service = AnalyticsService(db)
    return service.get_parse_case_distribution()


@router.get("/keywords")
async def get_keyword_stats(db: Session = Depends(get_db)):
    """Keyword statistics"""
    service = AnalyticsService(db)
    return service.get_keyword_stats()


@router.get("/inter-rater")
async def get_inter_rater_reliability(db: Session = Depends(get_db)):
    """Inter-rater reliability metrics"""
    service = AnalyticsService(db)
    return service.get_inter_rater_reliability()


@router.get("/completeness")
async def get_data_completeness(db: Session = Depends(get_db)):
    """Data completeness metrics"""
    service = AnalyticsService(db)
    return service.get_completeness_metrics()


@router.get("/case-identifier")
async def get_case_identifier_stats(db: Session = Depends(get_db)):
    """Case validation statistics"""
    service = AnalyticsService(db)
    return service.get_case_identifier_stats()
