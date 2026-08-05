# discover.py — run once, tells us the actual gloss markup
import requests, re
from collections import Counter
from bs4 import BeautifulSoup

r = requests.get("https://www.utvalavi.ge/geo/saxelosno.php?t=1", timeout=30)
r.encoding = "utf-8"
soup = BeautifulSoup(r.text, "html.parser")

sig = Counter()
for el in soup.find_all(True):
    if el.name in ("html", "body", "head", "script", "style"):
        continue
    keys = tuple(sorted(el.attrs.keys()))
    if keys:
        sig[(el.name, keys)] += 1

for (tag, keys), n in sig.most_common(30):
    print(f"{n:5d}  <{tag} {' '.join(keys)}>")

print("\n--- elements carrying candidate gloss attributes ---")
for el in soup.find_all(True):
    for a in ("title", "alt", "onmouseover", "data-title", "data-tip",
              "data-original-title", "data-content", "rel"):
        if el.has_attr(a):
            print(f"<{el.name} {a}={el[a]!r}> text={el.get_text(strip=True)!r}")
            break

print("\n--- red styling ---")
for el in soup.find_all(style=re.compile("color", re.I)):
    print(el.name, el.get("style"), "|", el.get_text(strip=True)[:40])
for el in soup.find_all(class_=True):
    print(el.name, el.get("class"), "|", el.get_text(strip=True)[:40])
    break