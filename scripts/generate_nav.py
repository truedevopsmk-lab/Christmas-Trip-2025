#!/usr/bin/env python3
import os
import urllib.parse
import pathlib
import re

GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "")
if GITHUB_REPOSITORY:
    USER, REPO = GITHUB_REPOSITORY.split("/",1)
    BASE_URL = f"https://{USER}.github.io/{REPO}"
else:
    USER = "USERNAME"
    REPO = "REPO"
    BASE_URL = f"https://{USER}.github.io/{REPO}"

def encode_path(path):
    parts = [urllib.parse.quote(p) for p in os.path.normpath(path).strip("./").split(os.sep) if p]
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

def build_nav(folders):
    entries = []
    for folder in folders:
        if folder == ".":
            continue
        name = os.path.basename(folder)
        pretty = name.replace("-", " ")
        encoded = encode_path(folder)
        entries.append((folder, pretty, encoded))
    entries.sort(key=lambda x: x[0].lower())
    parts = [f"[🏠 Home]({BASE_URL}/) •"]
    for _, pretty, encoded in entries:
        parts.append(f"[{pretty}]({BASE_URL}/{encoded}/) •")
    # join into single line with spaces, ensure no literal \n remains
    nav_line = "## 📘 Navigation Menu\n" + " ".join(parts) + "\n\n---\n<!-- inject-nav -->"
    # replace any accidental literal backslash-n sequences
    nav_line = nav_line.replace("\\n", "\n")
    return nav_line

def remove_all_existing_navs(content):
    pattern = re.compile(r"## 📘 Navigation Menu[\s\S]*?<!-- inject-nav -->", re.MULTILINE)
    new = re.sub(pattern, "", content)
    return new.lstrip("\r\n ")

def inject_nav_into_readme(file_path, nav):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    rest = remove_all_existing_navs(content)
    new_content = nav + "\n\n" + rest
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)

def create_index_md_for_folder(folder):
    child_links = []
    try:
        entries = sorted(os.listdir(folder))
    except FileNotFoundError:
        return
    for p in entries:
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
    for folder in folders:
        readme = os.path.join(folder, "README.md")
        inject_nav_into_readme(readme, nav)
    for folder in folders:
        create_index_md_for_folder(folder)
    print("Done. Navigation injected and index.md files created where applicable.")

if __name__ == '__main__':
    main()
