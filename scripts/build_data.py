"""Build drinks.json for the site from Mixer-Android's asset JSON.

Usage: python3 scripts/build_data.py <path-to-mixer-android>/core/src/main/assets/json
"""
import json
import sys
from pathlib import Path

src = Path(sys.argv[1])
out = Path(__file__).resolve().parent.parent / "drinks.json"


def load(name):
    return json.loads((src / f"{name}.json").read_text())[name]


ingredients = {i["id"]: i for i in load("ingredients")}
glasses = {g["id"]: g["name"] for g in load("glasses")}
garnishes = {g["id"]: g["name"] for g in load("garnishes")}
themes = {t["id"]: t["name"] for t in load("themes")}
pours = {}
for di in load("drink_ingredients"):
    pours.setdefault(di["links"]["drink"], []).append(di)
drink_garnishes = {}
for dg in load("drink_garnishes"):
    drink_garnishes.setdefault(dg["links"]["drink"], []).append(garnishes.get(dg["links"]["garnish"]))
drink_themes = {}
for dt in load("drink_themes"):
    drink_themes.setdefault(dt["links"]["drink"], set()).add(themes.get(dt["links"]["theme"]))


def argb_to_hex(v):
    return "#%06x" % (v & 0xFFFFFF) if v else None


def clean(s):
    return " ".join(s.split()) if s else ""


by_name = {}
for d in load("drinks"):
    name = clean(d["name"])
    if not name:
        continue
    ings = []
    for p in pours.get(d["id"], []):
        ing = ingredients.get(p["links"]["ingredient"])
        if ing:
            ings.append({"name": clean(ing["name"]), "ml": p.get("volume") if p.get("unit") else None,
                         "proof": ing.get("proof") or 0})
    entry = {
        "name": name,
        "description": clean(d.get("description")),
        "history": clean(d.get("history")),
        "instructions": clean(d.get("instructions")),
        "glass": glasses.get(d["links"].get("glass"), ""),
        "ingredients": ings,
        "garnishes": sorted({g for g in drink_garnishes.get(d["id"], []) if g}),
        "themes": set(t for t in drink_themes.get(d["id"], set()) | {themes.get(t) for t in d["links"].get("themes", [])} if t),
        "color": argb_to_hex(d.get("vibrant_color")),
        "dark": argb_to_hex(d.get("dark_vibrant_color")),
    }
    key = name.lower()
    prev = by_name.get(key)
    if prev:
        # Same drink appears once per menu theme; keep the richest copy and merge the themes.
        entry["themes"] |= prev["themes"]
        score = lambda e: (len(e["ingredients"]), len(e["description"]) + len(e["instructions"]) + len(e["history"]))
        if score(prev) >= score(entry):
            prev["themes"] = entry["themes"]
            continue
    by_name[key] = entry

drinks = sorted(by_name.values(), key=lambda e: e["name"].lower())
for e in drinks:
    e["themes"] = sorted(e["themes"])
out.write_text(json.dumps(drinks, separators=(",", ":"), ensure_ascii=False))
print(f"wrote {len(drinks)} drinks to {out}")
