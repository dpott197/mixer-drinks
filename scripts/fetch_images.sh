#!/bin/sh
# Download drink images from MonsieurCode/monsieur-data and convert them to 480px WebP.
# Usage: scripts/fetch_images.sh <path-to-mixer-android>/core/src/main/assets/json
set -e
src="$1"
out="$(cd "$(dirname "$0")/.." && pwd)/images"
tmp="$(mktemp -d)"
base=https://raw.githubusercontent.com/MonsieurCode/monsieur-data/develop/S3/barback-assets/drinks
mkdir -p "$out"
python3 -I -c 'import json,sys; [print(d["id"]) for d in json.load(open(sys.argv[1]))["drinks"]]' "$src/drinks.json" |
while read -r id; do
  [ -f "$out/$id.webp" ] && continue
  curl -sfL "$base/$id.png" -o "$tmp/$id.png" || continue
  cwebp -quiet -q 78 -alpha_q 85 -resize 480 0 "$tmp/$id.png" -o "$out/$id.webp"
done
rm -rf "$tmp"
ls "$out" | wc -l
