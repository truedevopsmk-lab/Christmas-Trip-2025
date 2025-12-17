#!/usr/bin/env bash
set -e

REPO_NAME=$(basename "$GITHUB_REPOSITORY")
USER_NAME=$(echo "$GITHUB_REPOSITORY" | cut -d'/' -f1)
BASE_URL="https://${USER_NAME}.github.io/${REPO_NAME}"

NAV="## 📘 Navigation Menu
"
declare -a entries=()

while IFS= read -r -d '' readme; do
  folder=$(dirname "$readme")
  name=$(basename "$folder")
  pretty=$(echo "$name" | sed 's/-/ /g')
  encoded=$(printf "%s" "$folder" | jq -sRr @uri)

  if [[ "$folder" == "." ]]; then continue; fi

  entries+=("$pretty|$encoded")
done < <(find . -type f -name "README.md" -print0)

IFS=$'\n' sorted=($(sort <<<"${entries[*]}"))
unset IFS

NAV+="[🏠 Home](${BASE_URL}/) • "
for entry in "${sorted[@]}"; do
  pretty="${entry%%|*}"
  encoded="${entry##*|}"
  NAV+="[$pretty](${BASE_URL}/${encoded}/) • "
done

NAV+="\n\n---\n<!-- inject-nav -->"

echo "$NAV" > nav-output.txt

while IFS= read -r -d '' file; do
  tmp=$(mktemp)

  awk '
    BEGIN {skip=0}
    /<!-- inject-nav -->/ {skip=1; next}
    skip==1 && NF==0 {skip=0; next}
    skip==1 {next}
    {print}
  ' "$file" > "$tmp.clean"

  {
    cat nav-output.txt
    echo ""
    cat "$tmp.clean"
  } > "$file"

  echo "Updated: $file"
done < <(find . -type f -name "README.md" -print0)
