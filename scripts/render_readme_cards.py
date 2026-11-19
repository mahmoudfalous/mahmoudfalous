#!/usr/bin/env python3
"""Render self-contained animated SVGs. STATIC=1 writes final frames to preview/cards/."""
import base64
from collections import defaultdict
import datetime as dt
import html
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = os.getenv('STATIC') == '1'
OUT = ROOT / ('preview/cards' if STATIC else 'cards')
OUT.mkdir(parents=True, exist_ok=True)
DATA = json.loads((ROOT / 'data/contributions.json').read_text())
DAYS = DATA['days']
BG, PANEL, BORDER, TEXT, MUTED, BLUE, MINT = '#0b1019', '#101927', '#263448', '#f2f6ff', '#96a9c2', '#75a7ff', '#89e4c2'

def esc(v):
    return html.escape(str(v))

def font_css():
    rules = []
    for family, filename, weight in [('Sans', 'sans.woff', 400), ('Sans', 'bold.woff', 700), ('Mono', 'mono.woff', 400)]:
        data = base64.b64encode((ROOT / 'fonts' / filename).read_bytes()).decode()
        rules.append(f"@font-face{{font-family:{family};font-weight:{weight};src:url(data:font/woff;base64,{data}) format('woff')}}")
    return ''.join(rules)

FONTS = font_css()
CSS = '''text{font-family:Sans,sans-serif;fill:#f2f6ff}.mono{font-family:Mono,monospace}.muted{fill:#96a9c2}.blue{fill:#75a7ff}.mint{fill:#89e4c2}.bold{font-weight:700}
@keyframes enter{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.35}}
@keyframes draw{from{stroke-dashoffset:440}to{stroke-dashoffset:0}}
.in{animation:enter .7s both;animation-delay:var(--delay,0s)}.bar{transform-box:fill-box;transform-origin:center bottom;animation:grow 1s both;animation-delay:var(--delay,0s)}.pulse{animation:blink 3s ease-in-out infinite}.orbit{stroke-dasharray:440;animation:draw 2s ease-out both}
@media(prefers-reduced-motion:reduce){*{animation:none!important;opacity:1!important;transform:none!important}}'''
if STATIC:
    CSS += '*{animation:none!important;opacity:1!important;transform:none!important}'

def text(x,y,value,size=14,cls='',extra=''):
    return f'<text x="{x}" y="{y}" font-size="{size}" class="{cls}" {extra}>{esc(value)}</text>'

def rect(x,y,w,h,fill,rx=0,extra=''):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" {extra}/>'

def save(name,h,body,w=900,description=''):
    title = name.replace('-', ' ').title()
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc"><title id="title">{esc(title)}</title><desc id="desc">{esc(description)}</desc><defs><style>{FONTS}{CSS}</style><linearGradient id="shine"><stop stop-color="#75a7ff"/><stop offset="1" stop-color="#89e4c2"/></linearGradient><pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse"><path d="M28 0H0V28" fill="none" stroke="#1b2b40" stroke-width=".7"/></pattern></defs>{rect(.5,.5,w-1,h-1,BG,18, f'stroke="{BORDER}"')}{body}</svg>'''
    (OUT / f'{name}.svg').write_text(svg)


def stats():
    total = sum(d['count'] for d in DAYS)
    active = sum(d['count'] > 0 for d in DAYS)
    longest = run = 0
    for day in DAYS:
        run = run + 1 if day['count'] else 0
        longest = max(longest, run)
    current = 0
    sample = DAYS[:-1] if DAYS[-1]['count'] == 0 else DAYS
    for day in reversed(sample):
        if not day['count']:
            break
        current += 1
    return total, active, longest, current

TOTAL, ACTIVE, LONGEST, CURRENT = stats()

