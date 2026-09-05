#!/usr/bin/env python3
"""
Open Cognition 项目结构扁平化迁移脚本
- domains/ 扁平化到根目录
- skills/ 融入各领域
- wisdom-masters/ 融入 religion/
- 配套文件收拢到 _meta/
- 修复所有 .md 文件中的相对路径
"""

import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAINS = [
    "philosophy", "religion", "sociology", "psychology",
    "ethics-politics", "aesthetics", "literature", "arts",
    "cognitive-systems"
]
SKILL_DOMAIN_MAP = {
    "philosophy-frameworks": "philosophy",
    "religion-frameworks": "religion",
    "sociology-frameworks": "sociology",
    "psychology-frameworks": "psychology",
    "ethics-politics-frameworks": "ethics-politics",
    "aesthetics-frameworks": "aesthetics",
    "literature-frameworks": "literature",
    "arts-frameworks": "arts",
    "cognitive-systems-frameworks": "cognitive-systems",
}


def run(cmd, check=True):
    """Run command from an argument list (str input is split with shlex; no shell)."""
    argv = shlex.split(cmd) if isinstance(cmd, str) else list(cmd)
    print(f"  > {' '.join(argv)}")
    result = subprocess.run(argv, capture_output=True, text=True, cwd=ROOT)
    if check and result.returncode != 0:
        print(f"  WARN: {result.stderr.strip()}")
    return result


def git_mv(src, dst):
    """Move file/dir using git mv, falling back to shutil.move."""
    src_full = os.path.join(ROOT, src)
    dst_full = os.path.join(ROOT, dst)
    if not os.path.exists(src_full):
        print(f"  SKIP (not found): {src}")
        return
    os.makedirs(os.path.dirname(dst_full), exist_ok=True)
    r = run(["git", "mv", src, dst], check=False)
    if r.returncode != 0:
        shutil.move(src_full, dst_full)
        run(["git", "add", dst], check=False)


def phase1_flatten_domains():
    """Move domains/X/ -> X/ for each domain."""
    print("\n=== Phase 1: Flatten domains/ ===")
    for d in DOMAINS:
        git_mv(f"domains/{d}", d)
    domains_dir = os.path.join(ROOT, "domains")
    if os.path.exists(domains_dir) and not os.listdir(domains_dir):
        os.rmdir(domains_dir)


def phase2_merge_skills():
    """Move skills/X-frameworks/ -> X/skills/."""
    print("\n=== Phase 2: Merge skills into domains ===")
    skills_dir = os.path.join(ROOT, "skills")
    if not os.path.exists(skills_dir):
        return
    for skill_folder, domain in SKILL_DOMAIN_MAP.items():
        src = os.path.join(skills_dir, skill_folder)
        if not os.path.exists(src):
            continue
        dst_base = os.path.join(ROOT, domain, "skills")
        os.makedirs(dst_base, exist_ok=True)
        for item in os.listdir(src):
            if item == "README.md":
                dst_readme = os.path.join(dst_base, "README.md")
                if not os.path.exists(dst_readme):
                    git_mv(f"skills/{skill_folder}/{item}", f"{domain}/skills/{item}")
            else:
                git_mv(f"skills/{skill_folder}/{item}", f"{domain}/skills/{item}")
    # Clean up
    remaining = [f for f in os.listdir(skills_dir) if not f.startswith('.')]
    if not remaining:
        shutil.rmtree(skills_dir)
        run(["git", "add", "-A", "skills/"], check=False)


def phase3_merge_wisdom_masters():
    """Move wisdom-masters/ -> religion/wisdom-masters/."""
    print("\n=== Phase 3: Merge wisdom-masters into religion/ ===")
    wm_dir = os.path.join(ROOT, "wisdom-masters")
    if not os.path.exists(wm_dir):
        return
    dst = os.path.join(ROOT, "religion", "wisdom-masters")
    os.makedirs(dst, exist_ok=True)
    for item in os.listdir(wm_dir):
        if item.startswith('.'):
            continue
        git_mv(f"wisdom-masters/{item}", f"religion/wisdom-masters/{item}")
    remaining = [f for f in os.listdir(wm_dir) if not f.startswith('.')]
    if not remaining:
        shutil.rmtree(wm_dir)
        run(["git", "add", "-A", "wisdom-masters/"], check=False)


