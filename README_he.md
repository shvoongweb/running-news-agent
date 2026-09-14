# סוכן "חדשות עולם הריצה" 🏃

כתבה יומית בעברית - כתבה ראשית על הסיפור הגדול של היום + 4 ידיעות קצרות - שרצה **בחינם בענן**, גם כשהמחשב כבוי.

## מה קורה כל בוקר (07:10 שעון ישראל בקיץ)

1. **איסוף** ידיעות מ-8 מקורות ריצה (RSS, חלון 36 שעות): Athletics Weekly, Athletics Illustrated, Canadian Running, Runner's World, Runner's Tribe, RUNPANEL, מרתון ישראל ו-ynet ספורט (מסונן לידיעות ריצה בלבד). **שוונג לא נאסף** - זה האתר שלנו, והוא חסום ב-`BLOCKED_DOMAINS`.
2. **Gemini 2.5 Flash** (שכבה חינמית) בוחר את הסיפור הגדול של היום, כותב עליו כתבה ראשית בעברית (פתיח, גוף, עובדות מפתח, "למה זה חשוב"), ועוד 4 ידיעות קצרות.
3. **תמונה ראשית**: קודם הצילום מהכתבה במקור, אחר כך ויקישיתוף לפי שם הרץ, ולבסוף Pexels כגיבוי - תמיד עם קרדיט.
4. **כתבת HTML** (RTL) נשמרת ל-`docs/` ומתפרסמת ב-**GitHub Pages**, כולל ארכיון.
5. **טלגרם**: תמונה + כתבה ראשית + הידיעות + קישור לכתבה + קובץ ה-HTML כמסמך.

## עלות: 0 ₪

GitHub Actions + GitHub Pages + Gemini free tier + Telegram Bot API - הכל חינם.

## Secrets (Settings → Secrets and variables → Actions)

| שם | ערך |
|----|-----|
| `GEMINI_API_KEY` | מפתח מ-aistudio.google.com (אפשר אותו מפתח כמו בסוכן האופניים) |
| `TELEGRAM_BOT_TOKEN` | הבוט @shvoongtribot |
| `TELEGRAM_CHAT_ID` | אותו ערוץ של סוכן האופניים |
| `PEXELS_API_KEY` | אופציונלי - גיבוי לתמונות סטוק |

## פריסה

1. repo **ציבורי** (נדרש ל-Pages בחינם) → העלאת כל הקבצים.
2. הגדרת ה-Secrets.
3. Settings → Pages → Source: **Deploy from a branch** → Branch: `main`, תיקייה `/docs`.
4. Actions → daily-running-news → **Run workflow** לבדיקה.

## תזמון

Cron: `10 4 * * *` (UTC) = 07:10 בקיץ / 06:10 בחורף. GitHub לא מכיר שעון קיץ; לחורף אפשר לשנות ל-`10 5 * * *`. עיכובים של 5-15 דק' בעומס הם נורמליים.

## כוונון ב-`config.py`

- `SOURCES` - הוספה/הסרה של פידים. `include_keywords` מסנן פיד רב-תחומי (כמו ynet ספורט) לידיעות ריצה בלבד.
- `BLOCKED_DOMAINS` - דומיינים שלא נאספים לעולם (כרגע shvoong.co.il).
- `HOURS_WINDOW` - חלון האיסוף (ברירת מחדל 36 שעות).
- `NUM_STORIES` - כתבה ראשית + (NUM_STORIES-1) ידיעות קצרות.
- `FOCUS_EVENT` - פוקוס עונתי. למשל `"Berlin Marathon"` בשבוע המרתון או `"World Athletics Championships"` באליפות; ריק = הסוכן בוחר לבד.

## הערות

- כל שלב עטוף בטיפול שגיאות - פיד שנופל לא מפיל את הצינור.
- הסיכומים בניסוח מקורי + קישור למקור בכל ידיעה (זכויות יוצרים).
- הכתבות ב-Pages ציבוריות לכל מי שיש לו קישור.
