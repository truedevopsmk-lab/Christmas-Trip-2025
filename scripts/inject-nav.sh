#!/usr/bin/env bash
set -euo pipefail

# Compute base pages URL like https://<user>.github.io/<repo>
REPO_NAME=$(basename "$GITHUB_REPOSITORY")
USER_NAME=$(echo "$GITHUB_REPOSITORY" | cut -d'/' -f1)
BASE_URL="https://${USER_NAME}.github.io/${REPO_NAME}"

echo "[inject-nav] Base URL: ${BASE_URL}"

# Temporary nav output
NAV_FILE=$(mktemp)
echo "## 📘 Navigation Menu" > "$NAV_FILE"

# Build entries array (pretty|encoded)
declare -a entries

# Find README.md files safely, including folder names with spaces
while IFS= read -r -d '' readme; do
  folder=$(dirname "$readme")
  # skip .github and hidden folders
  case "$folder" in
    .github*|./.github*|.*) continue ;;
  esac

  # skip root README — we'll add Home manually
  if [[ "$folder" == "." ]]; then
    continue
  fi

  name=$(basename "$folder")
  pretty=$(echo "$name" | sed 's/-/ /g')

  # Encode using jq (@uri) to avoid problems with spaces/special chars
  encoded=$(printf "%s" "$folder" | jq -sRr @uri)

  entries+=("$pretty|$encoded")
done < <(find . -type f -name "README.md" -print0)

# Sort entries in natural tree order (we'll sort by path so structure remains)
# Transform entries into "encoded|pretty" so sort is by encoded path (preserves tree order)
tmp_sorted=$(mktemp)
for e in "${entries[@]}"; do
  pretty="${e%%|*}"
  encoded="${e##*|}"
  printf "%s|%s\n" "$encoded" "$pretty" >> "$tmp_sorted"
done

# sort preserves natural ascii order which matches tree order for most repos.
sort "$tmp_sorted" -o "$tmp_sorted"

# Add Home first
printf "[🏠 Home](%s/) • " "$BASE_URL" >> "$NAV_FILE"

# Append sorted entries
while IFS='|' read -r encoded pretty; do
  # If pretty is empty, fallback to encoded
  if [[ -z "$pretty" ]]; then
    pretty="$encoded"
  fi
  printf "[%s](%s/%s/) • " "$pretty" "$BASE_URL" "$encoded" >> "$NAV_FILE"
done < "$tmp_sorted"

# finish nav
printf "\n\n---\n<!-- inject-nav -->\n" >> "$NAV_FILE"

echo "[inject-nav] Built navigation: "
cat "$NAV_FILE"

# Now inject into all README.md files.
# We first remove an existing injected block (if any), then prepend the fresh one.
while IFS= read -r -d '' file; do
  echo "[inject-nav] Updating: $file"
  tmpclean=$(mktemp)

  # Remove previous injected block (from its start to the marker line)
  awk '
    BEGIN {skip=0}
    /<!-- inject-nav -->/ { skip=1; next }
    skip==1 && NF==0 { skip=0; next }  # handle trailing blank line after removed block
    skip==1 { next }
    { print }
  ' "$file" > "$tmpclean"

  # Prepend new nav + original content
  {
    cat "$NAV_FILE"
    echo ""
    cat "$tmpclean"
  } > "${file}.new"

  mv "${file}.new" "$file"
done < <(find . -type f -name "README.md" -print0)

# cleanup
rm -f "$NAV_FILE" "$tmp_sorted"
echo "[inject-nav] Done."