def phase4_meta_consolidation():
    """Move supporting dirs into _meta/."""
    print("\n=== Phase 4: Consolidate into _meta/ ===")
    os.makedirs(os.path.join(ROOT, "_meta"), exist_ok=True)
    # meta/ -> _meta/
    meta_dir = os.path.join(ROOT, "meta")
    if os.path.exists(meta_dir):
        for item in sorted(os.listdir(meta_dir)):
            if item.startswith('.'):
                continue
            git_mv(f"meta/{item}", f"_meta/{item}")
        remaining = [f for f in os.listdir(meta_dir) if not f.startswith('.')]
        if not remaining:
            shutil.rmtree(meta_dir)
            run(["git", "add", "-A", "meta/"], check=False)
    # visual/ -> _meta/visual/
    if os.path.exists(os.path.join(ROOT, "visual")):
        git_mv("visual", "_meta/visual")
    # reports/ -> _meta/reports/
    if os.path.exists(os.path.join(ROOT, "reports")):
        git_mv("reports", "_meta/reports")
    # scripts/ -> _meta/scripts/
    if os.path.exists(os.path.join(ROOT, "scripts")):
        git_mv("scripts", "_meta/scripts")
    # _includes/ -> _meta/_includes/
    if os.path.exists(os.path.join(ROOT, "_includes")):
        git_mv("_includes", "_meta/_includes")
    # _config.yml -> _meta/
    if os.path.exists(os.path.join(ROOT, "_config.yml")):
        git_mv("_config.yml", "_meta/_config.yml")


def build_path_mapping():
    """
    Build old_abs -> new_abs and new_abs -> old_abs mappings.
    Done AFTER physical moves by scanning new structure and computing old paths.
    """
    old_to_new = {}
    new_to_old = {}
    skip_dirs = {'.git', '.github', '.claude', '.qoder', 'node_modules', '_meta'}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        rel_dir = os.path.relpath(dirpath, ROOT)
        parts = rel_dir.split(os.sep)
        if any(p in skip_dirs or (p.startswith('.') and p != '.') for p in parts):
            continue
        for f in filenames:
            new_abs = os.path.normpath(os.path.join(dirpath, f))
            new_rel = os.path.relpath(new_abs, ROOT)
            old_rel = reverse_map_path(new_rel)
            if old_rel != new_rel:
                old_abs = os.path.normpath(os.path.join(ROOT, old_rel))
                old_to_new[old_abs] = new_abs
                new_to_old[new_abs] = old_abs
    return old_to_new, new_to_old


def reverse_map_path(new_rel):
    """Given a new relative path, compute what the old relative path was."""
    parts = new_rel.replace('\\', '/').split('/')

    # Domain files: X/... -> domains/X/...
    if parts[0] in DOMAINS:
        return "domains/" + new_rel

    # Skills: domain/skills/skill-name/... -> skills/domain-frameworks/skill-name/...
    if len(parts) >= 3 and parts[0] in DOMAINS and parts[1] == "skills":
        domain = parts[0]
        skill_name = parts[2]
        rest = "/".join(parts[3:])
        old = f"skills/{domain}-frameworks/{skill_name}"
        if rest:
            old += "/" + rest
        return old

    # Wisdom-masters: religion/wisdom-masters/... -> wisdom-masters/...
    if parts[0] == "religion" and len(parts) >= 2 and parts[1] == "wisdom-masters":
        rest = "/".join(parts[2:])
        return "wisdom-masters/" + rest if rest else "wisdom-masters/README.md"

    return new_rel


def resolve_and_remap(rel_path, file_old_dir, file_new_dir, old_to_new):
    """
    Resolve a relative path from the file's OLD location, look up the target
    in old_to_new, and compute the new relative path from the file's NEW location.
    """
    # Separate anchor
    anchor = ''
    clean = rel_path
    if '?' in rel_path:
        clean = rel_path.split('?')[0]
    if '#' in clean:
        clean, anchor = clean.split('#', 1)
        anchor = '#' + anchor

    # Resolve to old absolute path
    old_target_abs = os.path.normpath(os.path.join(file_old_dir, clean))

    # Look up in mapping
    if old_target_abs in old_to_new:
        new_target_abs = old_to_new[old_target_abs]
        new_rel = os.path.relpath(new_target_abs, file_new_dir).replace('\\', '/')
        return new_rel + anchor

    # Try with .md extension
    if not old_target_abs.endswith('.md'):
        test = old_target_abs + '.md'
        if test in old_to_new:
            new_target_abs = old_to_new[test]
            new_rel = os.path.relpath(new_target_abs, file_new_dir).replace('\\', '/')
            return new_rel + anchor

    # Try without .md (for directory references)
    if old_target_abs.endswith('.md'):
        test = old_target_abs[:-3]
        if test in old_to_new:
            new_target_abs = old_to_new[test]
            new_rel = os.path.relpath(new_target_abs, file_new_dir).replace('\\', '/')
            return new_rel + anchor

    return rel_path  # couldn't resolve