# Hero: identity and the existing repository portrait.
b = rect(580,1,319,298,'url(#grid)',18)
b += '<g class="in">' + text(38,42,'MAHMOUD / SOFTWARE ENGINEER',12,'mono mint')
b += text(36,108,'Mahmoud',53,'bold') + text(36,168,'Mohamed.',53,'bold blue')
b += text(38,207,'Mobile & web developer at Stockastic',17)
b += text(38,238,'Production systems. Useful products. Open data.',13,'muted')
b += rect(38,261,8,8,MINT,4,'class="pulse"') + text(57,269,'@mahmoudfalous',12,'mono muted') + '</g>'
b += '<g class="in" style="--delay:.25s">'
photo = base64.b64encode((ROOT / 'assets/new.jpeg').read_bytes()).decode()
b += '<defs><clipPath id="portrait"><rect x="653" y="30" width="174" height="210" rx="20"/></clipPath></defs>'
b += f'<image x="653" y="30" width="174" height="210" preserveAspectRatio="xMidYMid slice" clip-path="url(#portrait)" href="data:image/jpeg;base64,{photo}"/>'
b += '<rect x="653" y="30" width="174" height="210" rx="20" fill="none" stroke="url(#shine)" stroke-width="2"/>' 
b += text(664,255,'CAIRO, EGYPT',12,'mono muted') + '</g>'
save('hero',300,b,description='Mahmoud Mohamed. Mobile and web developer at Stockastic. Cairo, Egypt.')

