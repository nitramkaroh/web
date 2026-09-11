#!/usr/bin/env bash
#
# Stamp styles.css and script.js with a content hash in every page.
#
#   tools/stamp-assets.sh            rewrite the stamps
#   tools/stamp-assets.sh --check    fail if any stamp is stale
#
# Why: the server sends no Cache-Control, so a browser that has visited before
# keeps its cached stylesheet while receiving the new HTML. In September 2026
# that shipped profile icons whose CSS rules the cached stylesheet did not have,
# and they rendered at full size over the text on phones. A hash in the URL
# makes a changed asset a different URL, so the cache cannot serve the old one.
#
# Every page must be re-uploaded whenever an asset changes, because every page
# carries the stamp.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

# NB: not `[ ... ] && check=1` -- under `set -e` a false test exits the script.
check=0
if [ "${1:-}" = "--check" ]; then check=1; fi

stale=0
for asset in styles.css script.js; do
    [ -f "$asset" ] || { printf 'ERROR: %s is missing\n' "$asset" >&2; exit 1; }
    hash=$(md5sum "$asset" | cut -c1-8)
    for page in *.html; do
        grep -q "$asset" "$page" || continue
        # `|| true`: an unstamped page makes grep exit 1, and with pipefail and
        # set -e that would abort the run instead of stamping it.
        current=$( { grep -o "$asset?v=[0-9a-f]\{8\}" "$page" || true; } | head -1 | sed "s/.*v=//")
        if [ "$current" = "$hash" ]; then
            continue
        fi
        if [ "$check" = 1 ]; then
            printf 'STALE: %s in %s (has %s, needs %s)\n' \
                   "$asset" "$page" "${current:-none}" "$hash" >&2
            stale=1
        else
            # match the asset with or without an existing stamp
            sed -i "s|$asset\(?v=[0-9a-f]\{8\}\)\{0,1\}|$asset?v=$hash|g" "$page"
            printf 'stamped %-20s %s -> %s\n' "$page" "$asset" "$hash"
        fi
    done
done

if [ "$check" = 1 ]; then
    [ "$stale" = 0 ] || { printf '\nRun tools/stamp-assets.sh before deploying.\n' >&2; exit 1; }
    printf 'all stamps current\n'
fi
