import json, re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from .hubspot_client import post_json, get_json, patch_json

SEARCH_URL = "/crm/v3/objects/contacts/search"
MERGE_URL  = "/crm/v3/objects/contacts/merge"
CONTACT_URL = "/crm/v3/objects/contacts"

PROPS = [
    "initial_channel_group","all_channel_groups","latest_channel_group",
    "initial_channel","all_channels","latest_channel",
    "initial_campaign","campaign","latest_campaign",
    "createdate","lastmodifieddate","notes_last_updated",
]

MIN_AWARE = datetime(1970,1,1,tzinfo=timezone.utc)
MAX_AWARE = datetime(9999,12,31,23,59,59,tzinfo=timezone.utc)
_FORWARD_REF_RE = re.compile(r"forward reference to\s+(\d+)", re.IGNORECASE)

def parse_iso(s: Optional[str]) -> Optional[datetime]:
    if not s: return None
    s = s.strip()
    try:
        return datetime.fromisoformat(s.replace("Z","+00:00")).astimezone(timezone.utc)
    except Exception:
        for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ","%Y-%m-%dT%H:%M:%SZ"):
            try:
                return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
            except Exception:
                pass
    return None

def split_multi(val):
    if val is None: return []
    if isinstance(val, list): return [str(x).strip() for x in val if str(x).strip()]
    s = str(val).strip()
    if not s: return []
    parts = s.split(";") if ";" in s else s.split(",")
    return [p.strip() for p in parts if p.strip()]

def uniq_stable(seq: List[str]) -> List[str]:
    seen, out = set(), []
    for item in seq:
        k = str(item)
        if k not in seen:
            seen.add(k); out.append(item)
    return out

