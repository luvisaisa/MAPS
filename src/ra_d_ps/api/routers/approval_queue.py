"""
Approval Queue Router

Manages files awaiting approval due to low confidence scores.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
import logging
from datetime import datetime

from ..dependencies import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

# Confidence threshold for automatic processing
DEFAULT_CONFIDENCE_THRESHOLD = 0.75


class QueueItem(BaseModel):
    """Item in approval queue"""
    id: str
    filename: str
    detected_parse_case: str
    confidence: float = Field(ge=0.0, le=1.0)
    file_type: str
    file_size: int
    uploaded_at: datetime
    status: str = "pending"  # pending, approved, rejected
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    notes: Optional[str] = None


class ApprovalRequest(BaseModel):
    """Approval decision"""
    action: str = Field(..., pattern="^(approve|reject)$")
    parse_case: Optional[str] = None  # Override detected parse case
    notes: Optional[str] = None
    reviewed_by: Optional[str] = "system"


class QueueStats(BaseModel):
    """Approval queue statistics"""
    total_pending: int
    total_approved: int
    total_rejected: int
    avg_confidence: float
    low_confidence_count: int  # confidence < 0.5
    medium_confidence_count: int  # 0.5 <= confidence < 0.75
    oldest_pending: Optional[datetime] = None


# In-memory queue for now (in production, this would be in database)
_approval_queue: List[QueueItem] = []
_queue_counter = 0


@router.get("/stats", response_model=QueueStats)
async def get_queue_stats():
    """
    Get approval queue statistics.

    Returns:
        Summary statistics for the approval queue
    """
    pending_items = [item for item in _approval_queue if item.status == "pending"]
    approved_items = [item for item in _approval_queue if item.status == "approved"]
    rejected_items = [item for item in _approval_queue if item.status == "rejected"]

    confidences = [item.confidence for item in pending_items] if pending_items else [0]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0

    low_conf = len([item for item in pending_items if item.confidence < 0.5])
    med_conf = len([item for item in pending_items if 0.5 <= item.confidence < 0.75])

    oldest = min([item.uploaded_at for item in pending_items]) if pending_items else None

    return QueueStats(
        total_pending=len(pending_items),
        total_approved=len(approved_items),
        total_rejected=len(rejected_items),
        avg_confidence=avg_confidence,
        low_confidence_count=low_conf,
        medium_confidence_count=med_conf,
        oldest_pending=oldest
    )


@router.get("", response_model=List[QueueItem])
async def list_queue_items(
    status: Optional[str] = Query(None, regex="^(pending|approved|rejected)$"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    max_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    List items in approval queue.

    Args:
        status: Filter by status (pending, approved, rejected)
        min_confidence: Minimum confidence score
        max_confidence: Maximum confidence score
        limit: Maximum items to return

    Returns:
        List of queue items matching filters
    """
    items = _approval_queue.copy()

    # Apply filters
    if status:
        items = [item for item in items if item.status == status]
    if min_confidence is not None:
        items = [item for item in items if item.confidence >= min_confidence]
    if max_confidence is not None:
        items = [item for item in items if item.confidence <= max_confidence]

    # Sort by confidence (lowest first for pending items)
    if not status or status == "pending":
        items.sort(key=lambda x: x.confidence)
    else:
        items.sort(key=lambda x: x.uploaded_at, reverse=True)

    return items[:limit]


@router.get("/{item_id}", response_model=QueueItem)
async def get_queue_item(item_id: str):
    """
    Get specific queue item.

    Args:
        item_id: Queue item ID

    Returns:
        Queue item details

    Raises:
        404: Item not found
    """
    for item in _approval_queue:
        if item.id == item_id:
            return item

    raise HTTPException(status_code=404, detail=f"Queue item '{item_id}' not found")


