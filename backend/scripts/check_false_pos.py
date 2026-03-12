"""Check which keywords let unrelated articles through."""
import sys
sys.path.insert(0, ".")
import re
from config.keywords import get_all_keywords
from db.database import get_supabase

keywords = get_all_keywords()
patterns = [(kw, re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE)) for kw in keywords]

sb = get_supabase()

# Check specific unrelated articles
search_terms = [
    "UN warns of widening crisis",
    "IEA agrees release of 400m barrels",
    "Nothing changes",
    "Toronto",
]

for partial in search_terms:
    result = sb.table("articles").select("id, title, full_text").ilike("title", f"%{partial}%").limit(1).execute()
    if result.data:
        a = result.data[0]
        text = (a.get("title", "") + " " + (a.get("full_text", "") or "")).lower()
        matched = [kw for kw, p in patterns if p.search(text)]
        print(f"id={a['id']} | {a['title'][:70]}")
        print(f"  Matched keywords: {matched}")
        print(f"  Full text length: {len(a.get('full_text', '') or '')}")
        # Show context around matches
        for kw in matched:
            idx = text.find(kw.lower())
            if idx >= 0:
                snippet = text[max(0,idx-30):idx+len(kw)+30]
                print(f"  Context for '{kw}': ...{snippet}...")
        print()
