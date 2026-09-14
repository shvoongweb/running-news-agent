# -*- coding: utf-8 -*-
"""בדיקה מקומית ללא רשת: מוודאת שהסינון, בניית ה-HTML והרכבת הודעת הטלגרם עובדים.
הרצה: python3 tests/test_pipeline.py
"""
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from build_html import build_page, build_html  # noqa: E402
import telegram_post  # noqa: E402

FEATURE = {
    "title_he": "עומר דורי בן ה-18 סיים איירונמן טאלין מתחת לעשר שעות",
    "lead_he": "בין בגרויות לאיש ברזל: הצעיר הישראלי חצה את קו הסיום אחרי 9:52 שעות בתנאי מזג אוויר קשים, והפך לאחד הישראלים הצעירים שהשלימו את המרחק המלא.",
    "body_he": "הזינוק נדחה בחצי שעה בגלל גשם, והשחייה קוצרה.\n\nבמקטע הריצה דורי שמר על קצב יציב של 5:10 לקילומטר עד הקילומטר ה-30.",
    "key_facts_he": ["9:52 - זמן הסיום", "42.2 ק\"מ בקצב 5:10 לק\"מ", "גיל 18"],
    "why_it_matters_he": "דור צעיר של טריאתלטים ישראלים מגיע למרחק המלא מוקדם מאי פעם.",
    "image_keyword": "Ironman Tallinn triathlon",
    "source_name": "RUNPANEL",
    "source_url": "https://runpanel.co.il/example",
}

STORIES = [
    {"title_he": "מוריס הריוט, מדליסט הכסף האולימפי, הלך לעולמו בגיל 86",
     "paragraph_he": "הריוט, שזכה בכסף במכשולים באולימפיאדת טוקיו 1964, נפטר השבוע.",
     "source_name": "Athletics Weekly", "source_url": "https://athleticsweekly.com/x"},
    {"title_he": "רות קרופט פורשת מ-UTMB",
     "paragraph_he": "האלופה המכהנת הודיעה על פרישה מהמרוץ ימים ספורים לפני הזינוק.",
     "source_name": "Canadian Running", "source_url": "https://runningmagazine.ca/x"},
    {"title_he": "רשימת המשתתפים המלאה לדיימונד ליג בציריך",
     "paragraph_he": "המפגש האחרון של העונה יארח את מיטב האתלטים.",
     "source_name": "Athletics Illustrated", "source_url": "https://www.athleticsillustrated.com/x"},
    {"title_he": "גרמין השיקה בישראל את סדרת fenix 9",
     "paragraph_he": "השעון החדש מגיע עם קישוריות לוויינית ומארז טיטניום.",
     "source_name": "RUNPANEL", "source_url": "https://runpanel.co.il/y"},
]


def test_filter():
    """סינון פיד ספורט כללי לידיעות ריצה בלבד + חסימת האתרים שלנו."""
    from config import SOURCES, BLOCKED_DOMAINS
    keys = next(s for s in SOURCES if s["name"] == "ynet ספורט")["include_keywords"]
    running = ["לונה צ'מטאי סלפטר שברה את שיא ישראל במרתון",
               "אלפים השתתפו במרוץ הלילה בתל אביב",
               "אליפות ישראל באתלטיקה נפתחה בחיפה"]
    other = ["רונאלדו הוחלף במחצית וירד עצבני, אל נאסר ניצחה",
             "תסריט הבלהות של הפועל באר-שבע | טור",
             "עולם השחייה בטירוף: ליגת ה-ISL חוזרת ללונדון"]
    for t in running:
        assert any(k in t for k in keys), f"ידיעת ריצה נפסלה בטעות: {t}"
    for t in other:
        assert not any(k in t for k in keys), f"ידיעה לא רלוונטית עברה את הסינון: {t}"

    assert "shvoong.co.il" in BLOCKED_DOMAINS
    assert not any("shvoong.co.il" in s["feed"] for s in SOURCES), "שוונג עדיין מופיע במקורות"
    print(f"✓ סינון ynet עובד ({len(running)} עברו, {len(other)} נחסמו) · שוונג חסום")


