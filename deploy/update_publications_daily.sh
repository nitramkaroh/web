#!/usr/bin/env bash
set -euo pipefail

# Run this script from cron/systemd to update publications.html from ORCID.
# Adjust SITE_DIR if the site is installed elsewhere on the server.
SITE_DIR="${SITE_DIR:-/var/www/computational_mechanics_soft_materials_group}"
LOG_DIR="$SITE_DIR/logs"
LOCK_FILE="/tmp/cmsm_publications_update.lock"

mkdir -p "$LOG_DIR"

# flock prevents two updates from running at the same time.
(
  flock -n 9 || exit 0
  cd "$SITE_DIR"
  /usr/bin/env python3 tools/generate_publications_from_orcid.py \
    >> "$LOG_DIR/orcid_publications_update.log" 2>&1
) 9>"$LOCK_FILE"
