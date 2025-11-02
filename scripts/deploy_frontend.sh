#!/usr/bin/env bash
# Sync web/ assets from a source branch into gh-pages and push.
# Usage: ./scripts/deploy_frontend.sh [SRC_BRANCH]
# Default SRC_BRANCH=main
set -euo pipefail
SRC_BRANCH="${1:-main}"

# Ensure we are inside a git repo
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || true)
if [[ -z "$REPO_ROOT" ]]; then
  echo "Error: not inside a git repository" >&2
  exit 2
fi
cd "$REPO_ROOT"

# Refuse to run if working tree is dirty (to avoid losing local edits)
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Error: working tree has local changes. Commit/stash them before deploying." >&2
  exit 3
fi

# Verify source branch exists and has required files
if ! git show "${SRC_BRANCH}:web/index.html" >/dev/null 2>&1; then
  echo "Error: cannot find web/index.html in ${SRC_BRANCH}" >&2
  exit 4
fi

CUR_BRANCH=$(git rev-parse --abbrev-ref HEAD)
cleanup() { git checkout -q "$CUR_BRANCH" 2>/dev/null || true; }
trap cleanup EXIT

# Ensure gh-pages exists locally
if ! git show-ref --verify --quiet refs/heads/gh-pages; then
  if git show-ref --verify --quiet refs/remotes/origin/gh-pages; then
    git checkout -q -t origin/gh-pages
  else
    echo "Error: gh-pages branch not found (local or remote). Create it first." >&2
    exit 5
  fi
else
  git checkout -q gh-pages
fi

# Update assets from source branch
for f in index.html app.js style.css config.js; do
  git show "${SRC_BRANCH}:web/${f}" > "${f}"
  echo "updated ${f} from ${SRC_BRANCH}:web/${f}"
done

# Add cache-busting version param to assets in index.html
HASH=$(git rev-parse --short "${SRC_BRANCH}")
# Replace or add ?v=HASH on known assets
sed -E -i.bak \
  -e "s|(href=\"style\.css)(\?v=[^\"]*)?\"|\\1?v=${HASH}\"|" \
  -e "s|(src=\"config\.js)(\?v=[^\"]*)?\"|\\1?v=${HASH}\"|" \
  -e "s|(src=\"app\.js)(\?v=[^\"]*)?\"|\\1?v=${HASH}\"|" \
  index.html
rm -f index.html.bak

# Commit and push if there are changes
if ! git diff --quiet -- index.html app.js style.css config.js; then
  git add index.html app.js style.css config.js
  git commit -m "gh-pages: sync frontend from ${SRC_BRANCH}/web (v=${HASH})"
  git push origin gh-pages
else
  echo "gh-pages already up to date"
fi

# Back to original branch (handled by trap)
