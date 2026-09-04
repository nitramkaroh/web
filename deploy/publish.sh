#!/usr/bin/env bash
#
# Publish the site to a web server over ssh.
#
#   deploy/publish.sh mhorak@mech:/home/mhorak/public_html/cmsm
#
# Uploads only what the site is made of, with web-readable modes. The site
# uses relative paths throughout, so it works from any subdirectory.
#
# It does NOT pass --delete: the target may hold other files (a personal
# page, older material) that are not part of this repo.
set -euo pipefail

dest="${1:-}"
if [ -z "$dest" ]; then
    printf 'usage: %s user@host:/path/to/webroot\n' "$0" >&2
    printf '\nDry run first if you are unsure:\n' >&2
    printf '  %s --dry-run user@host:/path\n' "$0" >&2
    exit 2
fi

dry=()
if [ "$dest" = "--dry-run" ]; then
    dry=(--dry-run)
    dest="${2:-}"
    [ -n "$dest" ] || { printf 'ERROR: --dry-run needs a destination too\n' >&2; exit 2; }
fi
dest="${dest%/}"

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

payload=(index.html people.html publications.html projects.html news.html openings.html
         styles.css script.js figs)
for f in "${payload[@]}"; do
    [ -e "$f" ] || { printf 'ERROR: %s is missing from the repo\n' "$f" >&2; exit 1; }
done

# The page must not reference a file that is not in the payload, which is how
# a slide ends up blank after a rename.
missing=0
while read -r ref; do
    [ -e "$ref" ] || { printf 'ERROR: pages reference %s, which does not exist\n' "$ref" >&2; missing=1; }
done < <(grep -ho '\(href\|src\|poster\)="[^"]*"' "${payload[@]%%figs}"*.html 2>/dev/null \
         | sed 's/.*="//;s/"$//' \
         | grep -v '^\(https\?:\|//\|mailto:\|#\)' | sort -u)
[ "$missing" = 0 ] || exit 1

if command -v rsync >/dev/null; then
    rsync -av "${dry[@]}" --chmod=D755,F644 --exclude='figs/*.pdf' --exclude='figs/*.eps' \
          "${payload[@]}" "$dest/"
else
    [ ${#dry[@]} -eq 0 ] || { printf 'ERROR: --dry-run needs rsync\n' >&2; exit 1; }
    scp -O -r "${payload[@]}" "$dest/"
    printf 'NOTE: scp cannot set modes - check the server returns no 403s.\n' >&2
fi

if [ ${#dry[@]} -eq 0 ]; then
    printf '\nUploaded: %s\n' "${payload[*]}"
    printf 'The publications page is generated; see README_DEPLOYMENT.md for the ORCID update.\n'
fi
