import os
import requests
import feedparser

# 1. Keys - Secrets se aayengi
GEMINI_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_KEY") or ""
BLOGGER_TOKEN = os.environ.get("BLOGGER_ACCESS_TOKEN") or ""
BLOG_ID = os.environ.get("BLOG_ID") or ""
FB_PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID") or ""
FB_TOKEN = os.environ.get("FACEBOOK_ACCESS_TOKEN") or os.environ.get("FACEBOOK_PAGE_TOKEN") or ""

FEEDS = [
    "https://www.espncricinfo.com/rss/content/story/feeds/0.xml",
    "https://sports.ndtv.com/cricket/news?output=1",
    "https://www.cricbuzz.com/rss"
]

# 2. News lao
news_list = []
for url in FEEDS:
    try:
        f = feedparser.parse(url)
        for e in f.entries[:3]:
            title = getattr(e, 'title', '') or ""
            summary = getattr(e, 'summary', '') or getattr(e, 'description', '') or ""
            link = getattr(e, 'link', '') or ""
            if title:
                news_list.append({"title": title.strip(), "summary": summary.strip(), "link": link.strip()})
    except Exception as ex:
        print("Feed fail:", url, ex)

if not news_list:
    print("Koi news nahi mili")
    exit(0)

print(f"Total news mili: {len(news_list)}")

# 3. Last run check
try:
    last = open("last_run.txt").read().strip()
except:
    last = ""

for news in news_list:
    if news["title"] == last:
        print("Skip duplicate:", news["title"][:50])
        continue

    print("Processing:", news["title"][:80])

    # 4. Gemini se Urdu / Roman me rewrite - FAIL HO TO BHI RUKEGA NAHI
    prompt = f"Is cricket news ko GMM style me Roman Urdu me rewrite karo. Pehli line me catchy headline likho, phir 3-4 lines me tafseel likho. News: {news['title']} {news['summary'][:500]}"
    
    text = ""
    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}",
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=60
        )
        data = r.json()
        print("GEMINI RAW:", str(data)[:400])
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as ex:
        print("Gemini fail:", ex, "- fallback use kar raha hoon")
        text = ""

    # Agar Gemini ne jawab na diya, to original news hi use karo
    if not text or len(text.strip()) < 10:
        text = news["title"] + "\n" + news["title"] + ". Tafseel ke liye link dekhen."

    lines = text.strip().split("\n")
    headline = lines[0].replace("#", "").replace("*", "").strip()
    if not headline:
        headline = news["title"]
    body = "\n".join(lines[1:]).strip()
    if not body:
        body = news["title"]
    
    full_post = f"<h2>{headline}</h2><p>{body}</p><p><a href='{news['link']}'>Mukammal Khabar Parhen</a></p>"
    fb_post = f"{headline}\n\n{body}\n\nMukammal Khabar: {news['link']}"

    # 5. Blogger - Tumhari Website par
    try:
        b = requests.post(
            f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts/",
            params={"key": GEMINI_KEY},
            headers={"Authorization": f"Bearer {BLOGGER_TOKEN}", "Content-Type": "application/json"},
            json={"title": headline, "content": full_post},
            timeout=60
        )
        print("Blogger:", b.status_code)
    except Exception as ex:
        print("Blogger fail:", ex)

    # 6. Facebook Page par lagao
    try:
        fb = requests.post(
            f"https://graph.facebook.com/{FB_PAGE_ID}/feed",
            data={"message": fb_post, "access_token": FB_TOKEN},
            timeout=60
        )
        print("Facebook:", fb.status_code, str(fb.text)[:200])
    except Exception as ex:
        print("Facebook fail:", ex)

    # 7. Last save karo taake dobara wohi na lage
    try:
        open("last_run.txt", "w").write(news["title"])
    except:
        pass

    print("HO GAYA:", headline[:60])
    break

print("Bot khatam - sab done")