def test_fetch_blocks_own_site():
    """fetch_all: פריט שמצביע לדומיין חסום לא נאסף, גם אם הגיע מפיד לגיטימי."""
    import time
    import fetch_news
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).timetuple()

    class _Feed:
        def __init__(self, entries):
            self.entries = entries

    def entry(title, link):
        return {"title": title, "link": link, "summary": "טקסט קצר",
                "published_parsed": now, "media_content": [], "media_thumbnail": [],
                "enclosures": [], "content": []}

    def fake_parse(url, agent=None):
        return _Feed([
            entry("שיא ישראלי חדש במרתון", "https://runpanel.co.il/post-1"),
            entry("סיכום מרוץ הלילה", "https://shvoong.co.il/post-2"),  # האתר שלנו
        ])

    original = fetch_news.feedparser.parse
    fetch_news.feedparser.parse = fake_parse
    try:
        items = fetch_news.fetch_all()
    finally:
        fetch_news.feedparser.parse = original

    urls = [i["url"] for i in items]
    assert urls, "לא נאספו ידיעות כלל"
    assert not any("shvoong.co.il" in u for u in urls), "ידיעה משוונג נאספה"
    print(f"✓ fetch_all חסם את shvoong.co.il ({len(items)} ידיעות נאספו)")


def test_html():
    page = build_page(FEATURE, STORIES, "26.08.2026",
                      "https://example.com/hero.jpg", "צילום: RUNPANEL")
    for must in (FEATURE["title_he"], FEATURE["lead_he"], "עובדות המפתח",
                 "למה זה חשוב", "שאר ההיליטים של עולם הריצה", STORIES[-1]["title_he"]):
        assert must in page, f"חסר בכתבה: {must}"
    assert 'dir="rtl"' in page and "<script" not in page
    path, date_str = build_html(FEATURE, STORIES, "https://example.com/hero.jpg", "צילום: RUNPANEL")
    assert os.path.exists(path) and os.path.exists("docs/index.html")
    assert os.path.exists("docs/archive.html")
    print(f"✓ HTML נבנה: {path} ({date_str}, {len(page):,} תווים)")
    return path


def test_telegram(html_path):
    """הרכבת ההודעות בלי לשלוח - מחליפים את requests.post במוק."""
    sent = []

    class _Resp:
        def raise_for_status(self):
            pass

    def fake_post(url, **kw):
        sent.append((url.rsplit("/", 1)[-1], kw))
        return _Resp()

    telegram_post.requests = types.SimpleNamespace(post=fake_post)
    os.environ["TELEGRAM_BOT_TOKEN"] = "t"
    os.environ["TELEGRAM_CHAT_ID"] = "c"
    os.environ["GITHUB_REPOSITORY"] = "shvoongweb/running-news-agent"

    telegram_post.post_to_telegram(FEATURE, STORIES, "26.08.2026", html_path,
                                   b"x" * 20000, "race-photo.jpg", "צילום: RUNPANEL")
    methods = [m for m, _ in sent]
    assert methods[0] == "sendPhoto" and methods[-1] == "sendDocument"
    texts = [kw["json"]["text"] for m, kw in sent if m == "sendMessage"]
    assert all(len(t) <= 4096 for t in texts), "הודעה חרגה ממגבלת טלגרם"
    body = "\n".join(texts)
    assert "shvoongweb.github.io/running-news-agent" in body
    assert all(s["title_he"] in body for s in STORIES)
    # ללא תמונה - הכתבה הראשית חייבת עדיין לצאת בטקסט
    sent.clear()
    telegram_post.post_to_telegram(FEATURE, STORIES, "26.08.2026", html_path)
    body2 = "\n".join(kw["json"]["text"] for m, kw in sent if m == "sendMessage")
    assert FEATURE["title_he"] in body2 and FEATURE["lead_he"] in body2
    print(f"✓ טלגרם: {methods.count('sendMessage')} הודעות + תמונה + מסמך")


if __name__ == "__main__":
    test_filter()
    test_fetch_blocks_own_site()
    p = test_html()
    test_telegram(p)
    print("\nכל הבדיקות עברו ✓")
