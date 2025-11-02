# services/scraping.py

import requests
from bs4 import BeautifulSoup

AMAZON_TAG = "smartquotr08-20"

# 🔁 Format: list of dicts with name + url for easy tabbed rendering
def wrap_named_links(query, links):
    return [{"name": query, "url": link} for link in links]

def scrape_amazon_links(query):
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://www.amazon.com/s?k={requests.utils.quote(query)}"
    try:
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")
        links = []
        for a in soup.select("a[href*='/dp/']")[:3]:
            href = a.get("href")
            if href and "/dp/" in href:
                clean = href.split("?")[0]
                full_link = f"https://www.amazon.com{clean}?tag={AMAZON_TAG}"
                links.append(full_link)
        return wrap_named_links(query, links or [f"{url}&tag={AMAZON_TAG}"])
    except:
        return wrap_named_links(query, [f"{url}&tag={AMAZON_TAG}"])

# def scrape_carparts_links(query):
#    headers = {"User-Agent": "Mozilla/5.0"}
#    url = f"https://www.carparts.com/search?q={requests.utils.quote(query)}"
#    try:
#        res = requests.get(url, headers=headers, timeout=5)
#        soup = BeautifulSoup(res.text, "html.parser")
#        links = []
#
#        # CarParts.com products have anchor tags with hrefs like `/details/...`
#       for a in soup.select("a[href^='/details/']")[:3]:
#            href = a.get("href")
#           if href:
#                full_link = f"https://www.carparts.com{href.split('?')[0]}"
#                links.append(full_link)
#
#        return wrap_named_links(query, links or [url])
#    except Exception as e:
#        print(f"⚠️ CarParts scrape failed for '{query}':", e)
#        return wrap_named_links(query, [url])

# def scrape_homedepot_links(query):
#    return wrap_named_links(query, [f"https://www.homedepot.com/s/{requests.utils.quote(query)}"])

# def scrape_tonkinautoparts_links(query):
#     headers = {"User-Agent": "Mozilla/5.0"}
#     url = f"https://www.tonkinautoparts.com/search?q={requests.utils.quote(query)}"
#     try:
#         res = requests.get(url, headers=headers, timeout=5)
#         soup = BeautifulSoup(res.text, "html.parser")
#         links = []
        # Product links: usually under /oem-parts/ or /product/
#         for a in soup.select("a[href^='/oem-parts/'], a[href^='/product/']")[:3]:
#             href = a.get("href")
#             if href:
#                 full_link = f"https://www.tonkinautoparts.com{href.split('?')[0]}"
#                 product_name = a.get_text(strip=True)
#                 if not product_name:
#                     product_name = a.get("title", query).strip()
#                 links.append({"name": product_name or query, "url": full_link})
#         return links or wrap_named_links(query, [url])
#     except Exception as e:
#         print(f"⚠️ TonkinAutoParts scrape failed for '{query}':", e)
#         return wrap_named_links(query, [url])


def scrape_walmart_links(query):
    return wrap_named_links(query, [f"https://www.walmart.com/search?q={requests.utils.quote(query)}"])

# def scrape_temu_links(query):
    slug = requests.utils.quote(query.lower().replace(" ", "-"))
    url = f"https://www.temu.com/keyword-{slug}.html"
#    return wrap_named_links(query, [url])

# def scrape_bestbuy_links(query):
    url = f"https://www.bestbuy.com/site/searchpage.jsp?st={requests.utils.quote(query)}"
#    return wrap_named_links(query, [url])

def scrape_harborfreight_links(query):
    url = f"https://www.harborfreight.com/search?q={requests.utils.quote(query)}"
    return wrap_named_links(query, [url])



def scrape_autozone_links(query):
    return wrap_named_links(query, [f"https://www.autozone.com/searchresult?searchText={requests.utils.quote(query)}"])

# def scrape_oreilly_links(query):
#    return wrap_named_links(query, [f"https://www.oreillyauto.com/search?q={requests.utils.quote(query)}"])

# def scrape_napa_links(query):
#    return wrap_named_links(query, [f"https://www.napaonline.com/en/search?text={requests.utils.quote(query)}"])


def scrape_all_links(advice, project_type, keywords_override=None):
    import re
    # from .scraping import (
    #    scrape_amazon_links, 
    #    scrape_walmart_links,
    #    scrape_harborfreight_links,  
    #    scrape_autozone_links,
    #    wrap_named_links
    # )

    # 🧠 Use override if provided, else parse from advice text
    if keywords_override:
        keywords = list(dict.fromkeys([k.strip().title() for k in keywords_override]))
    else:
        keywords = []
        for line in advice.splitlines():
            match = re.search(r"-\s*\[?\s*]?\s*(.+?)[:(]", line)
            if match:
                kw = match.group(1).strip()
                if len(kw) > 2:
                    cleaned = kw.replace("[", "").replace("]", "").strip()
                    keywords.append(cleaned)
        keywords = list(dict.fromkeys([k.strip().title() for k in keywords])) or ["Screwdriver", "Sealant"]



    # Smart wrapper for fallback
    def safe(scrape_func, query):
        try:
            links = scrape_func(query)
            return links if links else wrap_named_links(query, [f"https://www.google.com/search?q={requests.utils.quote(query)}"])
        except:
            return wrap_named_links(query, [f"https://www.google.com/search?q={requests.utils.quote(query)}"])

    # 🔧 Tabbed/Sectioned dictionary output
    all_links = {
        "amazon_links": [],
        # "homedepot_links": [],
        "walmart_links": [],
        # "temu_links": [],
        # "bestbuy_links": [],       
        "harborfreight_links": [],
        "autozone_links": [],
        # "oreilly_links": [],
        # "napa_links": [],
        # "carparts_links": [],
        # "tonkinautoparts_links": [],
    }

    for kw in keywords:
        all_links["amazon_links"] += safe(scrape_amazon_links, kw)
        # all_links["homedepot_links"] += safe(scrape_homedepot_links, kw)
        all_links["walmart_links"] += safe(scrape_walmart_links, kw)
        # all_links["temu_links"] += safe(scrape_temu_links, kw)
        # all_links["bestbuy_links"] += safe(scrape_bestbuy_links, kw)
        all_links["harborfreight_links"] += safe(scrape_harborfreight_links, kw)
        


        if "auto" in project_type.lower():
            all_links["autozone_links"] += safe(scrape_autozone_links, kw)
            # all_links["oreilly_links"] += safe(scrape_oreilly_links, kw)
            # all_links["napa_links"] += safe(scrape_napa_links, kw)
            # all_links["carparts_links"] += safe(scrape_carparts_links, kw)
            # all_links["tonkinautoparts_links"] += safe(scrape_tonkinautoparts_links, kw)
    return all_links
