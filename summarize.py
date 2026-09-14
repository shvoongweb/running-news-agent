# -*- coding: utf-8 -*-
"""שלב 2: Gemini - כתבה ראשית על סיפור היום + ידיעות קצרות, בעברית."""
import json
import os
import time

import requests

from config import GEMINI_MODEL, NUM_STORIES, FOCUS_EVENT

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

PROMPT = """אתה עורך חדשות ריצה מקצועי הכותב בעברית לקהל ישראלי של רצים - מחובבים ועד תחרותיים.
לפניך רשימת ידיעות (JSON) מ-36 השעות האחרונות מאתרי הריצה והאתלטיקה המובילים בעולם ומאתרים ישראליים. חלק מהידיעות כוללות שדה details עם טקסט מורחב - שם נמצאים הזמנים, התוצאות והציטוטים.

{focus_line}

צור JSON עם שני חלקים:

1. "feature" - כתבה ראשית על **הסיפור הגדול של היום** בעולם הריצה. בחר את הידיעה החשובה, המסקרנת או המדוברת ביותר (תוצאת מרוץ גדול, שיא, פרישה, מעבר קבוצה, סערה, מחקר או חידוש משמעותי). מלא את כל השדות:
   - "title_he": כותרת ראשית קולעת (עד 12 מילים)
   - "lead_he": פסקת פתיחה אחת (2-3 משפטים) שמספרת את העיקר - מי, מה, איפה ולמה זה חשוב
   - "body_he": 2-3 פסקאות נוספות (מופרדות ב-\\n\\n) עם הפירוט: איך זה קרה, נתונים, ציטוטים אם יש, והקשר רחב
   - "key_facts_he": מערך של 2-4 מחרוזות - עובדות המפתח בשורה אחת כל אחת (זמן, מקום, פער, שיא, גיל, מרחק). לדוגמה "2:03:41 - השיא האישי החדש" או "פער של 47 שניות על המקום השני". קח את המספרים אך ורק מהידיעות; אם אין נתונים מספריים - מערך ריק []
   - "why_it_matters_he": משפט או שניים - למה זה מעניין את הרץ הישראלי (הקשר, השלכות, מה צפוי הלאה). אם אין זווית אמיתית - ""
   - "image_keyword": שאילתת תמונה באנגלית - שם הרץ המרכזי + הקשר (למשל "Jakob Ingebrigtsen runner" או "Berlin Marathon finish")
   - "source_name", "source_url": המקור העיקרי

2. "stories" - {n} ידיעות קצרות על נושאים אחרים (לא מה שכבר סוקר בכתבה הראשית). גוון בין תחרותי לבין ריצת עם, אימונים, ציוד ומחקר, וכלול ידיעה ישראלית אם יש כזו ברשימה:
   לכל אחת: "title_he" (כותרת קצרה), "paragraph_he" (פסקה של 3-4 משפטים בניסוח מקורי), "source_name", "source_url"

כללים מחייבים:
- שמות רצים בעברית מלאה (שם פרטי + משפחה) כשידוע לך; אחרת תעתיק את שם המשפחה. בפעם הראשונה אפשר להוסיף את השם הלועזי בסוגריים.
- זמנים ומרחקים בפורמט ישראלי: "2:03:41", "10 ק\"מ", "חצי מרתון".
- אסור להמציא עובדות, שמות, זמנים או פערים שלא מופיעים בידיעות המקור. עדיף לוותר על נתון מלהמציא אותו.
- ניסוח מקורי לחלוטין - לא תרגום מילולי של המקור.
- אם ידיעה במקור בעברית - נסח מחדש, אל תעתיק.

החזר JSON תקין בלבד (ללא טקסט נוסף וללא סימוני קוד):
{{"feature": {{...}}, "stories": [...]}}

הידיעות:
{items}
"""


def _clean_json(text):
    """חילוץ JSON תקין גם אם המודל עטף בטקסט/סימוני קוד."""
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]
    return json.loads(text)


def _ask_gemini(prompt, key):
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.4},
    }
    r = requests.post(API_URL.format(model=GEMINI_MODEL, key=key), json=body, timeout=180)
    r.raise_for_status()
    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    return _clean_json(text)


def summarize(items):
    key = os.environ["GEMINI_API_KEY"]
    focus_line = (
        f'שים לב: יש פוקוס עונתי על "{FOCUS_EVENT}" - אם יש ברשימה ידיעה משמעותית על האירוע הזה, '
        "היא הכתבה הראשית." if FOCUS_EVENT else
        "אין פוקוס עונתי - בחר בעצמך את הסיפור החזק ביותר של היום."
    )
    # שדה image הוא לשימוש פנימי (תמונת הירו) - לא נשלח למודל
    payload = [{k: v for k, v in it.items() if k != "image"} for it in items]
    prompt = PROMPT.format(
        n=NUM_STORIES - 1,
        focus_line=focus_line,
        items=json.dumps(payload, ensure_ascii=False),
    )

    data = None
    last_err = None
    for attempt in range(1, 4):
        try:
            data = _ask_gemini(prompt, key)
            break
        except (requests.RequestException, json.JSONDecodeError, KeyError) as ex:
            last_err = ex
            print(f"[gemini] ניסיון {attempt}/3 נכשל: {ex}")
            time.sleep(4)
    if data is None:
        raise last_err

    feature = data.get("feature")
    stories = data.get("stories") or []
    print(f"[gemini] כתבה ראשית: {'כן' if feature else 'אין'} | ידיעות קצרות: {len(stories)}")
    return feature, stories
