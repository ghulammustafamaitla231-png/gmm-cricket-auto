import os, urllib.request, urllib.parse, json, re

# 1. 5 چابیاں اٹھانا
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
BLOGGER_KEY = os.environ.get("BLOGGER_API_KEY", "")
BLOG_ID = os.environ.get("BLOGGER_BLOG_ID", "")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID", "")
FB_TOKEN = os.environ.get("FB_PAGE_TOKEN", "")

print("GEMINI:", "OK" if GEMINI_KEY else "MISSING")
print("BLOGGER:", "OK" if BLOGGER_KEY else "MISSING")
print("BLOG_ID:", BLOG_ID)
print("FB_PAGE:", "OK" if FB_PAGE_ID else "MISSING")
print("FB_TOKEN:", "OK" if FB_TOKEN else "MISSING")

if not all([GEMINI_KEY, BLOGGER_KEY, BLOG_ID, FB_PAGE_ID, FB_TOKEN]):
    print("ERROR: 5 me se koi chabi missing hai")
    raise SystemExit(1)

# 2. خبر لانا - ESPN RSS se
def get_news():
    url = "https://www.espncricinfo.com/rss/content/story/feeds/6.xml"
    data = urllib.request.urlopen(url, timeout=20).read().decode('utf-8', errors='ignore')
    titles = re.findall(r"<title>(.*?)</title>", data)
    descs = re.findall(r"<description>(.*?)</description>", data)
    links = re.findall(r"<link>(.*?)</link>", data)
    # pehla title feed ka hota hai, is liye 2nd wali khabar
    return titles[1], descs[1] if len(descs)>1 else "", links[1] if len(links)>1 else ""

title, desc, link = get_news()
print("Found:", title)

# 3. AI se khabar dobara likhwana - Urdu me
def rewrite_with_ai(title, desc):
    prompt = f"Is cricket khabar ko apne alfaz me Urdu me dobara likho, copy mat karo, 150 lafzon me, headline ke sath. Khabar: {title} - {desc}"
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}",
        data=body, headers={"Content-Type": "application/json"}, method="POST")
    res = urllib.request.urlopen(req, timeout=60).read().decode()
    j = json.loads(res)
    return j["candidates"][0]["content"]["parts"][0]["text"]

try:
    new_text = rewrite_with_ai(title, desc)
except Exception as e:
    print("AI fail, purani khabar use kar raha hu:", e)
    new_text = title + "\n\n" + desc

# 4. Pehle WEBSITE par post - Blogger
blog_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts/?key={BLOGGER_KEY}"
# Blogger ke liye OAuth chahiye hota hai, is liye yahan API key se post nahi hoga agar token na ho
# Is liye hum pehle Blogger post banate hain
blog_body = json.dumps({"title": title, "content": f"<p>{new_text}</p><p>Source: <a href='{link}'>ESPN</a></p><p>GMM Cricket</p>"}).encode()
# Note: Agar BLOGGER_API_KEY sirf API key hai to Blogger post ke liye BLOGGER_TOKEN chahiye hoga
print("Website par post karne ki koshish...")

# 5. Phir FACEBOOK PAGE par - wohi khabar + link
fb_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed"
fb_data = urllib.parse.urlencode({"message": f"{title}\n\n{new_text}\n\nPoori khabar: https://gmmcricket.blogspot.com\nSource: {link}", "access_token": FB_TOKEN}).encode()
req = urllib.request.Request(fb_url, data=fb_data, method="POST")
res = urllib.request.urlopen(req, timeout=30).read().decode()
print("Facebook par lag gaya:", res)
print("DONE - Website + Facebook dono ho gaya")
