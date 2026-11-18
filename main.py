import os, requests, feedparser, json, time
from datetime import datetime

GEMINI = os.environ.get("GEMINI_API_KEY", "")
BLOG_ID = os.environ.get("BLOGGER_BLOG_ID", "")
BLOGGER_TOKEN = os.environ.get("BLOGGER_TOKEN", "")
FB_PAGE = os.environ.get("FB_PAGE_ID", "")
FB_TOKEN = os.environ.get("FB_TOKEN", "")

print("GEMINI:", "OK" if GEMINI else "MISSING")
print("BLOG_ID:", "***" if BLOG_ID else "MISSING")
print("BLOGGER:", "OK" if BLOGGER_TOKEN else "MISSING")
print("FB_PAGE:", "OK" if FB_PAGE else "MISSING")
print("FB_TOKEN:", "OK" if FB_TOKEN else "MISSING")

if not all([GEMINI, BLOG_ID, BLOGGER_TOKEN, FB_PAGE, FB_TOKEN]):
    print("ERROR: 5 me se koi chabi missing hai")
    exit(1)

# 1. Cricket News lao - GMM Cricket ke liye
FEEDS = [
    "https://www.espncricinfo.com/rss/content/story/feeds/0.xml",
    "https://sports.ndtv.com/cricket/news/rss",
    "https://www.cricbuzz.com/rss"
]

news_list = []
for url in FEEDS:
    try:
        f = feedparser.parse(url)
        for e in f.entries[:3]:
            news_list.append({"title": e.title, "link": e.link, "summary": getattr(e, 'summary', '')[:800]})
    except Exception as ex:
        print("Feed fail:", url, ex)

if not news_list:
    print("Koi news nahi mili")
    exit(0)

# Last run check - taake dobara wohi khabar na lage
try:
    last = open("last_run.txt").read().strip()
except:
    last = ""

for news in news_list:
    if news["title"] == last:
        continue

    # 2. Gemini se Urdu / Roman me rewrite karwao
    prompt = f"Is cricket news ko GMM Cricket ke liye 300 lafzon ki asaan Urdu (Roman) me khabar banao, dilchasp headline ke sath. News: {news['title']} - {news['summary']}"
    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI}",
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=60
        )
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as ex:
        print("Gemini fail:", ex)
        continue

    lines = text.strip().split("\n")
    headline = lines[0].replace("#", "").strip()
    body = "\n".join(lines[1:]).strip()
    full_post = f"<h2>{headline}</h2><p>{body}</p><p><br>Source: GMM Cricket - Sadasi</p><p> mazeed cricket khabron ke liye hamari website visit karen.</p>"

    # 3. Blogger - Tumhari Website par lagao
    try:
        b = requests.post(
            f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts/?access_token={BLOGGER_TOKEN}",
            json={"title": headline, "content": full_post},
            timeout=60
        )
        print("Blogger:", b.status_code)
    except Exception as ex:
        print("Blogger fail:", ex)

    # 4. Facebook Page par lagao
    try:
        fb = requests.post(
            f"https://graph.facebook.com/{FB_PAGE}/feed",
            data={"message": f"{headline}\n\n{body}\n\nPoori khabar parhen: GMM Cricket", "access_token": FB_TOKEN},
            timeout=60
        )
        print("Facebook:", fb.status_code)
    except Exception as ex:
        print("Facebook fail:", ex)

    open("last_run.txt", "w").write(news["title"])
    print("HO GAYA:", headline)
    break