def pick_with_fallback(records: List[Dict[str, Any]], field: str, mode: str) -> str:
    n = len(records)
    if n == 0: return ""
    first, last = 0, n-1
    middle = (n//2) if n>=3 else None
    order = ([last] + ([middle] if middle is not None else []) + [first]) if mode=="latest" \
            else ([first] + ([middle] if middle is not None else []) + [last])
    for idx in order:
        v = (records[idx].get(field) or "").strip()
        if v: return v
    return ""

def fetch_contacts_by_unique(token: str, unique_identifier: str) -> List[Dict[str, Any]]:
    payload = {
        "filterGroups":[{"filters":[{"propertyName":"unique_identifier","operator":"EQ","value":unique_identifier}]}],
        "properties": PROPS, "limit": 100
    }
    results, after, page = [], None, 0
    while True:
        body = dict(payload); 
        if after is not None: body["after"]=after
        page += 1
        data = post_json(SEARCH_URL, body, token)
        batch = data.get("results", []) or []
        for r in batch:
            p = r.get("properties", {}) or {}
            results.append({
                "id": str(r.get("id") or ""),
                "createdate": p.get("createdate",""),
                "lastmodifieddate": p.get("lastmodifieddate",""),
                "notes_last_updated": p.get("notes_last_updated",""),
                "initial_channel_group": p.get("initial_channel_group","") or "",
                "all_channel_groups":   p.get("all_channel_groups","") or "",
                "latest_channel_group": p.get("latest_channel_group","") or "",
                "initial_channel": p.get("initial_channel","") or "",
                "all_channels":    p.get("all_channels","") or "",
                "latest_channel":  p.get("latest_channel","") or "",
                "initial_campaign":p.get("initial_campaign","") or "",
                "campaign":        p.get("campaign","") or "",
                "latest_campaign": p.get("latest_campaign","") or "",
            })
        paging = (data.get("paging") or {}).get("next") or {}
        after = paging.get("after")
        if not after: break
    return results

def canonical_id(token: str, contact_id: str) -> str:
    try:
        data = get_json(f"{CONTACT_URL}/{contact_id}?archived=true", token)
        return str(data.get("id") or contact_id)
    except Exception:
        return contact_id

def merge_contact(token: str, object_id_to_merge: str, primary_object_id: str) -> Dict[str, Any]:
    body = {"objectIdToMerge": object_id_to_merge, "primaryObjectId": primary_object_id}
    try:
        resp = post_json(MERGE_URL, body, token)
        return {"id": str(resp.get("id") or primary_object_id), "raw": resp}
    except Exception as e:
        txt = str(e)
        m = _FORWARD_REF_RE.search(txt)
        if m:
            canonical = m.group(1)
            if canonical != primary_object_id:
                resp2 = post_json(MERGE_URL, {"objectIdToMerge": canonical, "primaryObjectId": primary_object_id}, token)
                return {"id": str(resp2.get("id") or primary_object_id), "raw": resp2}
        return {"error": True, "message": txt}

def patch_contact(token: str, contact_id: str, props: Dict[str, str]) -> Dict[str, Any]:
    return patch_json(f"{CONTACT_URL}/{contact_id}", {"properties": props}, token)

def run_dedupe(token: str, unique_identifier: str, dry_run: bool=False) -> Dict[str, Any]:
    records = fetch_contacts_by_unique(token, unique_identifier)
    if not records:
        return {"initial_channel_group":"","all_channel_groups":"","latest_channel_group":"",
                "initial_channel":"","all_channels":"","latest_channel":"",
                "initial_campaign":"","campaign":"","latest_campaign":"",
                "primary_id":"","merged_ids":"","merge_count":0,"merge_errors_json":"[]"}

    for r in records:
        r["_created_dt"] = parse_iso(r.get("createdate"))
        r["_lastmod_dt"] = parse_iso(r.get("lastmodifieddate"))
        r["_notes_dt"]   = parse_iso(r.get("notes_last_updated"))

    # Primary selection
    if any(r["_notes_dt"] is not None for r in records):
        records_for_merge = sorted(records, key=lambda x: (
            x["_notes_dt"] or MIN_AWARE, x["_lastmod_dt"] or MIN_AWARE, x["_created_dt"] or MIN_AWARE, x.get("id") or ""
        ), reverse=True)
    else:
        records_for_merge = sorted(records, key=lambda x: (
            x["_created_dt"] or MAX_AWARE, x["_lastmod_dt"] or MAX_AWARE, x.get("id") or ""
        ))

    primary_id = records_for_merge[0]["id"]
    others = [r["id"] for r in records_for_merge[1:]]

    # Canonicalize set
    primary_id = canonical_id(token, primary_id)
    canon_others, seen = [], {primary_id}
    for oid in others:
        cid = canonical_id(token, oid)
        if cid != primary_id and cid not in seen:
            seen.add(cid); canon_others.append(cid)
    others = canon_others

    # Rollups (by created asc)
    records_for_props = [r for r in records if r["_created_dt"] is not None]
    records_for_props.sort(key=lambda x: x["_created_dt"])

    def build_all(field: str) -> str:
        chunks = []
        for r in records_for_props: chunks.extend(split_multi(r.get(field,"")))
        return ";".join(uniq_stable(chunks))

    all_channel_groups = build_all("all_channel_groups")
    all_channels = build_all("all_channels")
    campaign = build_all("campaign")

    initial_channel_group = pick_with_fallback(records_for_props, "initial_channel_group", "initial")
    latest_channel_group  = pick_with_fallback(records_for_props, "latest_channel_group",  "latest")
    initial_channel       = pick_with_fallback(records_for_props, "initial_channel",       "initial")
    latest_channel        = pick_with_fallback(records_for_props, "latest_channel",        "latest")
    initial_campaign      = pick_with_fallback(records_for_props, "initial_campaign",      "initial")
    latest_campaign       = pick_with_fallback(records_for_props, "latest_campaign",       "latest")

    merge_results, merge_errors = [], []
    if not dry_run:
        for oid in others:
            res = merge_contact(token, oid, primary_id)
            if res.get("error"): merge_errors.append(res); continue
            new_primary = res.get("id") or primary_id
            primary_id = new_primary

    # Final survivor id then PATCH
    primary_id = canonical_id(token, primary_id)
    props_to_write = {
        "initial_channel_group": initial_channel_group,
        "all_channel_groups":    all_channel_groups,
        "latest_channel_group":  latest_channel_group,
        "initial_channel":       initial_channel,
        "all_channels":          all_channels,
        "latest_channel":        latest_channel,
        "initial_campaign":      initial_campaign,
        "campaign":              campaign,
        "latest_campaign":       latest_campaign,
    }

    if not dry_run and primary_id:
        try:
            patch_contact(token, primary_id, props_to_write)
        except Exception as e:
            merge_errors.append({"error": True, "message": f"patch failed: {e}"})

    return {
        "initial_channel_group": initial_channel_group,
        "all_channel_groups": all_channel_groups,
        "latest_channel_group": latest_channel_group,
        "initial_channel": initial_channel,
        "all_channels": all_channels,
        "latest_channel": latest_channel,
        "initial_campaign": initial_campaign,
        "campaign": campaign,
        "latest_campaign": latest_campaign,
        "primary_id": primary_id,
        "merged_ids": ";".join(others),
        "merge_count": len(others) if not dry_run else 0,
        "merge_errors_json": json.dumps(merge_errors),
    }
