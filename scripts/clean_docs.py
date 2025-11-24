#!/usr/bin/env python3
"""
Script to clean documentation files:
1. Remove all emojis
2. Remove AI-style phrasing
3. Update NYT/RA-D-PS references to MAPS
"""

import re
from pathlib import Path
from typing import List, Tuple

# Emoji pattern - matches most Unicode emoji ranges
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F1E0-\U0001F1FF"  # flags (iOS)
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U0001F018-\U0001F270"
    "\U0001FA70-\U0001FAFF"
    "]+",
    flags=re.UNICODE
)

# AI-style phrases to remove or replace
AI_PHRASES = [
    # Conversational starters
    (r"^Here's\s+", ""),
    (r"^Let's\s+", ""),
    (r"^I've\s+", ""),
    (r"^We'll\s+", ""),
    (r"^We've\s+", ""),
    (r"^You'll\s+", ""),
    (r"^You can\s+", ""),
    (r"\bHere's\s+", ""),
    (r"\bLet's\s+", ""),
    (r"\bI've\s+", ""),
    (r"\bWe'll\s+", ""),
    (r"\bWe've\s+", ""),
    (r"\bYou'll\s+", ""),

    # Unnecessary qualifiers
    (r"\bsimply\s+", ""),
    (r"\bjust\s+", ""),
    (r"\beasily\s+", ""),
    (r"\bbasically\s+", ""),

    # Convert "You can X" to imperative
    (r"You can ([a-z])", lambda m: m.group(1).upper()),

    # Remove "This will" at start of sentence
    (r"^This will\s+", "This "),
]

# Product name replacements
NAME_REPLACEMENTS = [
    (r"\bNYT XML Parser\b", "MAPS"),
    (r"\bRA-D-PS\b", "MAPS"),
    (r"\bra-d-ps\b", "maps"),
    (r"\bra_d_ps\b", "maps"),
]


def clean_emojis(text: str) -> Tuple[str, int]:
    """Remove all emojis from text."""
    cleaned = EMOJI_PATTERN.sub("", text)
    # Also remove common text-based emojis
    cleaned = re.sub(r":\)|:\(|:D|:P|;\)|<3", "", cleaned)

    # Count removals
    removals = len(text) - len(cleaned)
    return cleaned, removals


def clean_ai_phrases(text: str) -> Tuple[str, int]:
    """Remove or replace AI-style phrasing."""
    original_length = len(text)

    for pattern, replacement in AI_PHRASES:
        if callable(replacement):
            text = re.sub(pattern, replacement, text, flags=re.MULTILINE | re.IGNORECASE)
        else:
            text = re.sub(pattern, replacement, text, flags=re.MULTILINE | re.IGNORECASE)

    removals = original_length - len(text)
    return text, removals


def update_product_names(text: str) -> Tuple[str, int]:
    """Update product name references."""
    changes = 0

    for pattern, replacement in NAME_REPLACEMENTS:
        new_text = re.sub(pattern, replacement, text)
        if new_text != text:
            changes += len(re.findall(pattern, text))
            text = new_text

    return text, changes


def clean_markdown_file(file_path: Path) -> Tuple[bool, dict]:
    """Clean a single markdown file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content

        stats = {
            'emojis_removed': 0,
            'ai_phrases_cleaned': 0,
            'names_updated': 0,
        }

        # Clean emojis
        content, emoji_count = clean_emojis(content)
        stats['emojis_removed'] = emoji_count

        # Clean AI phrases
        content, phrase_count = clean_ai_phrases(content)
        stats['ai_phrases_cleaned'] = phrase_count

        # Update product names
        content, name_count = update_product_names(content)
        stats['names_updated'] = name_count

        # Write back if changed
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            return True, stats

        return False, stats

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False, {}


def main():
    """Main execution function."""
    project_root = Path(__file__).parent.parent

    # Find all markdown files (excluding node_modules)
    md_files = []
    for pattern in ["*.md", "docs/**/*.md", "web_dashboard/*.md", "src/case_identifier/*.md"]:
        md_files.extend(project_root.glob(pattern))

    # Filter out node_modules
    md_files = [f for f in md_files if 'node_modules' not in str(f)]

    # Also exclude .pytest_cache
    md_files = [f for f in md_files if '.pytest_cache' not in str(f)]

    print(f"Found {len(md_files)} markdown files to process\n")

    total_stats = {
        'files_changed': 0,
        'emojis_removed': 0,
        'ai_phrases_cleaned': 0,
        'names_updated': 0,
    }

    changed_files = []

    for md_file in sorted(md_files):
        relative_path = md_file.relative_to(project_root)
        changed, stats = clean_markdown_file(md_file)

        if changed:
            total_stats['files_changed'] += 1
            total_stats['emojis_removed'] += stats['emojis_removed']
            total_stats['ai_phrases_cleaned'] += stats['ai_phrases_cleaned']
            total_stats['names_updated'] += stats['names_updated']
            changed_files.append(str(relative_path))

            changes = []
            if stats['emojis_removed'] > 0:
                changes.append(f"{stats['emojis_removed']} emojis")
            if stats['ai_phrases_cleaned'] > 0:
                changes.append(f"{stats['ai_phrases_cleaned']} chars (AI phrases)")
            if stats['names_updated'] > 0:
                changes.append(f"{stats['names_updated']} names")

            print(f"✓ {relative_path}")
            print(f"  Cleaned: {', '.join(changes)}")

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Files processed: {len(md_files)}")
    print(f"Files changed: {total_stats['files_changed']}")
    print(f"Emojis removed: {total_stats['emojis_removed']}")
    print(f"AI phrases cleaned: {total_stats['ai_phrases_cleaned']} characters")
    print(f"Product names updated: {total_stats['names_updated']}")
    print(f"\nChanged files:")
    for file in changed_files:
        print(f"  - {file}")


if __name__ == "__main__":
    main()
