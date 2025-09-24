# 10K Webhook Test - Transaction Fix Validation

## 🎯 Objective
Test that the database transaction fix resolves the race condition where `merge_count = 0` despite successful merges.

## 🔧 What Was Fixed

**Before**: `autocommit=True` caused race conditions
```python
# OLD - Race condition
get_one_queued_for_update(conn)  # Lock acquired & immediately released
mark_working(conn, job_id)       # New transaction, no lock
# ... long processing time ...
mark_done(conn, job_id, merge_count)  # Potential data loss
```

**After**: Proper transactions maintain locks
```python
# NEW - Atomic operations
conn.begin()
get_one_queued_for_update(conn)  # Lock held throughout
mark_working(conn, job_id)       # Same transaction
# ... processing ...
mark_done(conn, job_id, merge_count)  # Atomic update
conn.commit()  # Lock released
```

## 📋 Test Plan

### Step 1: Deploy the Fix to PythonAnywhere

1. **Upload the updated files**:
   - `src/queue_db.py` (autocommit=False)
   - `src/worker.py` (proper transactions)
   - `src/app.py` (transaction handling + /stats endpoint)

2. **Restart your Always-On Task**:
   - Go to PythonAnywhere Dashboard → Tasks
   - Stop the current worker
   - Start it again to pick up the new code

3. **Restart your Web App**:
   - Go to Web tab
   - Hit the "Reload" button

### Step 2: Send 10,000 Test Webhooks

```bash
# Run the test script locally (it will send to your PythonAnywhere URL)
cd /Users/anton/Projects/pythonanywherededuplicatoin
python scripts/send_test_webhooks.py
```

This will:
- Send 10,000 webhooks in batches of 100
- Use 1,000 unique contact IDs (so ~10 webhooks per contact)
- Create scenarios that should trigger merges
- Show real-time progress

### Step 3: Monitor Progress

**Check stats periodically**:
```bash
# Quick check
python scripts/check_progress.py

# Or manually via curl
curl https://boykomobil2000.pythonanywhere.com/stats
```

**Key metrics to watch**:
- `zero_merge_rate` should be **< 5%** (vs ~50% before)
- `merge_success_rate` should be **> 95%**
- Total jobs should eventually reach 10,000

### Step 4: Validate After 1-2 Days

**Expected Results**:
- ✅ All 10,000 jobs processed (`status = 'done'`)
- ✅ Low zero merge rate (< 5%)
- ✅ Merge counts properly recorded
- ✅ No data inconsistencies

## 📊 Monitoring URLs

- **Stats**: https://boykomobil2000.pythonanywhere.com/stats
- **Health**: https://boykomobil2000.pythonanywhere.com/health
- **Individual Result**: https://boykomobil2000.pythonanywhere.com/results/test-contact-0001

## 🚨 What to Look For

### ✅ Success Indicators
- Zero merge rate drops from ~50% to < 5%
- All webhook batches send successfully
- Worker processes jobs steadily
- No database errors in logs

### ❌ Failure Indicators  
- Zero merge rate stays high (> 20%)
- Database connection errors
- Worker crashes or stops processing
- Webhook sending failures

## 📈 Expected Timeline

- **Webhook sending**: ~10-15 minutes
- **Processing 10k jobs**: 1-2 days (with 1 worker)
- **Each job**: ~5-10 seconds (HubSpot API calls)

## 🔍 Troubleshooting

**If worker stops**:
- Check PythonAnywhere error logs
- Restart the Always-On Task
- Check database connection limits

**If zero merge rate is still high**:
- Verify the code was deployed correctly
- Check that autocommit=False is active
- Look for transaction rollback errors

**If webhooks fail to send**:
- Check the PythonAnywhere URL is correct
- Verify Flask app is running
- Check webhook endpoint logs

## 🎉 Success Criteria

The fix is successful if:
1. **Data Consistency**: Zero merge rate < 5% (down from ~50%)
2. **Reliability**: All 10k webhooks process without errors
3. **Performance**: Worker maintains steady processing rate
4. **Monitoring**: Stats endpoint provides accurate metrics

This test will definitively prove whether the transaction fix resolves the concurrency issue!
