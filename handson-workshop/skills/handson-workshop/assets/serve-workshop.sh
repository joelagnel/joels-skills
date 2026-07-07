#!/bin/bash
# serve-workshop.sh — serve a generated workshop directory over HTTP for local
# preview and testing on other devices on your network.
#
# The generated WORKSHOP.html / exam.html are fully self-contained, so this is
# only a convenience for viewing over the network (e.g. from a phone). To just
# read it locally, open the file directly in a browser (file://…/WORKSHOP.html).
#
# Usage:
#   serve-workshop.sh [dir] [port]
#
#   dir   Workshop directory to serve (default: current directory).
#   port  Port to listen on (default: 8000).
#
# Examples:
#   serve-workshop.sh                  # serve ./ on :8000
#   serve-workshop.sh http-caching     # serve ./http-caching on :8000
#   serve-workshop.sh http-caching 9000
set -euo pipefail

DIR="${1:-.}"
PORT="${2:-8000}"

if [ ! -d "$DIR" ]; then
    echo "Error: directory '$DIR' does not exist" >&2
    exit 1
fi

if [ ! -f "$DIR/WORKSHOP.html" ]; then
    echo "Warning: no WORKSHOP.html found in '$DIR' — serving anyway." >&2
fi

echo "Serving '$DIR' at:"
echo "    http://localhost:$PORT/WORKSHOP.html"
echo "    http://localhost:$PORT/exam.html"
echo
echo "Reachable from other devices on your LAN at http://<this-host-ip>:$PORT/"
echo "Press Ctrl-C to stop."
echo

exec python3 -m http.server "$PORT" --directory "$DIR"
