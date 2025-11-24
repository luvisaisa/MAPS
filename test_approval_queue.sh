#!/bin/bash
# Approval Queue End-to-End Test Script

BASE_URL="http://localhost:8000/api/v1"

echo "===================================="
echo "APPROVAL QUEUE END-TO-END TEST"
echo "===================================="

# Test 1: Check API health
echo -e "\n1️⃣  Testing API health..."
curl -s http://localhost:8000/health | jq '.'

# Test 2: List queue items (should be empty initially)
echo -e "\n2️⃣  Listing initial queue items..."
curl -s "$BASE_URL/approval-queue" | jq '.'

# Test 3: Get queue statistics
echo -e "\n3️⃣  Getting queue statistics..."
curl -s "$BASE_URL/approval-queue/stats" | jq '.'

# Note: To add items to the queue, we need to use the Python API directly
# or trigger a low-confidence parse. For now, let's test the endpoints.

echo -e "\n4️⃣  Testing queue filtering..."
echo "  - Filter by status (pending):"
curl -s "$BASE_URL/approval-queue?status=pending" | jq 'length'

echo "  - Filter by confidence range (0.5-0.7):"
curl -s "$BASE_URL/approval-queue?min_confidence=0.5&max_confidence=0.7" | jq 'length'

echo -e "\n✅ Basic endpoint tests completed!"
echo -e "\nTo fully test the approval queue:"
echo "  1. Manually add test items using Python"
echo "  2. Test approve/reject operations"
echo "  3. Test reprocessing"

echo -e "\nRun: python3 -c 'from src.ra_d_ps.api.routers.approval_queue import add_to_queue; item = add_to_queue(\"test.xml\", \"LIDC_Single_Session\", 0.45, \"XML\", 50000); print(f\"Added: {item.id}\")'"
