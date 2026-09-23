# scrape_glossary.py
import csv, re, time, requests
from bs4 import BeautifulSoup

BASE = "https://www.utvalavi.ge/geo/saxelosno.php?t="
CHAPTERS = range(1, 80)
GANM = re.compile(r"#(ganm_\d+)")

occurrences, orphans = [], []

def strophe_of(el):
    for p in el.parents:
        if p.has_attr("strofi_number"):
            try:
                return int(p["strofi_number"])
            except ValueError:
                return None
    return None

for t in CHAPTERS:
    url = BASE + str(t)
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        r.encoding = "utf-8"
    except requests.RequestException as e:
        print(f"t={t} FAILED {url} -> {e}")
        continue

    soup = BeautifulSoup(r.text, "html.parser")

    glosses = {d["id"]: d.get_text(" ", strip=True)
               for d in soup.find_all("div", id=re.compile(r"^ganm_\d+$"))}

    last_strophe, n_before = None, len(occurrences)

    for el in soup.find_all(True):
        if el.has_attr("strofi_number"):
            try:
                last_strophe = int(el["strofi_number"])
            except ValueError:
                pass
            continue

        if el.name != "span" or not el.has_attr("onmouseover"):
            continue

        m = GANM.search(el["onmouseover"])
        if not m:
            continue

        gid = m.group(1)
        term = el.get_text(" ", strip=True)
        gloss = glosses.get(gid)

        if gloss is None:
            orphans.append({"chapter_id": t, "ganm_id": gid, "term": term})
            continue

        occurrences.append({
            "ganm_id": gid,
            "term": term,
            "gloss": gloss,
            "chapter_id": t,
            "strophe_id": strophe_of(el) or last_strophe,
            "is_phrase": len(term.split()) > 1,
        })

    print(f"t={t:3d}  +{len(occurrences)-n_before:3d}  total {len(occurrences)}")
    time.sleep(0.5)

with open("gloss_occurrences.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=[
        "ganm_id", "term", "gloss", "chapter_id", "strophe_id", "is_phrase"])
    w.writeheader()
    w.writerows(occurrences)

uniq = {(o["term"], o["gloss"]) for o in occurrences}
words = {t for t, g in uniq if len(t.split()) == 1}
missing = [o for o in occurrences if o["strophe_id"] is None]

print(f"\n{len(occurrences)} occurrences")
print(f"{len(uniq)} unique term+gloss pairs ({len(words)} single words)")
print(f"{len(orphans)} orphan spans, {len(missing)} unassigned to a strophe")