# Calendar, GitHub levels retained, counts are in accessible descriptions.
start, end = dt.date.fromisoformat(DATA['start']), dt.date.fromisoformat(DATA['end'])
origin = start - dt.timedelta(days=(start.weekday()+1)%7)
colors = ['#172436','#254370','#3766ad','#659cf1','#a8cbff']
b = text(30,35,'A YEAR OF BUILDING',12,'mono mint') + text(868,35,f'{start:%d %b %Y} - {end:%d %b %Y}',11,'mono muted','text-anchor="end"')
b += text(30,70,f'{TOTAL:,}',28,'bold') + text(147,69,'public-calendar contributions',13,'muted')
for day in DAYS:
    date = dt.date.fromisoformat(day['date'])
    offset = (date-origin).days
    x,y = 52+(offset//7)*15, 98+(offset%7)*15
    b += rect(x,y,11,11,colors[day['level']],2,f'class="in" style="--delay:{.3+(offset//7)*.012:.3f}s"')
    b += ''
for i,label in [(0,'S'),(2,'T'),(4,'T'),(6,'S')]:
    b += text(30,107+i*15,label,9,'mono muted')
b += text(30,225,'LESS',9,'mono muted')
for i,c in enumerate(colors): b += rect(68+i*14,216,10,10,c,2)
b += text(145,225,'MORE',9,'mono muted') + text(868,225,'All contribution types / not just commits',10,'muted','text-anchor="end"')
save('contributions',247,b,description=f'{TOTAL} public-calendar contributions over 365 days. Source: {DATA["source"]}.')

# Monthly bars, two edge months are explicitly partial.
months = defaultdict(int)
for day in DAYS: months[day['date'][:7]] += day['count']
maxval=max(months.values()) or 1
b=text(30,35,'THE RHYTHM',12,'mono mint') + text(30,64,'Consistency, month by month.',23,'bold')
b+=text(870,35,'365-DAY WINDOW / EDGE MONTHS PARTIAL',10,'mono muted','text-anchor="end"')
for i,(month,count) in enumerate(months.items()):
    x=35+i*64; height=max(3,94*count/maxval)
    b+=rect(x,186-height,40,height,BLUE if count==maxval else '#2d4667',5,f'class="bar" style="--delay:{.5+i*.045:.3f}s"')
    b+=text(x+20,176-height,count,10,'mono blue' if count==maxval else 'mono muted','text-anchor="middle"')
    date=dt.date.fromisoformat(month+'-01')
    b+=text(x+20,207,date.strftime('%b'),10,'mono muted','text-anchor="middle"')
    if i==0 or date.month==1: b+=text(x+20,221,date.year,8,'mono muted','text-anchor="middle"')
b+=f'<path d="M30 239H870" stroke="{BORDER}"/>'
best=max(DAYS,key=lambda d:d['count'])
for x,value,label in [(30,f'{ACTIVE} / 365','ACTIVE DAYS'),(255,f'{LONGEST} DAYS','LONGEST STREAK'),(480,f'{CURRENT} DAYS','CURRENT STREAK'),(705,str(best['count']),'BUSIEST DAY')]:
    b+=text(x,272,value,21,'bold')+text(x,293,label,10,'mono muted')
b+=text(705,313,dt.date.fromisoformat(best['date']).strftime('%d %b %Y'),9,'mono muted')
save('activity',330,b,description=f'{ACTIVE} active days, longest streak {LONGEST} days. Current streak {CURRENT} days, allowing today to be unfinished. Busiest date {best["date"]}: {best["count"]}.')

for name,num,title,lines,color in [
    ('apis','01','APIs & DATA',['Useful data,','ready to build on.'],BLUE),
    ('web','02','WEB PRODUCTS',['Small details.','Thoughtful experiences.'],MINT),
    ('tools','03','USEFUL TOOLS',['Practical software.','Less friction.'],'#e8c884')]:
    b=text(24,34,num,12,'mono muted')+text(259,35,'↗',21,'blue','text-anchor="end"')
    b+=f'<path d="M24 51H264" stroke="{color}" stroke-width="2"/>'
    b+=text(24,83,title,19,'bold')
    for i,line in enumerate(lines): b+=text(24,113+i*20,line,12,'muted')
    save(name,162,'<g class="in" style="--delay:.7s">'+b+'</g>',288, title+'. '+' '.join(lines))

repos = json.loads((ROOT / 'data/public-repos.json').read_text())
# The profile repository is presentation, not a project. Exclude forks.
projects = sorted([p for p in repos if not p['fork'] and p['name'].lower() != DATA['username'].lower()],
                  key=lambda p: (-p['stargazers_count'], p['name'].lower()))[:3]
blurbs = {
    'eg-drugs': '27K+ Egyptian medicines, reusable datasets and a public REST API.',
    'pixel-bouquet': 'Pixel-art bouquets and private letters. A personal web experience.',
    'wedding-invitation-': 'Customizable animated digital invitations for a special day.',
}
for old in OUT.glob('repo-*.svg'):
    old.unlink()
for project in projects:
    slug, count = project['name'], project['stargazers_count']
    title = slug.rstrip('-')
    desc = blurbs.get(slug, (project.get('description') or 'Explore the project on GitHub.')[:92])
    language = project.get('language') or 'OPEN SOURCE'
    b=text(30,31,'OPEN SOURCE / SELECTED BY STARS',10,'mono mint')
    b+=text(30,70,title,26,'bold')+text(30,102,desc,13,'muted')
    b+=rect(740,17,130,31,'#152740',9)
    b+=text(805,38,f'{count} STARS',13,'mono blue','text-anchor="middle"')
    b+=text(870,132,language.upper(),10,'mono muted','text-anchor="end"')
    save('repo-'+slug,151,'<g class="in" style="--delay:.9s">'+b+'</g>',description=f'{title}. {desc} {count} stars on GitHub.')

if not STATIC:
    readme = ROOT / 'README.md'
    content = readme.read_text()
    selected = '\n\n'.join(f'<a href="{esc(p["html_url"])}"><img src="./cards/repo-{esc(p["name"])}.svg" width="100%" alt="{esc(p["name"])}: {p["stargazers_count"]} GitHub stars" /></a>' for p in projects)
    content = re.sub(r'(?<=### Selected work)\s+.*?(?=\n<!-- Contact section -->)', '\n\n'+selected+'\n', content, flags=re.S)
    readme.write_text(content)

# Two independent linked contact cards keep click targets intact in GitHub Markdown.
for slug,kicker,title,detail in [
    ('contact-email','GET IN TOUCH','Email','mahmoudfalous@gmail.com'),
    ('contact-linkedin','KEEP IN TOUCH','LinkedIn','Connect with Mahmoud'),
]:
    b = text(26,30,kicker,10,'mono mint')
    b += text(26,68,title,25,'bold') + text(874,65,'↗',25,'blue','text-anchor="end"')
    b += text(26,99,detail,12,'muted')
    save(slug,125,b,description=title+'. '+detail)
b = text(26,27,'BUILT FROM REAL GITHUB ACTIVITY',10,'mono mint')
b += text(26,51,'Daily refresh  /  365-day window  /  Edge months partial  /  Reduced motion',11,'muted')
save('footer',73,b,description='Public GitHub activity. Daily refresh. Rolling 365-day window, edge months partial. Reduced motion supported.')

if STATIC:
    (OUT.parent / 'stats.json').write_text(json.dumps({'total':TOTAL,'active':ACTIVE,'longest':LONGEST,'current':CURRENT,'busiest':best,'months':dict(months)},indent=2))
print(f'Rendered {len(list(OUT.glob("*.svg")))} SVGs in {OUT}')
