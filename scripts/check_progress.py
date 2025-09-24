#!/usr/bin/env python3
"""
Simple script to check the progress of webhook processing
Run this periodically to monitor the 10k webhook test
"""

import requests
import json
from datetime import datetime

STATS_URL = "https://boykomobil2000.pythonanywhere.com/stats"

def main():
    print(f"📊 Checking processing stats at {datetime.now()}")
    print("=" * 60)
    
    try:
        response = requests.get(STATS_URL, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Error: HTTP {response.status_code}")
            print(response.text)
            return
            
        stats = response.json()
        
        # Status breakdown
        print("📈 Status Breakdown:")
        for status_info in stats.get("status_breakdown", []):
            status = status_info["status"]
            count = status_info["count"]
            avg_merge = status_info.get("avg_merge_count", 0) or 0
            print(f"   {status.upper():>8}: {count:>6} jobs (avg merges: {avg_merge:.2f})")
        
        print()
        
        # Merge analysis
        merge_analysis = stats.get("merge_analysis", {})
        if merge_analysis:
            print("🔍 Merge Analysis:")
            total_done = merge_analysis.get("total_done_jobs", 0)
            jobs_with_merges = merge_analysis.get("jobs_with_merges", 0)
            jobs_zero_merges = merge_analysis.get("jobs_zero_merges", 0)
            avg_merge_count = merge_analysis.get("avg_merge_count", 0) or 0
            
            print(f"   Total completed jobs: {total_done}")
            print(f"   Jobs with merges:     {jobs_with_merges}")
            print(f"   Jobs with zero merges: {jobs_zero_merges}")
            print(f"   Average merge count:  {avg_merge_count:.2f}")
        
        print()
        
        # Data quality metrics
        data_quality = stats.get("data_quality", {})
        if data_quality:
            print("🎯 Data Quality:")
            merge_success_rate = data_quality.get("merge_success_rate", 0)
            zero_merge_rate = data_quality.get("zero_merge_rate", 0)
            
            print(f"   Merge success rate:   {merge_success_rate}%")
            print(f"   Zero merge rate:      {zero_merge_rate}%")
            
            # Highlight potential issues
            if zero_merge_rate > 10:
                print(f"   ⚠️  HIGH zero merge rate! This indicates the bug is still present.")
            elif zero_merge_rate < 5:
                print(f"   ✅ Low zero merge rate - transaction fix appears to be working!")
            else:
                print(f"   🤔 Moderate zero merge rate - monitor closely")
        
        print()
        
        # Recent activity
        recent_activity = stats.get("recent_activity", {})
        if recent_activity:
            print("⏱️  Recent Activity (last hour):")
            recent_jobs = recent_activity.get("recent_jobs", 0)
            recent_merges = recent_activity.get("recent_merges", 0)
            print(f"   Jobs processed: {recent_jobs}")
            print(f"   Total merges:   {recent_merges}")
            
            if recent_jobs > 0:
                print(f"   Avg merges/job: {recent_merges/recent_jobs:.2f}")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"💥 Error fetching stats: {e}")

if __name__ == "__main__":
    main()
