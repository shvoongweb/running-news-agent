# -*- coding: utf-8 -*-
"""הגדרות מרכזיות לסוכן חדשות הריצה."""

# מקורות הריצה. include_keywords (אופציונלי) מסנן פיד רב-תחומי לידיעות ריצה בלבד.
SOURCES = [
    {"name": "Athletics Weekly",      "feed": "https://athleticsweekly.com/feed/",
     "site": "https://athleticsweekly.com"},
    {"name": "Athletics Illustrated", "feed": "https://www.athleticsillustrated.com/feed/",
     "site": "https://www.athleticsillustrated.com"},
    {"name": "Canadian Running",      "feed": "https://runningmagazine.ca/feed/",
     "site": "https://runningmagazine.ca"},
    {"name": "Runner's World",        "feed": "https://www.runnersworld.com/rss/all.xml/",
     "site": "https://www.runnersworld.com"},
    {"name": "Runner's Tribe",        "feed": "https://runnerstribe.com/feed/",
     "site": "https://runnerstribe.com"},
    # מקורות ישראליים (לא כולל שוונג - זה האתר שלנו)
    {"name": "RUNPANEL",              "feed": "https://runpanel.co.il/feed/",
     "site": "https://runpanel.co.il"},
    {"name": "מרתון ישראל",            "feed": "https://www.marathonisrael.co.il/feed/",
     "site": "https://www.marathonisrael.co.il"},
    # פיד ספורט כללי - מסונן לידיעות ריצה/אתלטיקה בלבד
    {"name": "ynet ספורט",             "feed": "https://www.ynet.co.il/Integration/StoryRss3.xml",
     "site": "https://www.ynet.co.il/sport",
     "include_keywords": ["מרתון", "חצי מרתון", "מרוץ", "אתלטיק", "ריצה", "ריצת",
                          "אולטרה", "טריאתל", "הליכה ספורטיבית", "שיא ישראלי"]},
]

# מקורות שלא נאספים לעולם (האתרים שלנו - אין טעם לצטט את עצמנו)
BLOCKED_DOMAINS = ["shvoong.co.il"]

# כמה שעות אחורה לאסוף ידיעות (בריצה קצב הפרסום נמוך מאופניים - חלון רחב יותר)
HOURS_WINDOW = 36

# כמה ידיעות בכתבה היומית (כתבה ראשית + NUM_STORIES-1 ידיעות קצרות)
NUM_STORIES = 5

# דגם Gemini (שכבה חינמית)
GEMINI_MODEL = "gemini-2.5-flash"

# כותרת המותג
BRAND_TITLE = "חדשות עולם הריצה"
BRAND_EMOJI = "🏃"

# פוקוס עונתי אופציונלי: שם אירוע באנגלית/עברית שיקבל עדיפות בבחירת הכתבה הראשית.
# למשל "Berlin Marathon" בספטמבר או "World Athletics Championships" באליפות.
# ריק = הסוכן בוחר לבד את הסיפור הגדול של היום.
FOCUS_EVENT = ""

# תקרת פריטים גולמיים שנשלחים ל-Gemini לדירוג
MAX_RAW_ITEMS = 40
