#!/bin/bash

# ─────────────────────────────────────────────
#  auto_commit.sh
#  Auto-commits every 45 minutes with a
#  structured conventional commit message
# ─────────────────────────────────────────────

INTERVAL_SECS=$((45 * 60))
TYPES=("feat" "fix" "chore" "refactor" "style" "docs")

DESCRIPTIONS=(
  "update project files and apply minor improvements"
  "clean up code and remove unused variables"
  "refactor logic for better readability and structure"
  "fix minor bugs and improve overall stability"
  "update dependencies and resolve compatibility issues"
  "improve error handling and edge case coverage"
  "add missing comments and improve documentation"
  "optimize performance and reduce redundant operations"
  "adjust styling and formatting across files"
  "sync latest changes and resolve merge conflicts"
)

random_type() {
  echo "${TYPES[$RANDOM % ${#TYPES[@]}]}"
}

random_description() {
  echo "${DESCRIPTIONS[$RANDOM % ${#DESCRIPTIONS[@]}]}"
}

do_commit() {
  local type description timestamp branch message

  type=$(random_type)
  description=$(random_description)
  timestamp=$(date +"%Y-%m-%d %H:%M")
  branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

  message="${type}(${branch}): ${description} [${timestamp}]"

  echo ""
  echo "── Staging all changes ──────────────────────"
  grep -qxF "auto_commit.sh" .gitignore 2>/dev/null || echo "auto_commit.sh" >> .gitignore
  git add -A

  if git diff --cached --quiet; then
    echo "⚠️  Nothing to commit (working tree clean). Skipping."
    return
  fi

  echo "── Committing ───────────────────────────────"
  git commit -m "$message"

  echo "── Pushing ──────────────────────────────────"
  git push

  echo ""
  echo "✅ Committed: $message"
  echo "─────────────────────────────────────────────"
}

# ── Main loop ─────────────────────────────────
echo "🚀 auto_commit.sh started — commits every 45 minutes"
echo "   Press Ctrl+C to stop."
echo ""

while true; do
  do_commit
  echo "⏳ Next commit in 45 minutes..."
  sleep $INTERVAL_SECS
done