def fix_paths_in_file(filepath, old_to_new, new_to_old):
    """Fix all relative paths in a single .md file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    file_new_abs = os.path.normpath(filepath)
    file_new_dir = os.path.dirname(file_new_abs)

    # Get old file location to resolve old paths correctly
    file_old_abs = new_to_old.get(file_new_abs, file_new_abs)
    file_old_dir = os.path.dirname(file_old_abs)

    # Pattern 1: Fix markdown links [text](path)
    def fix_md_link(match):
        full_match = match.group(0)
        text = match.group(1)
        path = match.group(2)
        if path.startswith(('http://', 'https://', '#', 'mailto:', 'ftp://')):
            return full_match
        if not path.startswith('./') and not path.startswith('../'):
            return full_match
        new_path = resolve_and_remap(path, file_old_dir, file_new_dir, old_to_new)
        if new_path != path:
            return f"[{text}]({new_path})"
        return full_match

    content = re.sub(r'\[([^\]]*)\]\(([^)]+)\)', fix_md_link, content)

    # Pattern 2: Fix YAML frontmatter paths
    in_frontmatter = False
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        if line.strip() == '---':
            in_frontmatter = not in_frontmatter
            new_lines.append(line)
            continue

        if in_frontmatter and re.match(r'^\s+-\s+\.\.?/', line):
            stripped = line.strip()
            prefix = line[:len(line) - len(stripped)]
            path = stripped[2:].strip()  # remove '- '
            new_path = resolve_and_remap(path, file_old_dir, file_new_dir, old_to_new)
            if new_path != path:
                new_lines.append(f"{prefix}- {new_path}")
            else:
                new_lines.append(line)
        elif in_frontmatter and re.match(r'^linked_thinker:\s+\.\.?/', line):
            key = "linked_thinker: "
            path = line[len(key):].strip()
            new_path = resolve_and_remap(path, file_old_dir, file_new_dir, old_to_new)
            if new_path != path:
                new_lines.append(f"{key}{new_path}")
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    content = '\n'.join(new_lines)

    if content != original:
        real = Path(filepath).resolve()
        root_real = Path(ROOT).resolve()
        try:
            real.relative_to(root_real)
        except ValueError:
            print(f"  SKIP (outside repo): {filepath}")
            return False
        real.write_text(content, encoding='utf-8')
        return True
    return False


def phase5_fix_all_paths():
    """Fix all relative paths in all .md files."""
    print("\n=== Phase 5: Fix relative paths ===")
    old_to_new, new_to_old = build_path_mapping()
    print(f"  Path mapping has {len(old_to_new)} entries")

    fixed_count = 0
    total = 0
    skip_dirs = {'.git', '.github', '.claude', '.qoder', 'node_modules', '_meta'}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        rel_dir = os.path.relpath(dirpath, ROOT)
        parts = rel_dir.split(os.sep)
        if any(p in skip_dirs for p in parts if p != '.'):
            continue
        for f in filenames:
            if not f.endswith('.md'):
                continue
            filepath = os.path.join(dirpath, f)
            total += 1
            if fix_paths_in_file(filepath, old_to_new, new_to_old):
                fixed_count += 1

    print(f"  Fixed {fixed_count} / {total} .md files")


def main():
    print(f"Root: {ROOT}")
    print("Starting Open Cognition restructure...")

    phase1_flatten_domains()
    phase2_merge_skills()
    phase3_merge_wisdom_masters()
    phase4_meta_consolidation()
    phase5_fix_all_paths()

    print("\n=== Done! ===")
    print("Next steps:")
    print("  1. Update INDEX.md, TAGS.md, README.md, AGENT.md with new paths")
    print("  2. Run 'git status' to review")
    print("  3. Commit when satisfied")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Open Cognition 项目结构扁平化迁移脚本
- domains/ 扁平化到根目录
- skills/ 融入各领域
- wisdom-masters/ 融入 religion/
- 配套文件收拢到 _meta/
- 修复所有 .md 文件中的相对路径
"""

