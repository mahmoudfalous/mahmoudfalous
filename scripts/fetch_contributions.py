#!/usr/bin/env python3
"""Refresh the public GitHub calendar and public repo list.\n\nAuthenticates the REST API calls with the workflow token when one is\nprovided (public data only), so the shared Actions runner IP does not\nhit the unauthenticated rate limit.\n"""
import datetime as dt
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
USER = 'mahmoudfalous'
SOURCE = f'https://github.com/users/{USER}/contributions'
TOKEN = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')

class Calendar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells, self.counts, self.tip, self.text = {}, {}, None, []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'td' and 'data-date' in a:
            self.cells[a['id']] = {'date': a['data-date'], 'level': int(a['data-level'])}
        if tag == 'tool-tip':
            self.tip, self.text = a.get('for'), []
    def handle_data(self, data):
        if self.tip:
            self.text.append(data)
    def handle_endtag(self, tag):
        if tag == 'tool-tip' and self.tip:
            value = ''.join(self.text).strip()
            if value.startswith('No contributions'):
                self.counts[self.tip] = 0
            else:
                m = re.match(r'([\d,]+) contribution', value)
                if m:
                    self.counts[self.tip] = int(m.group(1).replace(',', ''))
            self.tip = None


def fetch_json(url):
    headers = {'User-Agent': 'mahmoudfalous-profile-cards'}
    if TOKEN:
        headers['Authorization'] = f'Bearer {TOKEN}'
    for attempt in range(4):
        try:
            with urlopen(Request(url, headers=headers), timeout=45) as response:
                return json.load(response)
        except HTTPError as e:
            if e.code in (403, 429) and attempt < 3:
                time.sleep(15 * (attempt + 1))
                continue
            raise

def main():
    req = Request(SOURCE, headers={'User-Agent': 'mahmoudfalous-profile-cards'})
    with urlopen(req, timeout=45) as response:
        raw = response.read().decode('utf-8')
    parser = Calendar()
    parser.feed(raw)
    if len(parser.cells) < 350 or any(k not in parser.counts for k in parser.cells):
        raise RuntimeError('GitHub calendar format changed or response incomplete. Keeping previous cards.')
    end = max(dt.date.fromisoformat(v['date']) for v in parser.cells.values())
    start = end - dt.timedelta(days=364)
    days = sorted([dict(v, count=parser.counts[k]) for k, v in parser.cells.items()
                   if start <= dt.date.fromisoformat(v['date']) <= end], key=lambda d: d['date'])
    if len(days) != 365 or len({d['date'] for d in days}) != 365:
        raise RuntimeError('Expected 365 distinct calendar days')
    payload = {'username': USER, 'source': SOURCE, 'fetched_at': dt.datetime.now(dt.timezone.utc).isoformat(),
               'start': str(start), 'end': str(end), 'days': days}
    target = ROOT / 'data/contributions.json'
    target.parent.mkdir(exist_ok=True)
    tmp = target.with_suffix('.tmp')
    tmp.write_text(json.dumps(payload, indent=2) + '\n')
    tmp.replace(target)
    repos = []
    for page in range(1, 11):
        url = f'https://api.github.com/users/{USER}/repos?type=owner&per_page=100&page={page}'
        batch = fetch_json(url)
        repos.extend(batch)
        if len(batch) < 100:
            break
    else:
        raise RuntimeError('Repository pagination incomplete')
    (ROOT / 'data/public-repos.json').write_text(json.dumps(repos, indent=2) + '\n')
    print(f'Refreshed {len(days)} public calendar days; total {sum(d["count"] for d in days):,}')

if __name__ == '__main__':
    main()
