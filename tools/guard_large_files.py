#!/usr/bin/env python3
import os
import sys
import subprocess

LIMIT_MB = 10  # size threshold for LFS in megabytes
ROOT = os.path.abspath(os.path.dirname(__file__) + "/..")

def humanize(nbytes):
    # format size in human-friendly units
    for unit in ['B','KB','MB','GB','TB']:
        if nbytes < 1024:
            return f"{nbytes:.1f}{unit}"
        nbytes /= 1024
    return f"{nbytes:.1f}PB"

def lfs_tracked_paths():
    try:
        out = subprocess.check_output(["git", "lfs", "ls-files"], text=True)
        tracked = set()
        for line in out.strip().splitlines():
            # line format: "<oid> <path>"
            p = line.split(None, 1)[-1].strip()
            tracked.add(os.path.normpath(p))
        return tracked
    except Exception:
        return set()

def main():
    lfs_set = lfs_tracked_paths()
    bad = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        # skip .git and other hidden dirs
        if ".git" in dirpath.split(os.sep):
            continue
        for fn in filenames:
            path = os.path.normpath(os.path.join(dirpath, fn))
            try:
                size = os.path.getsize(path)
            except FileNotFoundError:
                continue
            if size >= LIMIT_MB * 1024 * 1024:
                rel = os.path.relpath(path, ROOT)
                if rel not in lfs_set:
                    bad.append((rel, size))

    if bad:
        print("ERROR: Large non-LFS files found:")
        for rel, size in sorted(bad, key=lambda x: x[1], reverse=True):
            print(f" - {rel} ({humanize(size)})")
        sys.exit(1)
    else:
        print(f"OK: No large non-LFS files detected (limit {LIMIT_MB} MB).")

if __name__ == "__main__":
    main()
