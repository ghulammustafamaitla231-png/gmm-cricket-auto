import urllib.request, re, datetime, html as html_lib

def get_news():
    try:
        url = "https://www.espncricinfo.com/rss/content/story/feeds/6.xml"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = urllib.request.urlopen(req, timeout=25).read().decode('utf-8', errors='ignore')
        items = re.findall(r'<item>(.*?)</item>', data, re.DOTALL)
        news = []
        for item in items[:12]:
            t = re.search(r'<title>(.*?)</title>', item, re.DOTALL)
            l = re.search(r'<link>(.*?)</link>', item, re.DOTALL)
            d = re.search(r'<description>(.*?)</description>', item, re.DOTALL)
            if t:
                title = html_lib.unescape(re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', t.group(1).strip()))
                link = l.group(1).strip() if l else "https://gmmcricket.blogspot.com"
                desc = ""
                if d:
                    desc = html_lib.unescape(re.sub(r'<[^>]+>', '', re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', d.group(1).strip())))[:220]
                news.append((title, link, desc))
        return news
    except Exception as e:
        print("Error:", e)
        return []

news = get_news()
if not news:
    news = [("GMM Cricket - Latest Cricket News, Live Scores, PSL, IPL Updates", "https://gmmcricket.blogspot.com", "Stay tuned for latest cricket news.")]

cards = ""
for title, link, desc in news:
    cards += f"<div class='card'><h2><a href='{link}' target='_blank'>{html_lib.escape(title)}</a></h2><p>{html_lib.escape(desc)}</p><a class='btn' href='{link}' target='_blank'>Read Full News</a></div>"

now = datetime.datetime.now().strftime("%d %B %Y - %I:%M %p")
full_html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>GMM Cricket - Latest Cricket News, Live Scores</title><style>body{{font-family:Arial,sans-serif;background:#f2f2f2;margin:0;padding:0}}header{{background:#0b3d91;color:white;text-align:center;padding:20px}}header h1{{margin:0;font-size:32px}}header p{{margin:5px}} .top{{text-align:center;padding:12px;background:white}} .top a{{background:#25D366;color:white;padding:10px 18px;text-decoration:none;border-radius:20px;font-weight:bold}} .wrap{{max-width:800px;margin:15px auto;padding:0 12px}} .card{{background:white;padding:16px;margin-bottom:12px;border-radius:10px;box-shadow:0 2px 6px rgba(0,0,0,0.1)}} .card h2{{font-size:18px;margin:0 0 8px}} .card h2 a{{color:#111;text-decoration:none}} .card p{{color:#555;font-size:14px}} .btn{{display:inline-block;background:#0b3d91;color:white;padding:8px 14px;text-decoration:none;border-radius:6px;font-size:14px}} footer{{text-align:center;padding:15px;color:#777;font-size:13px}}</style></head>
<body><header><h1>GMM Cricket</h1><p>Latest Cricket News, Live Scores, PSL, IPL Updates</p><p>Updated: {now}</p></header>
<div class="top"><a href="https://gmmcricket.blogspot.com">Back to GMM Cricket Blogspot</a></div>
<div class="wrap">{cards}</div>
<footer>GMM Cricket | Auto Updated Every 30 Minutes | Powered by GitHub - Free - No Credit Card</footer></body></html>"""

open('index.html','w',encoding='utf-8').write(full_html)
print("Done - Total News:", len(news))
