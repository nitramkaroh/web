#!/usr/bin/env bash
#
# Make every video in figs/carousel/ fit for the web, in place.
#
#   tools/optimize-carousel.sh            optimise what needs it
#   tools/optimize-carousel.sh --check    list what would be done, change nothing
#
# Drop a video into figs/carousel/ under the name the page references, then run
# this. Anything wider than MAXW is re-encoded down to MAXW and given a poster
# frame; files already small enough are left alone, so it is safe to re-run.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

MAXW=1200          # more than the page ever shows, even on a 2x display
BITRATE=1500

check=0
[ "${1:-}" = "--check" ] && check=1

command -v gst-launch-1.0 >/dev/null || {
    printf 'ERROR: gst-launch-1.0 not found (gstreamer1.0-tools + -plugins-ugly)\n' >&2
    exit 1
}

shopt -s nullglob
did=0
for src in figs/carousel/*.mp4; do
    base="${src%.mp4}"
    width=$(gst-discoverer-1.0 "$src" 2>/dev/null | awk '/Width:/{print $2; exit}')
    [ -n "$width" ] || { printf 'SKIP  %s (cannot read its width)\n' "$src" >&2; continue; }

    needs_video=0
    [ "$width" -gt "$MAXW" ] && needs_video=1
    needs_poster=0
    [ -f "$base.jpg" ] || needs_poster=1

    if [ "$needs_video" = 0 ] && [ "$needs_poster" = 0 ]; then
        printf 'ok    %-46s %s px\n' "$src" "$width"
        continue
    fi

    if [ "$check" = 1 ]; then
        [ "$needs_video" = 1 ] && printf 'would re-encode %-40s %s -> %s px\n' "$src" "$width" "$MAXW"
        [ "$needs_poster" = 1 ] && printf 'would add poster %s.jpg\n' "$base"
        did=1
        continue
    fi

    if [ "$needs_video" = 1 ]; then
        height=$(gst-discoverer-1.0 "$src" 2>/dev/null | awk '/Height:/{print $2; exit}')
        # keep the aspect ratio, and keep the height even for the encoder
        newh=$(( width > 0 ? MAXW * height / width : 0 ))
        newh=$(( newh - newh % 2 ))
        tmp="$base.optimizing.mp4"
        printf 're-encode %-42s %sx%s -> %sx%s\n' "$src" "$width" "$height" "$MAXW" "$newh"
        gst-launch-1.0 -q filesrc location="$src" ! decodebin ! videoconvert \
            ! videoscale method=lanczos ! video/x-raw,width=$MAXW,height=$newh \
            ! videoconvert ! video/x-raw,format=I420 \
            ! x264enc bitrate=$BITRATE speed-preset=slower key-int-max=50 \
            ! h264parse ! mp4mux faststart=true ! filesink location="$tmp"
        mv -- "$tmp" "$src"
        needs_poster=1
    fi

    if [ "$needs_poster" = 1 ]; then
        rm -f -- "$base".poster-*.jpg
        gst-launch-1.0 -q filesrc location="$src" ! decodebin ! videoconvert ! jpegenc quality=88 \
            ! multifilesink location="$base.poster-%04d.jpg" 2>/dev/null || true
        # two thirds in, where these animations are past their initial state
        frames=( "$base".poster-*.jpg )
        if [ ${#frames[@]} -gt 0 ]; then
            pick="${frames[$(( ${#frames[@]} * 2 / 3 ))]}"
            mv -- "$pick" "$base.jpg"
            rm -f -- "$base".poster-*.jpg
            printf 'poster    %s.jpg\n' "$base"
        fi
    fi
    did=1
done

if [ "$check" = 1 ]; then
    [ "$did" = 0 ] && printf '\nNothing to do.\n' || exit 1
else
    printf '\n%s\n' "$([ "$did" = 1 ] && echo 'Done. Commit the results.' || echo 'Everything was already optimised.')"
fi
