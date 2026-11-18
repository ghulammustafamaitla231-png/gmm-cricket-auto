import os
import requests
import feedparser
import re
from datetime import datetime

# ===== 1. تمہاری 5 چابیاں - 100% تمہارے ناموں سے =====
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
BLOGGER_TOKEN = os.environ.get("BLOGGER_TOKEN", "").strip()
BLOG_ID = os.environ.get("BLOGGER_BLOG_ID", "").strip()
FB_PAGE_ID = os.environ.get("FB_PAGE_ID", "").strip()
FB_TOKEN = os.environ.get("FB_TOKEN", "").strip()

print("Keys check:", "GEMINI:", bool(GEMINI_KEY), "BLOGGER:", bool(BLOGGER_TOKEN), "BLOG_ID:", bool(BLOG_ID), "FB_ID:", bool(FB_PAGE_ID), "FB_TOKEN:", bool(FB_TOKEN))

# ===== 2. خبریں کہاں سے لینی ہیں =====
# یہاں کمپنی کا نام آئے گا - ESPNcricinfo
RSS_URLS = [
    "https://www.espncricinfo.com/rss/content/story/feeds/0.xml",
    "https://www.cricbuzz.com/rssfeed/cricket/news",
]

def get_latest_news():
    for url in RSS_URLS:
        try:
            feed = feedparser.parse(url)
            if feed.entries:
                e = feed.entries[0]
                title = e.title
                link = e.link
                # تصویر نکالنا
                image_url = ""
                if "media_content" in e and e.media_content:
                    image_url = e.media_content[0].get("url", "")
                elif "media_thumbnail" in e and e.media_thumbnail:
                    image_url = e.media_thumbnail[0].get("url", "")
                # اگر تصویر میں _w_ چھوٹی ہے تو بڑی کر دو
                if image_url:
                    image_url = image_url.replace("w=100", "w=800").replace("width=100", "width=800")
                
                summary = e.get("summary", "")[:1500]
                source_name = "ESPNcricinfo" if "espn" in url else "Cricbuzz"
                return title, link, summary, image_url, source_name
        except Exception as ex:
            print("RSS fail:", url, ex)
            continue
    return None, None, None, None, None

def rewrite_with_gemini(title, summary, source_name):
    prompt = f"""
    Tum ek Urdu cricket journalist ho.
    Is English khabar ko apni zaban me 100% naye alfaz me, mukammal tafseel ke sath Urdu me likho.
    Copy paste mat karna, AI apni zaban me likhe.
    Heading, phir 4-5 paragraph, phir akhir me players ke naam.
    Original Title: {title}
    Original Summary: {summary}
    Sirf Urdu me jawab do.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    r = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
    print("Gemini status:", r.status_code)
    data = r.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except:
        print("Gemini error:", r.text[:500])
        return f"{title}\n\n{summary}"

def post_to_blogger(title, full_text_urdu, image_url, source_name, original_link):
    # حوالہ + تصویر + پوری خبر
    html = f"""
    <div style="font-family: sans-serif; direction: rtl; text-align: right;">
    <img src="{image_url}" style="width:100%; border-radius:10px;" />
    <h1>{title}</h1>
    <p>{full_text_urdu.replace(chr(10), '<br><br>')}</p>
    <hr>
    <p style="background:#f0f0f0; padding:10px; border-radius:8px;">
    <b>حوالہ / Source:</b> یہ خبر <b>{source_name}</b> سے لی گئی ہے۔ ہماری ٹیم نے اس خبر کو AI کی مدد سے اپنی زبان میں دوبارہ لکھ کر آپ تک پہنچایا ہے۔ اصل خبر یہاں پڑھیں: <a href="{original_link}">Original News</a><br>
    <b>نوٹ:</b> یہ خبر AI نے {source_name} کے حوالے سے اپنی زبان میں ویب سائٹ کے لیے تیار کی ہے، اور یہی خبر ہمارے فیس بک پیج پر بھی شائع کی گئی ہے۔
    </p>
    </div>
    """
    url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts/"
    headers = {"Authorization": f"Bearer {BLOGGER_TOKEN}", "Content-Type": "application/json"}
    payload = {"kind": "blogger#post", "blog": {"id": BLOG_ID}, "title": title, "content": html}
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    print("Blogger status:", r.status_code, r.text[:500])
    if r.status_code in [200, 201]:
        return r.json().get("url", "")
    return ""

def post_to_facebook(title, full_text_urdu, image_url, blog_url, source_name, original_link):
    # فیس بک پر وہی تصویر + وہی پوری خبر + حوالہ
    caption = f"""{title}

{full_text_urdu}

---
حوالہ: یہ خبر {source_name} سے لی گئی ہے، AI نے اپنی زبان میں لکھ کر ہماری ویب سائٹ پر لگائی ہے اور وہی خبر یہاں فیس بک پیج پر بھی شائع کی جا رہی ہے۔
اصل خبر: {original_link}
ہماری ویب سائٹ پر مکمل خبر پڑھیں: {blog_url}
#GMM #Cricket #CricketNews
"""
    # 1. پہلے تصویر اپلوڈ کرو
    if image_url:
        img_data = requests.get(image_url, timeout=30).content
        url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
        files = {"source": ("image.jpg", img_data)}
        data = {"caption": caption, "access_token": FB_TOKEN}
        r = requests.post(url, files=files, data=data, timeout=90)
        print("FB Photo status:", r.status_code, r.text[:500])
        if r.status_code == 200:
            return True
    # اگر تصویر فیل ہو جائے تو صرف ٹیکسٹ پوسٹ کر دو
    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed"
    r = requests.post(url, data={"message": caption, "link": blog_url, "access_token": FB_TOKEN}, timeout=60)
    print("FB Text status:", r.status_code, r.text[:500])
    return r.status_code == 200

def main():
    title, link, summary, image_url, source_name = get_latest_news()
    if not title:
        print("Koi khabar nahi mili")
        return
    print("News mili:", title, "Source:", source_name, "Image:", image_url)
    urdu_text = rewrite_with_gemini(title, summary, source_name)
    blog_url = post_to_blogger(title, urdu_text, image_url, source_name, link)
    print("Blog URL:", blog_url)
    ok = post_to_facebook(title, urdu_text, image_url, blog_url, source_name, link)
    print("Facebook done:", ok)

if __name__ == "__main__":
    main()
