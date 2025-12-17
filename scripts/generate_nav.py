#!/usr/bin/env python3
import os
import urllib.parse
import pathlib
import re
import shutil

GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "")
if GITHUB_REPOSITORY:
    USER, REPO = GITHUB_REPOSITORY.split("/", 1)
    BASE_URL = f"https://{USER}.github.io/{REPO}"
else:
    BASE_URL = ""

# ------------------------
# Helpers
# ------------------------

def encode_path(path: str) -> str:
    parts = [
        urllib.parse.quote(p)
        for p in os.path.normpath(path).strip("./").split(os.sep)
        if p
    ]
    return "/".join(parts)

def find_readme_folders():
    folders = []
    for root, dirs, files in os.walk("."):
        parts = pathlib.Path(root).parts
        if ".git" in parts or ".github" in parts:
            continue
        if "README.md" in files:
            folders.append(root)
    return sorted(folders)

# ------------------------
# Navigation
# ------------------------

def build_nav(folders):
    entries = []
    for folder in folders:
        if folder == ".":
            continue
        name = os.path.basename(folder)
        pretty = name.replace("-", " ")
        encoded = encode_path(folder)
        entries.append((folder.lower(), pretty, encoded))

    entries.sort()

    links = [f"[🏠 Home]({BASE_URL}/) •"]
    for _, pretty, encoded in entries:
        links.append(f"[{pretty}]({BASE_URL}/{encoded}/) •")

    nav = (
        "## 📘 Navigation Menu\n"
        + " ".join(links)
        + "\n\n---\n<!-- inject-nav -->"
    )
    return nav

def strip_existing_nav(content: str) -> str:
    pattern = re.compile(
        r"## 📘 Navigation Menu[\s\S]*?<!-- inject-nav -->",
        re.MULTILINE,
    )
    cleaned = re.sub(pattern, "", content)
    return cleaned.lstrip("\r\n ")

def inject_nav(readme_path: str, nav: str):
    with open(readme_path, "r", encoding="utf-8") as f:
        original = f.read()

    body = strip_existing_nav(original)
    final = nav + "\n\n" + body

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(final)

# ------------------------
# index.md handling
# ------------------------

def sync_root_index():
    """
    Root index.md should be a mirror of README.md
    """
    if not os.path.exists("README.md"):
        return
    shutil.copyfile("README.md", "index.md")

def create_folder_index(folder: str):
    """
    For non-root folders:
    Create index.md listing immediate child folders with README.md
    """
    if folder == ".":
        return

    children = []
    for entry in sorted(os.listdir(folder)):
        child = os.path.join(folder, entry)
        if os.path.isdir(child) and os.path.exists(os.path.join(child, "README.md")):
            pretty = entry.replace("-", " ")
            children.append(f"- [{pretty}](./{entry}/)")

    if not children:
        return

    index_path = os.path.join(folder, "index.md")
    content = (
        "# Index\n\n"
        "## Subsections\n\n"
        + "\n".join(children)
        + "\n"
    )

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(content)

# ------------------------
# Main
# ------------------------

def main():
    folders = find_readme_folders()
    nav = build_nav(folders)

    # Inject nav into all README.md files
    for folder in folders:
        inject_nav(os.path.join(folder, "README.md"), nav)

    # Root: mirror README.md → index.md
    sync_root_index()

    # Subfolders: generate index.md
    for folder in folders:
        create_folder_index(folder)

    print("✔ Navigation updated")
    print("✔ Root index.md mirrors README.md")
    print("✔ Folder indexes generated")

if __name__ == "__main__":
    main()
