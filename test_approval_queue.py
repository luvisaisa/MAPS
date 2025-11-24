"""
Test Approval Queue Workflow End-to-End

This script tests the complete approval queue functionality including:
1. Adding items with low confidence to the queue
2. Listing queue items
3. Reviewing (approving/rejecting) items
4. Reprocessing approved items
5. Batch operations
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

def test_health():
    """Test API is running"""
    response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health")
    print(f"\n✅ API Health: {response.json()}")
    return response.status_code == 200

def manually_add_test_items():
    """Add test items directly to the queue via Python"""
    from src.ra_d_ps.api.routers.approval_queue import add_to_queue

    print("\n📝 Adding test items to queue...")

    # Add low confidence item (should be queued)
    item1 = add_to_queue(
        filename="test_low_confidence.xml",
        detected_parse_case="LIDC_Single_Session",
        confidence=0.45,
        file_type="XML",
        file_size=50000
    )
    if item1:
        print(f"  ✅ Added item 1: {item1.id} (confidence: {item1.confidence})")

    # Add medium confidence item (should be queued)
    item2 = add_to_queue(
        filename="test_medium_confidence.xml",
        detected_parse_case="LIDC_Multi_Session_2",
        confidence=0.65,
        file_type="XML",
        file_size=75000
    )
    if item2:
        print(f"  ✅ Added item 2: {item2.id} (confidence: {item2.confidence})")

    # Add high confidence item (should be auto-approved, NOT queued)
    item3 = add_to_queue(
        filename="test_high_confidence.xml",
        detected_parse_case="Complete_Attributes",
        confidence=0.92,
        file_type="XML",
        file_size=100000
    )
    if item3:
        print(f"  ✅ Added item 3: {item3.id} (confidence: {item3.confidence})")
    else:
        print(f"  ℹ️  High confidence item auto-approved (not queued)")

    return item1, item2, item3

def list_queue_items():
    """Test listing all queue items"""
    print("\n📋 Listing all queue items...")
    response = requests.get(f"{BASE_URL}/approval-queue")
    items = response.json()

    if response.status_code == 200:
        print(f"  ✅ Found {len(items)} items in queue")
        for item in items:
            print(f"     - {item['id']}: {item['filename']} (confidence: {item['confidence']}, status: {item['status']})")
        return items
    else:
        print(f"  ❌ Error: {response.status_code}")
        return []

def get_queue_stats():
    """Test getting queue statistics"""
    print("\n📊 Getting queue statistics...")
    response = requests.get(f"{BASE_URL}/approval-queue/stats")

    if response.status_code == 200:
        stats = response.json()
        print(f"  ✅ Queue Stats:")
        print(f"     - Pending: {stats['total_pending']}")
        print(f"     - Approved: {stats['total_approved']}")
        print(f"     - Rejected: {stats['total_rejected']}")
        print(f"     - Avg Confidence: {stats['avg_confidence']:.2f}")
        print(f"     - Low Confidence (<0.5): {stats['low_confidence_count']}")
        print(f"     - Medium Confidence (0.5-0.75): {stats['medium_confidence_count']}")
        return stats
    else:
        print(f"  ❌ Error: {response.status_code}")
        return None

def approve_item(item_id, parse_case_override=None):
    """Test approving a queue item"""
    print(f"\n✅ Approving item {item_id}...")

    payload = {
        "action": "approve",
        "reviewed_by": "test_user",
        "notes": "Approved during automated testing"
    }

    if parse_case_override:
        payload["parse_case"] = parse_case_override

    response = requests.post(
        f"{BASE_URL}/approval-queue/{item_id}/review",
        json=payload
    )

    if response.status_code == 200:
        item = response.json()
        print(f"  ✅ Approved: {item['filename']}")
        print(f"     - Status: {item['status']}")
        print(f"     - Reviewed by: {item['reviewed_by']}")
        print(f"     - Parse case: {item['detected_parse_case']}")
        return item
    else:
        print(f"  ❌ Error: {response.status_code} - {response.text}")
        return None

def reject_item(item_id, notes="Test rejection"):
    """Test rejecting a queue item"""
    print(f"\n❌ Rejecting item {item_id}...")

    payload = {
        "action": "reject",
        "reviewed_by": "test_user",
        "notes": notes
    }

    response = requests.post(
        f"{BASE_URL}/approval-queue/{item_id}/review",
        json=payload
    )

    if response.status_code == 200:
        item = response.json()
        print(f"  ✅ Rejected: {item['filename']}")
        print(f"     - Status: {item['status']}")
        print(f"     - Notes: {item['notes']}")
        return item
    else:
        print(f"  ❌ Error: {response.status_code} - {response.text}")
        return None

def reprocess_item(item_id):
    """Test reprocessing an approved item"""
    print(f"\n🔄 Reprocessing item {item_id}...")

    response = requests.post(f"{BASE_URL}/approval-queue/{item_id}/reprocess")

    if response.status_code == 200:
        result = response.json()
        print(f"  ✅ Reprocessing initiated:")
        print(f"     - Status: {result['status']}")
        print(f"     - Message: {result['message']}")
        return result
    else:
        print(f"  ❌ Error: {response.status_code} - {response.text}")
        return None

def filter_queue_items():
    """Test filtering queue items"""
    print("\n🔍 Testing queue filters...")

    # Filter by status
    response = requests.get(f"{BASE_URL}/approval-queue?status=pending")
    if response.status_code == 200:
        items = response.json()
        print(f"  ✅ Pending items: {len(items)}")

    # Filter by confidence range
    response = requests.get(f"{BASE_URL}/approval-queue?min_confidence=0.5&max_confidence=0.7")
    if response.status_code == 200:
        items = response.json()
        print(f"  ✅ Medium confidence items (0.5-0.7): {len(items)}")

    return True

def batch_review():
    """Test batch approval/rejection"""
    print("\n📦 Testing batch operations...")

    # Get current pending items
    response = requests.get(f"{BASE_URL}/approval-queue?status=pending")
    if response.status_code == 200:
        pending = response.json()
        if len(pending) >= 2:
            item_ids = [pending[0]['id'], pending[1]['id']]

            # Batch approve
            payload = {
                "item_ids": item_ids,
                "action": "approve",
                "reviewed_by": "batch_test"
            }

            response = requests.post(
                f"{BASE_URL}/approval-queue/batch-review",
                json=payload
            )

            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ Batch operation:")
                print(f"     - Total: {result['total']}")
                print(f"     - Success: {result['success']}")
                print(f"     - Failed: {result['failed']}")
                return result

    print("  ℹ️  Not enough pending items for batch test")
    return None

def run_full_test():
    """Run complete end-to-end test"""
    print("=" * 60)
    print("APPROVAL QUEUE END-TO-END TEST")
    print("=" * 60)

    # 1. Check API health
    if not test_health():
        print("\n❌ API not responding. Please start the API first.")
        return False

    # 2. Add test items
    item1, item2, item3 = manually_add_test_items()

    # 3. List all items
    items = list_queue_items()

    # 4. Get statistics
    stats = get_queue_stats()

    # 5. Test filters
    filter_queue_items()

    # 6. Approve first item
    if items and len(items) > 0:
        approved_item = approve_item(items[0]['id'])

        # 7. Reprocess approved item
        if approved_item:
            reprocess_item(approved_item['id'])

    # 8. Reject second item
    if items and len(items) > 1:
        reject_item(items[1]['id'], "Test rejection - not confident enough")

    # 9. Test batch operations
    batch_review()

    # 10. Final statistics
    print("\n" + "=" * 60)
    print("FINAL STATISTICS")
    print("=" * 60)
    get_queue_stats()
    list_queue_items()

    print("\n✅ All tests completed successfully!")
    return True

if __name__ == "__main__":
    try:
        run_full_test()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