@router.post("/{item_id}/review", response_model=QueueItem)
async def review_queue_item(
    item_id: str,
    request: ApprovalRequest
):
    """
    Review and approve/reject a queue item.

    Args:
        item_id: Queue item ID
        request: Approval decision

    Returns:
        Updated queue item

    Raises:
        404: Item not found
        400: Invalid action or item already reviewed
    """
    # Find item
    item = None
    for i, queue_item in enumerate(_approval_queue):
        if queue_item.id == item_id:
            item = queue_item
            break

    if not item:
        raise HTTPException(status_code=404, detail=f"Queue item '{item_id}' not found")

    if item.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Item already reviewed with status: {item.status}"
        )

    # Update item
    item.status = "approved" if request.action == "approve" else "rejected"
    item.reviewed_by = request.reviewed_by
    item.reviewed_at = datetime.now()
    item.notes = request.notes

    # Override parse case if provided
    if request.parse_case:
        item.detected_parse_case = request.parse_case

    logger.info(
        f"Queue item {item_id} {item.status} by {item.reviewed_by}. "
        f"Parse case: {item.detected_parse_case} (confidence: {item.confidence})"
    )

    return item


@router.post("/{item_id}/reprocess")
async def reprocess_item(item_id: str):
    """
    Reprocess an approved item through the parsing pipeline.

    Args:
        item_id: Queue item ID

    Returns:
        Processing result

    Raises:
        404: Item not found
        400: Item not approved
    """
    # Find item
    item = None
    for queue_item in _approval_queue:
        if queue_item.id == item_id:
            item = queue_item
            break

    if not item:
        raise HTTPException(status_code=404, detail=f"Queue item '{item_id}' not found")

    if item.status != "approved":
        raise HTTPException(
            status_code=400,
            detail=f"Item must be approved before reprocessing. Current status: {item.status}"
        )

    # TODO: Implement actual reprocessing logic
    # This would call the parser with the approved parse_case

    return {
        "status": "success",
        "message": f"Item {item_id} queued for reprocessing with parse case '{item.detected_parse_case}'",
        "item_id": item_id
    }


@router.delete("/{item_id}")
async def delete_queue_item(item_id: str):
    """
    Delete an item from the queue.

    Args:
        item_id: Queue item ID

    Returns:
        Success message

    Raises:
        404: Item not found
    """
    global _approval_queue

    for i, item in enumerate(_approval_queue):
        if item.id == item_id:
            _approval_queue.pop(i)
            logger.info(f"Deleted queue item {item_id}")
            return {
                "status": "success",
                "message": f"Queue item '{item_id}' deleted"
            }

    raise HTTPException(status_code=404, detail=f"Queue item '{item_id}' not found")


@router.post("/batch-review")
async def batch_review(
    action: str = Query(..., regex="^(approve|reject)$"),
    item_ids: List[str] = Query(...),
    reviewed_by: str = "system"
):
    """
    Review multiple items in batch.

    Args:
        action: approve or reject
        item_ids: List of item IDs to review
        reviewed_by: Reviewer identifier

    Returns:
        Batch operation results
    """
    results = []
    for item_id in item_ids:
        try:
            request = ApprovalRequest(
                action=action,
                reviewed_by=reviewed_by
            )
            updated_item = await review_queue_item(item_id, request)
            results.append({
                "item_id": item_id,
                "status": "success",
                "action": action
            })
        except HTTPException as e:
            results.append({
                "item_id": item_id,
                "status": "error",
                "error": e.detail
            })

    success_count = len([r for r in results if r["status"] == "success"])
    return {
        "total": len(item_ids),
        "success": success_count,
        "failed": len(item_ids) - success_count,
        "results": results
    }


# Helper function to add items to queue (called from parse detection)
def add_to_queue(
    filename: str,
    detected_parse_case: str,
    confidence: float,
    file_type: str,
    file_size: int
) -> QueueItem:
    """
    Add item to approval queue if confidence is below threshold.

    Args:
        filename: Original filename
        detected_parse_case: Detected parse case
        confidence: Confidence score
        file_type: File type
        file_size: File size in bytes

    Returns:
        Queue item if added, None if auto-approved
    """
    global _queue_counter

    # Auto-approve if confidence is high enough
    if confidence >= DEFAULT_CONFIDENCE_THRESHOLD:
        logger.info(f"Auto-approved: {filename} (confidence: {confidence})")
        return None

    # Add to queue
    _queue_counter += 1
    item = QueueItem(
        id=f"q_{_queue_counter}",
        filename=filename,
        detected_parse_case=detected_parse_case,
        confidence=confidence,
        file_type=file_type,
        file_size=file_size,
        uploaded_at=datetime.now(),
        status="pending"
    )

    _approval_queue.append(item)
    logger.info(f"Added to queue: {filename} (confidence: {confidence})")

    return item