import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAINS = [
    "philosophy", "religion", "sociology", "psychology",
    "ethics-politics", "aesthetics", "literature", "arts",
    "cognitive-systems"
]
SKILL_DOMAIN_MAP = {
    "philosophy-frameworks": "philosophy",
    "religion-frameworks": "religion",
    "sociology-frameworks": "sociology",
    "psychology-frameworks": "psychology",
    "ethics-politics-frameworks": "ethics-politics",
    "aesthetics-frameworks": "aesthetics",
    "literature-frameworks": "literature",
    "arts-frameworks": "arts",
    "cognitive-systems-frameworks": "cognitive-systems",
}


def run(cmd, check=True):
    """Run command from an argument list (str input is split with shlex; no shell)."""
    argv = shlex.split(cmd) if isinstance(cmd, str) else list(cmd)
    print(f"  > {' '.join(argv)}")
    result = subprocess.run(argv, capture_output=True, text=True, cwd=ROOT)
    if check and result.returncode != 0:
        print(f"  WARN: {result.stderr.strip()}")
    return result


def git_mv(src, dst):
    """Move file/dir using git mv, falling back to os.rename."""
    src_full = os.path.join(ROOT, src)
    dst_full = os.path.join(ROOT, dst)
    if not os.path.exists(src_full):
        print(f"  SKIP (not found): {src}")
        return
    os.makedirs(os.path.dirname(dst_full), exist_ok=True)
    r = run(["git", "mv", src, dst], check=False)
    if r.returncode != 0:
        # fallback: manual move + git add
        shutil.move(src_full, dst_full)
        run(["git", "add", dst], check=False)


def phase1_flatten_domains():
    """Move domains/X/ -> X/ for each domain."""
    print("\n=== Phase 1: Flatten domains/ ===")
    for d in DOMAINS:
        git_mv(f"domains/{d}", d)
    # Remove empty domains/ dir
    domains_dir = os.path.join(ROOT, "domains")
    if os.path.exists(domains_dir) and not os.listdir(domains_dir):
        os.rmdir(domains_dir)


def phase2_merge_skills():
    """Move skills/X-frameworks/ -> X/skills/."""
    print("\n=== Phase 2: Merge skills into domains ===")
    skills_dir = os.path.join(ROOT, "skills")
    if not os.path.exists(skills_dir):
        return
    for skill_folder, domain in SKILL_DOMAIN_MAP.items():
        src = os.path.join(skills_dir, skill_folder)
        if not os.path.exists(src):
            continue
        dst_base = os.path.join(ROOT, domain, "skills")
        os.makedirs(dst_base, exist_ok=True)
        for item in os.listdir(src):
            if item == "README.md":
                # Move skills README to domain skills README if no conflict
                dst_readme = os.path.join(dst_base, "README.md")
                if not os.path.exists(dst_readme):
                    git_mv(f"skills/{skill_folder}/{item}", f"{domain}/skills/{item}")
            else:
                git_mv(f"skills/{skill_folder}/{item}", f"{domain}/skills/{item}")
    # Remove empty skills/ dir
    remaining = [f for f in os.listdir(skills_dir) if not f.startswith('.')]
    if not remaining:
        shutil.rmtree(skills_dir)
        run(["git", "add", "-A", "skills/"], check=False)


def phase3_merge_wisdom_masters():
    """Move wisdom-masters/ -> religion/wisdom-masters/."""
    print("\n=== Phase 3: Merge wisdom-masters into religion/ ===")
    wm_dir = os.path.join(ROOT, "wisdom-masters")
    if not os.path.exists(wm_dir):
        return
    dst = os.path.join(ROOT, "religion", "wisdom-masters")
    os.makedirs(dst, exist_ok=True)
    # Move contents
    for item in os.listdir(wm_dir):
        if item.startswith('.'):
            continue
        git_mv(f"wisdom-masters/{item}", f"religion/wisdom-masters/{item}")
    # Clean up empty dir
    remaining = [f for f in os.listdir(wm_dir) if not f.startswith('.')]
    if not remaining:
        shutil.rmtree(wm_dir)
        run(["git", "add", "-A", "wisdom-masters/"], check=False)


