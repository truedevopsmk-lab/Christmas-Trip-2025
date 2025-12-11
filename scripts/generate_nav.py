#!/usr/bin/env python3
import os
import urllib.parse
import pathlib

GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "")
if GITHUB_REPOSITORY:
    USER, REPO = GITHUB_REPOSITORY.split("/",1)
    BASE_URL = f"https://{USER}.github.io/{REPO}"
else:
    # fallback for local testing
    USER = "USERNAME"
    REPO = "REPO"
    BASE_URL = f"https://{USER}.github.io/{REPO}"

def encode_path(path):
    # Encode each path segment, keep slashes
    parts = [urllib.parse.quote(p) for p in path.strip("./").split(os.sep) if p]
    return "/".join(parts)

def find_readme_folders():
    folders = []
    for root, dirs, files in os.walk("."):
        # skip .git and .github
        if any(part in (".git", ".github") for part in pathlib.Path(root).parts):
            continue
        if "README.md" in files:
            folders.append(root)
    return sorted(folders)  # natural tree order

def build_nav(folders):
    entries = []
    for folder in folders:
        if folder == ".":
            continue
        name = os.path.basename(folder)
        pretty = name.replace("-", " ")
        encoded = encode_path(folder)
        entries.append((folder, pretty, encoded))
    # sort by folder path to maintain tree/natural order
    entries.sort(key=lambda x: x[0].lower())
    # Build nav string: Home first
    nav = "## 📘 Navigation Menu\n"
    nav += f"[🏠 Home]({BASE_URL}/) • "
    for _, pretty, encoded in entries:
        nav += f"[{pretty}]({BASE_URL}/{encoded}/) • "
    nav += "\n---\n<!-- inject-nav -->"
    return nav

def remove_existing_nav(content):
    marker = "<!-- inject-nav -->"
    idx = content.find(marker)
    if idx == -1:
        return content
    # remove from start up to and including marker, then strip following blank lines
    after = content[idx+len(marker):]
    # drop leading whitespace/newlines
    after = after.lstrip("\n\r ")
    return after

def inject_nav_into_readme(file_path, nav):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    rest = remove_existing_nav(content)
    new_content = nav + "\n\n" + rest
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)

def create_index_md_for_folder(folder, folders_set):
    # create index.md listing immediate child folders (only those with README.md)
    child_links = []
    for p in sorted(os.listdir(folder)):
        child = os.path.join(folder, p)
        if os.path.isdir(child):
            readme = os.path.join(child, "README.md")
            if os.path.exists(readme):
                pretty = p.replace("-", " ")
                rel = "./" + p + "/"
                child_links.append((p.lower(), pretty, rel))
    if not child_links:
        return
    index_path = os.path.join(folder, "index.md")
    lines = ["# Index", "", "## Subsections", ""]
    for _, pretty, rel in child_links:
        lines.append(f"- [{pretty}]({rel})")
    content = "\n".join(lines) + "\n"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(content)

def main():
    folders = find_readme_folders()
    nav = build_nav(folders)
    # Inject nav into all README.md
    for folder in folders:
        readme = os.path.join(folder, "README.md")
        inject_nav_into_readme(readme, nav)
    # Create index.md in each folder listing child folders
    folders_set = set(folders)
    for folder in folders:
        create_index_md_for_folder(folder, folders_set)
    print("Done. Navigation injected and index.md files created where applicable.")

if __name__ == '__main__':
    main()
