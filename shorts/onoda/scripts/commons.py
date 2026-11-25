import json, sys, subprocess, urllib.parse
def api(params):
    params.update(format="json")
    u = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    import time
    for i in range(5):
        out = subprocess.run(["curl", "-s", "-A", "ShortsPhotoResearch/1.0", u], capture_output=True, text=True).stdout
        try: return json.loads(out)
        except Exception: print("  retry:", out[:80].replace("\n"," ")); time.sleep(8*(i+1))
    return {}
import time
for q in sys.argv[1:]:
    time.sleep(3)
    r = api(dict(action="query", generator="search", gsrsearch=q, gsrnamespace=6, gsrlimit=10,
                 prop="imageinfo", iiprop="url|size|extmetadata"))
    print("##", q)
    for p in (r.get("query", {}).get("pages", {}) or {}).values():
        ii = p["imageinfo"][0]; md = ii.get("extmetadata", {})
        lic = md.get("LicenseShortName", {}).get("value", "?")
        dt = md.get("DateTimeOriginal", {}).get("value", "")[:40]
        print(f"  {p['title']} | {ii['width']}x{ii['height']} | {lic} | {dt}")
