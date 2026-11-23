#!/usr/bin/env python3
"""renameforge.py - A command-line tool for renaming files with various transformations."""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rename files in a directory with various transformations.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/dir --prefix "new_" --apply
  %(prog)s /path/to/dir --pattern "(\\d+)" --replace "file_\\1" --apply
  %(prog)s /path/to/dir --suffix ".bak" --ext ".txt,.md"
  %(prog)s /path/to/dir --undo renameforge-log.json
"""
    )
    parser.add_argument("directory", help="Directory containing files to rename")
    
    transform_group = parser.add_mutually_exclusive_group()
    transform_group.add_argument(
        "--pattern", metavar="REGEX", help="Regex pattern for substitution"
    )
    transform_group.add_argument(
        "--prefix", metavar="TEXT", help="Add prefix to filenames"
    )
    transform_group.add_argument(
        "--suffix", metavar="TEXT", help="Add suffix to filenames"
    )
    transform_group.add_argument(
        "--lower", action="store_true", help="Convert filenames to lowercase"
    )
    transform_group.add_argument(
        "--spaces-to-dash", action="store_true", dest="spaces_to_dash",
        help="Replace spaces with dashes in filenames"
    )
    
    parser.add_argument(
        "--replace", metavar="TEMPLATE",
        help="Replacement template for --pattern (supports \\1, \\2, etc.)"
    )
    parser.add_argument(
        "--ext", metavar="EXTENSIONS",
        help="Comma-separated list of extensions to filter (e.g., '.txt,.md')"
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Actually rename files (default is dry-run)"
    )
    parser.add_argument(
        "--undo", metavar="LOGFILE",
        help="Reverse renames recorded in LOGFILE"
    )
    
    return parser.parse_args()


def get_transform_func(args: argparse.Namespace):
    if args.pattern:
        if not args.replace:
            print("Error: --replace is required when using --pattern", file=sys.stderr)
            sys.exit(1)
        pattern = args.pattern
        replace = args.replace
        def transform(name: str) -> str:
            return re.sub(pattern, replace, name)
        return transform
    elif args.prefix:
        prefix = args.prefix
        def transform(name: str) -> str:
            return prefix + name
        return transform
    elif args.suffix:
        suffix = args.suffix
        def transform(name: str) -> str:
            return name + suffix
        return transform
    elif args.lower:
        def transform(name: str) -> str:
            return name.lower()
        return transform
    elif args.spaces_to_dash:
        def transform(name: str) -> str:
            return name.replace(" ", "-")
        return transform
    else:
        def transform(name: str) -> str:
            return name
        return transform


def matches_extension(filename: str, extensions: Optional[str]) -> bool:
    if not extensions:
        return True
    ext_list = [e.strip() for e in extensions.split(",")]
    file_ext = Path(filename).suffix
    return file_ext in ext_list


def collect_files(directory: Path, extensions: Optional[str]) -> list[Path]:
    files = []
    for item in directory.iterdir():
        if item.is_file() and matches_extension(item.name, extensions):
            files.append(item)
    return sorted(files)


def perform_rename(
    old_path: Path, new_path: Path, apply: bool, log_entries: list
) -> bool:
    if old_path == new_path:
        return False
    
    if new_path.exists():
        print(f"Warning: Skipping {old_path.name} -> {new_path.name}: target exists", file=sys.stderr)
        return False
    
    if apply:
        try:
            old_path.rename(new_path)
            log_entries.append({
                "old": str(old_path),
                "new": str(new_path)
            })
            return True
        except OSError as e:
            print(f"Error renaming {old_path.name}: {e}", file=sys.stderr)
            return False
    else:
        return True


def undo_rename(logfile: Path, directory: Path) -> int:
    try:
        with open(logfile, "r") as f:
            log_entries = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error reading log file: {e}", file=sys.stderr)
        return 1
    
    count = 0
    for entry in reversed(log_entries):
        old_path = Path(entry["old"])
        new_path = Path(entry["new"])
        
        if not new_path.exists():
            print(f"Warning: {new_path.name} does not exist, cannot undo", file=sys.stderr)
            continue
        
        if old_path.exists():
            print(f"Warning: {old_path.name} already exists, skipping undo", file=sys.stderr)
            continue
        
        try:
            new_path.rename(old_path)
            print(f"Undo: {new_path.name} -> {old_path.name}")
            count += 1
        except OSError as e:
            print(f"Error undoing rename: {e}", file=sys.stderr)
    
    return 0 if count > 0 else 1


def main():
    args = parse_args()
    directory = Path(args.directory)
    
    if not directory.is_dir():
        print(f"Error: {directory} is not a directory", file=sys.stderr)
        sys.exit(1)
    
    if args.undo:
        if not args.undo:
            print("Error: --undo requires a log file path", file=sys.stderr)
            sys.exit(1)
        logfile = Path(args.undo)
        sys.exit(undo_rename(logfile, directory))
    
    transform = get_transform_func(args)
    log_entries = []
    count = 0
    
    files = collect_files(directory, args.ext)
    
    for old_path in files:
        new_name = transform(old_path.name)
        new_path = old_path.parent / new_name
        
        if args.apply:
            if perform_rename(old_path, new_path, True, log_entries):
                print(f"{old_path.name} -> {new_name}")
                count += 1
        else:
            if old_path != new_path:
                print(f"{old_path.name} -> {new_name}")
                count += 1
    
    if args.apply and log_entries:
        log_path = directory / "renameforge-log.json"
        try:
            with open(log_path, "w") as f:
                json.dump(log_entries, f, indent=2)
        except IOError as e:
            print(f"Error writing log file: {e}", file=sys.stderr)
            sys.exit(1)
    
    print(f"\nSummary: {count} file{'s' if count != 1 else ''} {'renamed' if args.apply else 'would be renamed'}")
    sys.exit(0)


if __name__ == "__main__":
    main()
