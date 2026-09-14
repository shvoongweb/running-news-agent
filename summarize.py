# -*- coding: utf-8 -*-
"""שלב 2: Gemini - כתבה ראשית על סיפור היום + ידיעות קצרות, בעברית."""
import json
import os
import time

import requests

from config import GEMINI_MODEL, NUM_STORIES, FOCUS_EVENT

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
LIST_URL = "https://generativelanguage.googleapis.com/v1beta/models?key={key}"

# סדר העדפה למודלים (ה-API מחזיר 404/503 כשמודל לא זמין למפתח או עמוס)
FALLBACK_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-3-flash-preview",
    "gemini-flash-latest",
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash",
]

_RESOLVED_MODEL = None
_BAD_MODELS = set()


def _clean_json(text):
    """חילוץ JSON תקין גם אם המודל עטף בטקסט/סימוני קוד."""
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]
    return json.loads(text)


def _available_models(key):
    """שמות המודלים שהמפתח הזה יכול להשתמש בהם ל-generateContent."""
    try:
        r = requests.get(LIST_URL.format(key=key), timeout=60)
        r.raise_for_status()
        names = [
            m["name"].split("/")[-1]
            for m in r.json().get("models", [])
            if "generateContent" in (m.get("supportedGenerationMethods") or [])
        ]
        print(f"[gemini] מודלים זמינים למפתח: {', '.join(names) or 'אין'}")
        return names
    except requests.RequestException as ex:
        print(f"[gemini] לא הצלחתי לרשום מודלים: {ex}")
        return []


def _resolve_model(key):
    """בוחר מודל שבאמת עונה: 404 = לא קיים, 5xx = עמוס, שניהם מדלגים הלאה."""
    global _RESOLVED_MODEL
    if _RESOLVED_MODEL and _RESOLVED_MODEL not in _BAD_MODELS:
        return _RESOLVED_MODEL

    candidates = [GEMINI_MODEL] + [m for m in FALLBACK_MODELS if m != GEMINI_MODEL]
    listed = False
    i = 0
    while i < len(candidates):
        model = candidates[i]
        i += 1
        if model in _BAD_MODELS:
            continue
        try:
            r = requests.post(
                API_URL.format(model=model, key=key),
                json={"contents": [{"parts": [{"text": "ping"}]}]},
                timeout=60,
            )
        except requests.RequestException as ex:
            print(f"[gemini] {model}: שגיאת רשת ({ex})")
            continue

        if r.status_code in (200, 429):
            _RESOLVED_MODEL = model
            note = " (מכסה מלאה, ננסה בכל זאת)" if r.status_code == 429 else ""
            print(f"[gemini] משתמש במודל {model}{note}")
            return model

        print(f"[gemini] {model}: HTTP {r.status_code} - מדלג")
        _BAD_MODELS.add(model)
        if r.status_code == 404 and not listed:
            listed = True
            extra = [
                m for m in _available_models(key)
                if "flash" in m and "image" not in m and "tts" not in m
                and "transcribe" not in m and m not in candidates
            ]
            candidates.extend(extra)

    raise RuntimeError("אף מודל Gemini לא זמין כרגע")


def _ask_gemini(prompt, key):
    model = _resolve_model(key)
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.4},
    }
    r = requests.post(API_URL.format(model=model, key=key), json=body, timeout=180)
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
    for attempt in range(1, 6):
        try:
            data = _ask_gemini(prompt, key)
            break
        except (requests.RequestException, json.JSONDecodeError, KeyError, RuntimeError) as ex:
            last_err = ex
            print(f"[gemini] ניסיון {attempt}/5 נכשל: {ex}")
            status = getattr(getattr(ex, "response", None), "status_code", None)
            if status and status >= 500 and _RESOLVED_MODEL:
                _BAD_MODELS.add(_RESOLVED_MODEL)
                print(f"[gemini] מסמן את {_RESOLVED_MODEL} כעמוס ועובר למודל הבא")
            time.sleep(4)
    if data is None:
        raise last_err

    feature = data.get("feature")
    stories = data.get("stories") or []
    print(f"[gemini] כתבה ראשית: {'כן' if feature else 'אין'} | ידיעות קצרות: {len(stories)}")
    return feature, stories
