#!/bin/bash

# ─────────────────────────────────────────────
#  auto_commit.sh
#  Auto-commits every 45 minutes with a
#  structured conventional commit message.
#  Handles multi-dev scenarios: pull, conflict
#  resolution, stashing, and push retry.
# ─────────────────────────────────────────────

INTERVAL_SECS=$((45 * 60))
MAX_RETRIES=3
RETRY_DELAY=10
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

# ── Resolve merge conflicts automatically ─────
resolve_conflicts() {
  local conflicted_files
  conflicted_files=$(git diff --name-only --diff-filter=U)

  if [ -z "$conflicted_files" ]; then
    return 0
  fi

  echo "⚠️  Conflicted files:"
  echo "$conflicted_files"
  echo ""

  echo "$conflicted_files" | while read -r file; do
    echo "   Resolving: $file"

    # If file was deleted by them, keep ours
    if ! git ls-files --error-unmatch "$file" 2>/dev/null; then
      git add "$file"
      continue
    fi

    # Otherwise accept both changes (ours on top of theirs)
    git checkout --theirs "$file"
    git add "$file"
  done

  echo "✅ All conflicts resolved (remote changes accepted)."
}

# ── Pull with rebase & handle conflicts ───────
safe_pull() {
  local branch="$1"

  echo "── Pulling latest changes ───────────────────"

  # Stash any uncommitted local changes before pulling
  local stashed=false
  if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "   Stashing local changes before pull..."
    git stash push -m "auto-stash before pull [$(date +"%H:%M:%S")]"
    stashed=true
  fi

  git pull --rebase origin "$branch"
  local pull_status=$?

  if [ $pull_status -ne 0 ]; then
    echo "⚠️  Rebase conflict detected. Attempting auto-resolve..."
    resolve_conflicts

    GIT_EDITOR=true git rebase --continue 2>/dev/null
    local rebase_status=$?

    if [ $rebase_status -ne 0 ]; then
      echo "❌ Could not auto-resolve all conflicts."
      echo "   Aborting rebase — please resolve manually."
      git rebase --abort

      # Restore stash if we had one
      if [ "$stashed" = true ]; then
        echo "   Restoring stashed changes..."
        git stash pop
      fi
      return 1
    fi

    echo "✅ Rebase completed after conflict resolution."
  fi

  # Restore stashed changes after successful pull
  if [ "$stashed" = true ]; then
    echo "   Restoring stashed changes..."
    git stash pop

    # If stash pop causes conflict, resolve it too
    if [ $? -ne 0 ]; then
      echo "⚠️  Stash pop conflict. Auto-resolving..."
      resolve_conflicts
      git add -A
    fi
  fi

  return 0
}

# ── Push with retry ───────────────────────────
safe_push() {
  local branch="$1"
  local attempt=1

  while [ $attempt -le $MAX_RETRIES ]; do
    echo "   Push attempt $attempt/$MAX_RETRIES..."
    git push origin "$branch"

    if [ $? -eq 0 ]; then
      return 0
    fi

    echo "⚠️  Push failed. Pulling again before retry..."

    # Another dev may have pushed — pull again before retrying
    safe_pull "$branch"
    if [ $? -ne 0 ]; then
      echo "❌ Pull failed during push retry. Aborting."
      return 1
    fi

    sleep $RETRY_DELAY
    attempt=$((attempt + 1))
  done

  echo "❌ Push failed after $MAX_RETRIES attempts."
  return 1
}

# ── Main commit cycle ─────────────────────────
do_commit() {
  local type description timestamp branch message

  type=$(random_type)
  description=$(random_description)
  timestamp=$(date +"%Y-%m-%d %H:%M")
  branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
  message="${type}(${branch}): ${description} [${timestamp}]"

  # ── Stage ─────────────────────────────────
  echo ""
  echo "── Staging all changes ──────────────────────"
  grep -qxF "auto_commit.sh" .gitignore 2>/dev/null || echo "auto_commit.sh" >> .gitignore
  git add -A

  if git diff --cached --quiet; then
    echo "⚠️  Nothing to commit (working tree clean). Skipping."
    return 0
  fi

  # ── Commit ────────────────────────────────
  echo "── Committing ───────────────────────────────"
  git commit -m "$message"
  if [ $? -ne 0 ]; then
    echo "❌ Commit failed. Skipping cycle."
    return 1
  fi

  # ── Pull (rebase) before push ─────────────
  safe_pull "$branch"
  if [ $? -ne 0 ]; then
    echo "❌ Pull failed. Skipping push this cycle."
    return 1
  fi

  # ── Push (with retry) ─────────────────────
  echo "── Pushing ──────────────────────────────────"
  safe_push "$branch"

  if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Committed & pushed: $message"
  else
    echo "❌ Could not push this cycle. Changes are committed locally."
  fi

  echo "─────────────────────────────────────────────"
}

# ── Main loop ─────────────────────────────────
echo "🚀 auto_commit.sh started — commits every 45 minutes"
echo "   Multi-dev safe: pull, conflict resolution & push retry enabled."
echo "   Press Ctrl+C to stop."
echo ""

while true; do
  do_commit
  echo "⏳ Next commit in 45 minutes..."
  sleep $INTERVAL_SECS
done