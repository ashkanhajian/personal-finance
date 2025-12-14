def mask_national_id(national_id: str, keep_last: int = 4) -> str:
    nid = (national_id or "").strip()
    if not nid:
        return ""
    if len(nid) <= keep_last:
        return "*" * len(nid)
    return "*" * (len(nid) - keep_last) + nid[-keep_last:]
