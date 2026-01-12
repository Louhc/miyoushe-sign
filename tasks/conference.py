#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Security & Cryptography Conference Deadlines
Data source: https://sec-deadlines.github.io/
"""

import os
import requests
from datetime import datetime, timedelta

# Conference data URL
CONF_URL = "https://raw.githubusercontent.com/sec-deadlines/sec-deadlines.github.io/master/_data/conferences.yml"

# How many days ahead to show deadlines
DAYS_AHEAD = int(os.environ.get("CONF_DAYS_AHEAD", "30"))

# Filter by tags (empty = all)
# Common tags: SEC, PRIV, CRYPTO, CONF, TOP4
FILTER_TAGS_STR = os.environ.get("CONF_FILTER_TAGS", "SEC,CRYPTO")
FILTER_TAGS = [t.strip().upper() for t in FILTER_TAGS_STR.split(",") if t.strip()]


def parse_yaml_simple(text: str) -> list:
    """
    Simple YAML parser for conference data
    (avoiding external dependency)
    """
    conferences = []
    current = {}

    for line in text.split('\n'):
        line = line.rstrip()

        if line.startswith('- name:'):
            if current:
                conferences.append(current)
            current = {'name': line.split(':', 1)[1].strip()}
        elif line.strip().startswith('- "') and 'deadlines' in current:
            # Multi-line deadline item (must check before key:value due to time containing ":")
            current['deadlines'].append(line.strip().strip('- "\''))
        elif line.startswith('  ') and ':' in line and current:
            stripped = line.strip()
            # Skip lines that look like list items
            if stripped.startswith('- '):
                continue
            key, value = stripped.split(':', 1)
            value = value.strip()

            # Handle lists
            if key == 'deadline':
                if value.startswith('['):
                    # Inline list: ["2025-06-05 23:59", "2025-11-13 23:59"]
                    value = value.strip('[]')
                    current['deadlines'] = [
                        d.strip().strip('"\'')
                        for d in value.split(',') if d.strip()
                    ]
                else:
                    current['deadlines'] = []
            elif key == 'tags':
                if value.startswith('['):
                    value = value.strip('[]')
                    current['tags'] = [
                        t.strip().strip('"\'')
                        for t in value.split(',') if t.strip()
                    ]
            else:
                current[key] = value.strip('"\'')

    if current:
        conferences.append(current)

    return conferences


def fetch_conferences() -> list:
    """Fetch conference data from GitHub"""
    try:
        resp = requests.get(CONF_URL, timeout=15)
        if resp.status_code == 200:
            return parse_yaml_simple(resp.text)
    except Exception as e:
        print(f"Failed to fetch conferences: {e}")
    return []


def parse_deadline(deadline_str: str) -> datetime:
    """Parse deadline string to datetime"""
    try:
        # Format: "2025-06-05 23:59"
        return datetime.strptime(deadline_str.strip(), "%Y-%m-%d %H:%M")
    except:
        return None


def get_upcoming_deadlines() -> list:
    """Get conferences with upcoming deadlines"""
    conferences = fetch_conferences()
    now = datetime.now()
    cutoff = now + timedelta(days=DAYS_AHEAD)

    upcoming = []

    for conf in conferences:
        # Filter by tags
        conf_tags = [t.upper() for t in conf.get('tags', [])]
        if FILTER_TAGS:
            if not any(t in conf_tags for t in FILTER_TAGS):
                continue

        # Check deadlines
        deadlines = conf.get('deadlines', [])
        for dl_str in deadlines:
            dl = parse_deadline(dl_str)
            if dl and now < dl <= cutoff:
                days_left = (dl - now).days
                upcoming.append({
                    'name': conf.get('name', 'Unknown'),
                    'description': conf.get('description', ''),
                    'deadline': dl,
                    'deadline_str': dl_str,
                    'days_left': days_left,
                    'date': conf.get('date', ''),
                    'place': conf.get('place', ''),
                    'link': conf.get('link', ''),
                    'tags': conf_tags
                })

    # Sort by deadline
    upcoming.sort(key=lambda x: x['deadline'])
    return upcoming


def format_deadline_message() -> str:
    """Format upcoming deadlines as message"""
    upcoming = get_upcoming_deadlines()

    lines = [f"**Conference Deadlines** (next {DAYS_AHEAD} days)", ""]

    if not upcoming:
        lines.append("No upcoming deadlines")
        if FILTER_TAGS:
            lines.append(f"(Filter: {', '.join(FILTER_TAGS)})")
        return "\n".join(lines)

    for conf in upcoming[:10]:  # Max 10
        days = conf['days_left']
        if days == 0:
            urgency = "🔴 TODAY"
        elif days <= 3:
            urgency = f"🟠 {days}d"
        elif days <= 7:
            urgency = f"🟡 {days}d"
        else:
            urgency = f"🟢 {days}d"

        name = conf['name']
        dl_date = conf['deadline'].strftime("%m/%d")

        lines.append(f"• **{name}** - {dl_date} ({urgency})")
        if conf['description']:
            lines.append(f"  {conf['description'][:50]}")

    if len(upcoming) > 10:
        lines.append(f"... and {len(upcoming) - 10} more")

    return "\n".join(lines)


def run() -> str:
    """
    Get upcoming conference deadlines

    Returns:
        Formatted deadline message
    """
    print("=" * 50)
    print("Conference Deadlines")
    print("=" * 50)

    return format_deadline_message()
