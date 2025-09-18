# HubSpot Dedupe & Merge Service

Receives HubSpot webhooks, enqueues jobs, then merges duplicate contacts and patches canonical properties on the survivor.

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in values
python -m scripts.init_db
make run       # webhook receiver on http://localhost:3000
make worker    # background worker
```

## Webhook signature (v3)

We verify X-HubSpot-Signature-V3 using the v3 base-string (method, path, query, body, timestamp) and your app secret.

## Deploy to PythonAnywhere

1. Upload repo, create a virtualenv, `pip install -r requirements.txt`.
2. Web tab → new Flask app → point WSGI to `wsgi.py`.
3. Set env vars: HUBSPOT\_PRIVATE\_APP\_TOKEN, HUBSPOT\_APP\_SECRET, DB\_\*.
4. Create DB table (run `python -m scripts.init_db` in a Bash console).
5. Add an **Always-on task** to run `python -m src.worker`.
6. Point HubSpot Webhooks to `https://<username>.pythonanywhere.com/webhooks/hubspot`.

## Notes

* Merge is irreversible.
* After the merge loop we re-canonicalize the survivor ID and **PATCH** it.
* Properties must exist in HubSpot with the exact internal names.
