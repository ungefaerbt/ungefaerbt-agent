def ist_zu_vage(headline):
    if not headline or not headline.strip():
        return True
    woerter = headline.split()
    if len(woerter) < 5:
        return True
    stripped = headline.strip()
    if (stripped[0] in ('„', '"', '"', "'") and
            stripped[-1] in ('"', '"', '"', "'") and
            len(woerter) < 8):
        return True
    return False
