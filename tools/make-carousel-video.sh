#!/usr/bin/env bash
#
# Turn a simulation animation into a web-playable carousel slide.
#
#   tools/make-carousel-video.sh path/to/animation.avi 02-horseshoe
#
# Writes figs/carousel/<name>.mp4 (H.264) and <name>.jpg (poster frame).
# ParaView writes Motion-JPEG AVI, which no browser plays; H.264 in MP4 plays
# everywhere. Uses GStreamer, because ffmpeg is not installed here.
set -euo pipefail

src="${1:-}"
name="${2:-}"
if [ -z "$src" ] || [ -z "$name" ]; then
    printf 'usage: %s <input video> <output basename>\n' "$0" >&2
    exit 2
fi
[ -f "$src" ] || { printf 'ERROR: no such file: %s\n' "$src" >&2; exit 1; }

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
out="figs/carousel/$name"
mkdir -p figs/carousel

command -v gst-launch-1.0 >/dev/null || {
    printf 'ERROR: gst-launch-1.0 not found. Either install gstreamer1.0-tools\n' >&2
    printf '       and gstreamer1.0-plugins-ugly (for x264enc), or install ffmpeg\n' >&2
    printf '       and use: ffmpeg -i "%s" -c:v libx264 -crf 23 -pix_fmt yuv420p \\\n' "$src" >&2
    printf '                -movflags +faststart -an "%s.mp4"\n' "$out" >&2
    exit 1
}

# The decoder depends on the container; decodebin picks it for us.
gst-launch-1.0 -q filesrc location="$src" \
    ! decodebin ! videoconvert ! video/x-raw,format=I420 \
    ! x264enc bitrate=1400 speed-preset=slow key-int-max=50 \
    ! h264parse ! mp4mux faststart=true \
    ! filesink location="$out.mp4"

# A poster frame keeps the slot filled before the video decodes, and is what
# reduced-motion viewers see until they press play.
gst-launch-1.0 -q filesrc location="$src" \
    ! decodebin ! videoconvert ! jpegenc quality=88 \
    ! multifilesink location="$out-%03d.jpg" max-files=1 2>/dev/null || true
if compgen -G "$out-*.jpg" >/dev/null; then
    mv -- "$(ls -1 "$out"-*.jpg | head -1)" "$out.jpg"
    rm -f -- "$out"-*.jpg
fi

printf '\nWrote %s.mp4 (%s)\n' "$out" "$(du -h "$out.mp4" | cut -f1)"
[ -f "$out.jpg" ] && printf 'Wrote %s.jpg  (poster)\n' "$out"
cat << EOF

Add this slide to the .carousel block in index.html:

      <li class="carousel-slide">
        <figure>
          <div class="carousel-media">
            <video src="$out.mp4" poster="$out.jpg"
                   muted loop playsinline preload="metadata"
                   aria-label="Describe what the animation shows"></video>
          </div>
          <figcaption>Short caption</figcaption>
        </figure>
      </li>
EOF
