#!/usr/bin/env bash
set -euo pipefail

# repository base details
REPO_NAME=$(basename "$GITHUB_REPOSITORY")
USER_NAME=$(echo "$GITHUB_REPOSITORY" | cut -d'/' -f1)
BASE_URL="https://${USER_NAME}.github.io/${REPO_NAME}"

NAV="## 📘 Navigation Menu\n"
declare -a entries=()

# Find all README.md files safely, handle spaces
while IFS= read -r -d '' readme; do
  folder=$(dirname "$readme")
  # skip .git and .github
  [[ "$folder" == .github* ]] && continue
  [[ "$folder" == "./.git"* ]] && continue

  # skip root README here — we'll add Home separately
  if [[ "$folder" == "." ]]; then
    continue
  fi

  name=$(basename "$folder")
  pretty=$(echo "$name" | sed 's/-/ /g')

  # URL-encode folder path (with jq @uri) - safe for spaces and special chars
  encoded=$(printf "%s" "$folder" | jq -sRr @uri)

  entries+=("$pretty|$encoded")
done < <(find . -type f -name "README.md" -print0)

# Sort entries naturally (lexicographic)
IFS=$'\n' sorted=($(sort <<<"${entries[*]}"))
unset IFS

# Build nav: Home first
NAV+="[🏠 Home](${BASE_URL}/) • "

for entry in "${sorted[@]}"; do
  pretty="${entry%%|*}"
  encoded="${entry##*|}"
  NAV+="[$pretty](${BASE_URL}/${encoded}/) • "
done

NAV+="\n\n---\n<!-- inject-nav -->"

# Write the nav to a temporary file to reuse
echo -e "$NAV" > nav-output.txt

# Replace any old nav in each README.md (remove the previous injected block and prepend fresh nav)
while IFS= read -r -d '' file; do
  tmp_clean=$(mktemp)

  # Remove previously injected nav block (from the <!-- inject-nav --> marker to the next blank line)
  awk '
    BEGIN {skip=0}
    /<!-- inject-nav -->/ {skip=1; next}
    skip==1 && NF==0 {skip=0; next}
    skip==1 {next}
    {print}
  ' "$file" > "$tmp_clean"

  # Prepend new nav
  {
    cat nav-output.txt
    echo ""
    cat "$tmp_clean"
  } > "$file"

  echo "Updated: $file"
done < <(find . -type f -name "README.md" -print0)