def phase4_meta_consolidation():
    """Move supporting dirs into _meta/."""
    print("\n=== Phase 4: Consolidate into _meta/ ===")
    os.makedirs(os.path.join(ROOT, "_meta"), exist_ok=True)
    # meta/ -> _meta/
    meta_dir = os.path.join(ROOT, "meta")
    if os.path.exists(meta_dir):
        for item in os.listdir(meta_dir):
            if item.startswith('.'):
                continue
            git_mv(f"meta/{item}", f"_meta/{item}")
        remaining = [f for f in os.listdir(meta_dir) if not f.startswith('.')]
        if not remaining:
            shutil.rmtree(meta_dir)
            run(["git", "add", "-A", "meta/"], check=False)
    # visual/ -> _meta/visual/
    if os.path.exists(os.path.join(ROOT, "visual")):
        git_mv("visual", "_meta/visual")
    # reports/ -> _meta/reports/
    if os.path.exists(os.path.join(ROOT, "reports")):
        git_mv("reports", "_meta/reports")
    # scripts/ -> _meta/scripts/
    if os.path.exists(os.path.join(ROOT, "scripts")):
        git_mv("scripts", "_meta/scripts")
    # _includes/ -> _meta/_includes/
    if os.path.exists(os.path.join(ROOT, "_includes")):
        git_mv("_includes", "_meta/_includes")
    # _config.yml -> _meta/
    if os.path.exists(os.path.join(ROOT, "_config.yml")):
        git_mv("_config.yml", "_meta/_config.yml")


def build_path_mapping():
    """
    Build old_abs_path -> new_abs_path mapping for all files.
    This is done AFTER physical moves, so we scan the new structure.
    """
    mapping = {}
    # Scan all files in root (excluding _meta, .git, .github, etc.)
    skip_dirs = {'.git', '.github', '.claude', '.qoder', 'node_modules', '_meta'}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        # Skip _meta and hidden dirs
        rel_dir = os.path.relpath(dirpath, ROOT)
        parts = rel_dir.split(os.sep)
        if any(p in skip_dirs or p.startswith('.') for p in parts if p != '.'):
            continue
        for f in filenames:
            new_abs = os.path.join(dirpath, f)
            new_rel = os.path.relpath(new_abs, ROOT)
            # Calculate old path
            old_rel = reverse_map_path(new_rel)
            if old_rel != new_rel:
                old_abs = os.path.join(ROOT, old_rel)
                mapping[old_abs] = new_abs
    return mapping


def reverse_map_path(new_rel):
    """Given a new relative path, figure out what the old relative path was."""
    parts = new_rel.replace('\\', '/').split('/')

    # Check if it's a domain file (was under domains/)
    if parts[0] in DOMAINS:
        # domain/X -> domains/domain/X
        old = "domains/" + new_rel
        return old

    # Check if it's a skill (was under skills/X-frameworks/)
    if len(parts) >= 3 and parts[0] in DOMAINS and parts[1] == "skills":
        domain = parts[0]
        skill_name = parts[2]
        # domain/skills/X/... -> skills/domain-frameworks/X/...
        rest = "/".join(parts[3:])
        old = f"skills/{domain}-frameworks/{skill_name}"
        if rest:
            old += "/" + rest
        return old

    # Check if it's wisdom-masters content (was under wisdom-masters/)
    if parts[0] == "religion" and len(parts) >= 2 and parts[1] == "wisdom-masters":
        rest = "/".join(parts[2:])
        old = "wisdom-masters/" + rest if rest else "wisdom-masters/README.md"
        return old

    # Check if it's cognitive-theory skills (stayed in same place)
    # These were always under domains/religion/buddhism/concepts/cognitive-theory/skills/
    # and they moved to religion/buddhism/concepts/cognitive-theory/skills/
    # Already handled by the domain mapping above

    return new_rel  # no change


