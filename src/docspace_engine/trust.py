from __future__ import annotations


def apply_trust_degradation(impact_report: dict) -> dict:
    trust = {}
    for item in impact_report.get("impacted_docs", []) or []:
        trust[item["doc_id"]] = {
            "trust_status": "impacted",
            "needs_review": True,
            "trust_confidence": min(item.get("confidence", 0.6), 0.6),
        }
    return trust


def merge_trust_snapshot(manifest: dict, trust_updates: dict) -> dict:
    merged = dict(manifest)
    merged.setdefault("trust", {})
    merged["trust"].update(trust_updates)
    return merged
