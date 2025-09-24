#!/usr/bin/env python3
"""
Script to send 10,000 test webhooks to test the transaction fix
This will help verify that merge_count is properly recorded under high load
"""

import requests
import time
import json
import random
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Configuration
WEBHOOK_URL = "https://boykomobil2000.pythonanywhere.com/webhooks/hubspot"
STATS_URL = "https://boykomobil2000.pythonanywhere.com/stats"
TOTAL_WEBHOOKS = 10000
BATCH_SIZE = 100  # Send webhooks in batches
DELAY_BETWEEN_BATCHES = 1  # seconds
MAX_WORKERS = 10  # concurrent threads

def generate_test_payload():
    """Generate a test webhook payload"""
    # Create unique identifiers that will likely create duplicates
    # This simulates real-world scenarios where multiple webhooks reference same contact
    base_ids = [f"test-contact-{i:04d}" for i in range(1, 1001)]  # 1000 unique contacts
    
    # Some webhooks will be duplicates (same unique_identifier)
    # This should trigger the merge logic
    unique_id = random.choice(base_ids)
    
    return {
        "unique_identifier": unique_id,
        "hs_object_id": f"hs-{random.randint(100000, 999999)}"
    }

def send_webhook(payload, webhook_num):
    """Send a single webhook"""
    try:
        response = requests.post(
            WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            return {"success": True, "webhook_num": webhook_num, "payload": payload}
        else:
            return {
                "success": False, 
                "webhook_num": webhook_num, 
                "error": f"HTTP {response.status_code}: {response.text}",
                "payload": payload
            }
            
    except Exception as e:
        return {
            "success": False, 
            "webhook_num": webhook_num, 
            "error": str(e),
            "payload": payload
        }

def send_webhook_batch(start_num, batch_size):
    """Send a batch of webhooks"""
    results = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all webhooks in this batch
        futures = []
        for i in range(batch_size):
            webhook_num = start_num + i
            payload = generate_test_payload()
            future = executor.submit(send_webhook, payload, webhook_num)
            futures.append(future)
        
        # Collect results
        for future in as_completed(futures):
            results.append(future.result())
    
    return results

def get_current_stats():
    """Get current processing statistics"""
    try:
        response = requests.get(STATS_URL, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def main():
    print(f"🚀 Starting to send {TOTAL_WEBHOOKS} test webhooks to {WEBHOOK_URL}")
    print(f"📊 Monitoring stats at {STATS_URL}")
    print(f"⚙️  Configuration: {BATCH_SIZE} webhooks per batch, {MAX_WORKERS} threads")
    print(f"📅 Started at: {datetime.now()}")
    print("-" * 80)
    
    # Get initial stats
    initial_stats = get_current_stats()
    print(f"📈 Initial stats: {json.dumps(initial_stats, indent=2)}")
    print("-" * 80)
    
    total_sent = 0
    total_success = 0
    total_failed = 0
    all_errors = []
    
    # Send webhooks in batches
    for batch_start in range(0, TOTAL_WEBHOOKS, BATCH_SIZE):
        current_batch_size = min(BATCH_SIZE, TOTAL_WEBHOOKS - batch_start)
        batch_num = (batch_start // BATCH_SIZE) + 1
        total_batches = (TOTAL_WEBHOOKS + BATCH_SIZE - 1) // BATCH_SIZE
        
        print(f"📦 Sending batch {batch_num}/{total_batches} ({current_batch_size} webhooks)...")
        
        batch_start_time = time.time()
        results = send_webhook_batch(batch_start, current_batch_size)
        batch_duration = time.time() - batch_start_time
        
        # Process results
        batch_success = sum(1 for r in results if r["success"])
        batch_failed = len(results) - batch_success
        
        total_sent += len(results)
        total_success += batch_success
        total_failed += batch_failed
        
        # Collect errors
        for result in results:
            if not result["success"]:
                all_errors.append(result)
        
        print(f"   ✅ Batch {batch_num}: {batch_success}/{current_batch_size} successful in {batch_duration:.1f}s")
        print(f"   📊 Overall: {total_success}/{total_sent} sent ({total_success/total_sent*100:.1f}% success)")
        
        # Show some sample errors if any
        if batch_failed > 0:
            print(f"   ❌ {batch_failed} failures in this batch")
            for error in results[-3:]:  # Show last 3 errors
                if not error["success"]:
                    print(f"      Error: {error['error']}")
        
        # Delay between batches to avoid overwhelming the server
        if batch_start + current_batch_size < TOTAL_WEBHOOKS:
            print(f"   ⏱️  Waiting {DELAY_BETWEEN_BATCHES}s before next batch...")
            time.sleep(DELAY_BETWEEN_BATCHES)
        
        print()
    
    # Final summary
    print("=" * 80)
    print(f"🎉 COMPLETED: Sent {total_sent} webhooks")
    print(f"✅ Success: {total_success} ({total_success/total_sent*100:.1f}%)")
    print(f"❌ Failed: {total_failed} ({total_failed/total_sent*100:.1f}%)")
    print(f"📅 Finished at: {datetime.now()}")
    
    if all_errors:
        print(f"\n🐛 Error Summary ({len(all_errors)} total errors):")
        error_types = {}
        for error in all_errors:
            error_msg = error["error"][:100]  # Truncate long errors
            error_types[error_msg] = error_types.get(error_msg, 0) + 1
        
        for error_msg, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
            print(f"   {count}x: {error_msg}")
    
    # Get final stats
    print("\n📊 Final stats:")
    final_stats = get_current_stats()
    print(json.dumps(final_stats, indent=2))
    
    print("\n🔍 To monitor progress over the next 1-2 days:")
    print(f"   curl {STATS_URL}")
    print("\n💡 Check individual results:")
    print(f"   curl {WEBHOOK_URL.replace('/webhooks/hubspot', '/results/test-contact-0001')}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