def fix_paths_in_file(filepath, old_to_new):
    """Fix all relative paths in a single .md file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    file_dir = os.path.dirname(filepath)

    # Pattern 1: Fix markdown links (text)(path)
    def fix_md_link(match):
        full_match = match.group(0)
        text = match.group(1)
        path = match.group(2)

        # Skip absolute URLs and anchors
        if path.startswith(('http://', 'https://', '#', 'mailto:')):
            return full_match
        # Skip non-relative paths
        if not path.startswith('./') and not path.startswith('../'):
            return full_match

        new_path = resolve_and_remap(path, file_dir, old_to_new)
        if new_path != path:
            return f"[{text}]({new_path})"
        return full_match

    content = re.sub(r'\[([^\]]*)\]\(([^)]+)\)', fix_md_link, content)

    # Pattern 2: Fix YAML frontmatter paths (  - path)
    in_frontmatter = False
    lines = content.split('\n')
    new_lines = []
    for i, line in enumerate(lines):
        if line.strip() == '---':
            in_frontmatter = not in_frontmatter
            new_lines.append(line)
            continue

        if in_frontmatter and re.match(r'^\s+-\s+\.\./', line):
            # This is a YAML list item with a relative path
            stripped = line.strip()
            prefix = line[:len(line) - len(stripped)]
            path = stripped.lstrip('- ').strip()
            new_path = resolve_and_remap(path, file_dir, old_to_new)
            if new_path != path:
                new_lines.append(f"{prefix}- {new_path}")
            else:
                new_lines.append(line)
        elif in_frontmatter and re.match(r'^linked_thinker:\s+\.\./', line):
            prefix = "linked_thinker: "
            path = line[len(prefix):].strip()
            new_path = resolve_and_remap(path, file_dir, old_to_new)
            if new_path != path:
                new_lines.append(f"{prefix}{new_path}")
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    content = '\n'.join(new_lines)

    # Pattern 3: Fix plain text paths like (../../skills/...) that aren't in links
    # Already handled by Pattern 1

    if content != original:
        real = Path(filepath).resolve()
        root_real = Path(ROOT).resolve()
        try:
            real.relative_to(root_real)
        except ValueError:
            print(f"  SKIP (outside repo): {filepath}")
            return False
        real.write_text(content, encoding='utf-8')
        return True
    return False


def resolve_and_remap(rel_path, file_dir, old_to_new):
    """
    Given a relative path from a file's directory, resolve it to absolute,
    look up in old_to_new mapping, and convert back to relative.
    """
    # Clean up path
    clean = rel_path.split('#')[0].split('?')[0]  # remove anchors/params

    # Resolve to absolute (using old structure)
    old_abs = os.path.normpath(os.path.join(file_dir, clean))

    # If it exists in the mapping, get the new abs path
    if old_abs in old_to_new:
        new_abs = old_to_new[old_abs]
        # Calculate new relative path from file_dir to new_abs
        new_rel = os.path.relpath(new_abs, file_dir)
        # Normalize to forward slashes
        new_rel = new_rel.replace('\\', '/')
        # Preserve anchors
        if '#' in rel_path:
            new_rel += '#' + rel_path.split('#', 1)[1]
        return new_rel

    # Not in mapping — try without the file extension
    for ext in ['.md', '']:
        test = old_abs + ext if not old_abs.endswith(ext) else old_abs
        if test in old_to_new:
            new_abs = old_to_new[test]
            new_rel = os.path.relpath(new_abs, file_dir)
            new_rel = new_rel.replace('\\', '/')
            if '#' in rel_path:
                new_rel += '#' + rel_path.split('#', 1)[1]
            return new_rel

    return rel_path  # couldn't resolve, return as-is


def phase5_fix_all_paths():
    """Fix all relative paths in all .md files."""
    print("\n=== Phase 5: Fix relative paths ===")
    old_to_new = build_path_mapping()
    print(f"  Path mapping has {len(old_to_new)} entries")

    fixed_count = 0
    total = 0

    # Scan all .md files in the new structure
    skip_dirs = {'.git', '.github', '.claude', '.qoder', 'node_modules', '_meta'}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        rel_dir = os.path.relpath(dirpath, ROOT)
        parts = rel_dir.split(os.sep)
        if any(p in skip_dirs for p in parts if p != '.'):
            continue
        for f in filenames:
            if not f.endswith('.md'):
                continue
            filepath = os.path.join(dirpath, f)
            total += 1
            if fix_paths_in_file(filepath, old_to_new):
                fixed_count += 1
                print(f"  Fixed: {os.path.relpath(filepath, ROOT)}")

    print(f"  Fixed {fixed_count} / {total} .md files")


def main():
    print(f"Root: {ROOT}")
    print("Starting Open Cognition restructure...")

    # Check git status
    r = run(["git", "status", "--porcelain"], check=False)
    if r.stdout.strip():
        print("\nWARNING: Uncommitted changes detected. Commit first?")
        print(r.stdout[:500])
        # Continue anyway — the script uses git mv which handles staging

    phase1_flatten_domains()
    phase2_merge_skills()
    phase3_merge_wisdom_masters()
    phase4_meta_consolidation()
    phase5_fix_all_paths()

    print("\n=== Done! ===")
    print("Run 'git status' to review changes.")
    print("Then update INDEX.md, TAGS.md, README.md etc. manually.")


if __name__ == "__main__":
    main()
