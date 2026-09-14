# -*- coding: utf-8 -*-
"""שלב 1: איסוף ידיעות מפידי RSS, סינון לפי חלון זמן ולפי רלוונטיות לריצה."""
import re
import time
from datetime import datetime, timedelta, timezone

import feedparser

from config import SOURCES, HOURS_WINDOW, MAX_RAW_ITEMS, BLOCKED_DOMAINS


def _strip_html(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()


def _entry_time(entry):
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            return datetime.fromtimestamp(time.mktime(t), tz=timezone.utc)
    return None


def _entry_image(entry):
    """תמונת הכתבה עצמה מהפיד - צילום אמיתי מהמרוץ, לא סטוק גנרי."""
    # media:content - נבחר את הרחב ביותר (איכות גבוהה)
    best, best_w = None, -1
    for mc in (entry.get("media_content") or []):
        url = mc.get("url")
        typ = (mc.get("type") or "")
        if not url or (typ and not typ.startswith("image")):
            continue
        try:
            w = int(mc.get("width") or 0)
        except (TypeError, ValueError):
            w = 0
        if w >= best_w:
            best, best_w = url, w
    if best:
        return best
    for mt in (entry.get("media_thumbnail") or []):
        if mt.get("url"):
            return mt["url"]
    for enc in (entry.get("enclosures") or []):
        if (enc.get("type") or "").startswith("image") and enc.get("href"):
            return enc["href"]
    # גיבוי: <img> ראשון בגוף הידיעה
    blob = ""
    if entry.get("content"):
        blob = entry["content"][0].get("value", "")
    blob = blob or entry.get("summary") or ""
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', blob)
    return m.group(1) if m else None


def _full_text(entry):
    content = ""
    if entry.get("content"):
        content = entry["content"][0].get("value", "")
    return _strip_html(content or entry.get("summary") or "")


def fetch_all():
    cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_WINDOW)
    items = []
    for src in SOURCES:
        kept = 0
        try:
            d = feedparser.parse(src["feed"], agent="Mozilla/5.0 (running-news-agent)")
            for e in d.entries:
                ts = _entry_time(e)
                if ts is None or ts < cutoff:
                    continue

                link = e.get("link") or src["site"]
                if any(dom in link for dom in BLOCKED_DOMAINS):
                    continue  # אתרים שלנו - לא מצטטים את עצמנו

                title = (e.get("title") or "").strip()
                summary = _strip_html(e.get("summary") or "")[:600]

                # פיד רב-תחומי (למשל שוונג): רק ידיעות ריצה
                keys = src.get("include_keywords")
                if keys:
                    blob = f"{title} {summary}"
                    if not any(k in blob for k in keys):
                        continue

                item = {
                    "source_name": src["name"],
                    "title": title,
                    "summary": summary,
                    "url": link,
                    "published": ts.isoformat(),
                    "image": _entry_image(e),
                }
                # טקסט מורחב - נותן ל-Gemini חומר אמיתי לכתבה הראשית (תוצאות, זמנים, ציטוטים)
                details = _full_text(e)
                if len(details) > 200:
                    item["details"] = details[:2500]

                items.append(item)
                kept += 1
            print(f"[fetch] {src['name']}: {kept} רלוונטיות מתוך {len(d.entries)} בפיד")
        except Exception as ex:  # פיד בודד שנופל לא מפיל את הכל
            print(f"[fetch] שגיאה ב-{src['name']}: {ex}")

    items.sort(key=lambda x: x["published"], reverse=True)
    print(f"[fetch] סה\"כ {len(items)} ידיעות בחלון של {HOURS_WINDOW} שעות")
    return items[:MAX_RAW_ITEMS]
