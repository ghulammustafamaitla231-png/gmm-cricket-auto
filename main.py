import urllib.request, re, datetime, html as html_lib, json, os, requests

def get_news():
    try:
        url = "https://www.espncricinfo.com/rss/content/story/feeds/6.xml"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = urllib.request.urlopen(req, timeout=20).read().decode('utf-8', 'ignore')
        items = re.findall(r'<item>(.*?)</item>', data, re.DOTALL)
        news = []
        for item in items[:12]:
            t = re.search(r'<title>(.*?)</title>', item, re.DOTALL)
            l = re.search(r'<link>(.*?)</link>', item, re.DOTALL)
            d = re.search(r'<description>(.*?)</description>', item, re.DOTALL)
            img = re.search(r'media:content[^>]*url="([^"]+)"', item)
            if not img:
                img = re.search(r'<enclosure[^>]*url="([^"]+)"', item)
            if not img:
                img = re.search(r'https://[^"\s<>]+\.(jpg|jpeg|png|webp)', item)
            if t:
                title = html_lib.unescape(t.group(1).strip())
                link = l.group(1).strip() if l else ""
                desc = ""
                if d:
                    desc = html_lib.unescape(re.sub('<[^<]+?>', '', d.group(1))).strip()[:300]
                image = img.group(1) if img else ""
                news.append((title, link, desc, image))
        return news
    except Exception as e:
        print("Error:", e)
        return []

def post_to_blogger(title, link, desc, image):
    blog_id = os.environ.get("BLOGGER_BLOG_ID")
    token = os.environ.get("BLOGGER_TOKEN")
    if not blog_id or not token:
        return False
    url = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts/"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    img_html = f'<img src="{image}" style="width:100%;border-radius:10px;" />' if image else ""
    html = f'<div>{img_html}<p>{desc}</p><p><a href="{link}">مزید پڑھیں</a></p></div>'
    r = requests.post(url, headers=headers, json={"title": title, "content": html})
    print("Blogger:", r.status_code)
    return r.status_code == 200

def post_to_facebook(title, link, desc, image):
    page_id = os.environ.get("FB_PAGE_ID")
    token = os.environ.get("FB_TOKEN")
    if not page_id or not token or not image:
        return
    url = f"https://graph.facebook.com/v18.0/{page_id}/photos"
    data = {"url": image, "caption": f"{title}\n\n{desc}\n\nمزید پڑھیں: {link}", "access_token": token}
    r = requests.post(url, data=data)
    print("Facebook:", r.status_code)

def main():
    news = get_news()
    print(f"Found: {len(news)}")
    # blog.html بھی بناؤ تاکہ ویب سائٹ بھی چلتی رہے
    html_page = "<html><head><meta charset='utf-8'><title>GMM Cricket</title></head><body><h1>GMM Cricket - Latest News</h1>"
    for title, link, desc, image in news:
        img_html = f'<br><img src="{image}" style="width:100%;max-width:600px;border-radius:10px;">' if image else ""
        html_page += f"<div style='border:1px solid #ddd;padding:15px;margin:10px;border-radius:10px;'><h2>{title}</h2>{img_html}<p>{desc}</p><a href='{link}'>مزید پڑھیں</a></div>"
        post_to_blogger(title, link, desc, image)
        post_to_facebook(title, link, desc, image)
    html_page += f"<p>Last Updated: {datetime.datetime.now()}</p></body></html>"
    with open("blog.html", "w", encoding="utf-8") as f:
        f.write(html_page)
    with open("last_run.txt", "w") as f:
        f.write(str(datetime.datetime.now()))

if __name__ == "__main__":
    main()
