import feedparser, sys
sys.stdout.reconfigure(encoding="utf-8")
from config import QUELLEN

ok, fail = [], []
for name, daten in QUELLEN.items():
    try:
        f = feedparser.parse(daten["rss"])
        if len(f.entries) > 0:
            ok.append(name)
        else:
            fail.append((name, f.get("status", "n/a")))
    except Exception as e:
        fail.append((name, str(e)[:40]))

print(f"Funktionierend: {len(ok)} / {len(ok) + len(fail)}\n")
print("DEFEKT:")
for name, status in fail:
    print(f"  {name}: status={status}")
