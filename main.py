import urllib.request, xml.etree.ElementTree as ET

url = "https://news.google.com/rss/search?q=cricket&hl=ur&gl=PK&ceid=PK:ur"
data = urllib.request.urlopen(url).read()
root = ET.fromstring(data)
items = root.findall(".//item")[:15]

html = "<html><head><meta charset='utf-8'><title>GMM Cricket</title></head><body style='font-family:Arial;direction:rtl;text-align:right;padding:20px;background:#f2f2f2'>"
html += "<h1 style='text-align:center'>GMM Cricket - Taza Cricket Khabrain</h1>"

for it in items:
    title = it.findtext("title")
    link = it.findtext("link")
    desc = it.findtext("description") or ""
    html += f"<div style='background:white;padding:15px;margin:15px;border-radius:10px'><h2>{title}</h2><p>{desc}</p><a href='{link}' style='background:green;color:white;padding:8px 15px;border-radius:5px;text-decoration:none'>Mukamal Khabar Parhain</a></div>"

html += "<p style='text-align:center'>Auto Updated - GMM Cricket</p></body></html>"

open("index.html","w",encoding="utf-8").write(html)
print("Done")
