# -*- coding: utf-8 -*-
"""שלב 4: שליחה לטלגרם - כתבה ראשית + ידיעות + קישור לכתבה + קובץ HTML."""
import html
import os

import requests

from config import BRAND_TITLE, BRAND_EMOJI

API = "https://api.telegram.org/bot{token}/{method}"


def _esc(s):
    return html.escape(s or "")


def _block(i, s):
    return (
        f"<b>{i}. {_esc(s.get('title_he'))}</b>\n"
        f"{_esc(s.get('paragraph_he'))}\n"
        f'🔗 <a href="{_esc(s.get("source_url"))}">{_esc(s.get("source_name"))}</a>'
    )


def _pages_url():
    """כתובת GitHub Pages נגזרת אוטומטית משם ה-repo שבו רץ ה-Action."""
    repo = os.environ.get("GITHUB_REPOSITORY", "")  # owner/repo
    if "/" in repo:
        owner, name = repo.split("/", 1)
        return f"https://{owner}.github.io/{name}/"
    return ""


_MIME = {"png": "image/png", "webp": "image/webp", "jpg": "image/jpeg", "jpeg": "image/jpeg"}


def _send_photo(token, chat_id, image_bytes, file_name, caption):
    ext = (file_name or "image.jpg").rsplit(".", 1)[-1].lower()
    mime = _MIME.get(ext, "image/jpeg")
    r = requests.post(
        API.format(token=token, method="sendPhoto"),
        data={"chat_id": chat_id, "caption": caption[:1024], "parse_mode": "HTML"},
        files={"photo": (file_name or "image.jpg", image_bytes, mime)},
        timeout=60,
    )
    r.raise_for_status()


def _feature_text(f):
    """המשך הכתבה הראשית כטקסט טלגרם (הפתיח כבר הלך לכיתוב התמונה)."""
    parts = []
    for para in (f.get("body_he") or "").split("\n\n"):
        if para.strip():
            parts.append(_esc(para.strip()))
            parts.append("")
    if f.get("key_facts_he"):
        parts.append("<b>📊 עובדות המפתח</b>")
        parts.extend("• " + _esc(x) for x in f["key_facts_he"][:4])
        parts.append("")
    if (f.get("why_it_matters_he") or "").strip():
        parts.append(f"<b>🔎 למה זה חשוב:</b> {_esc(f['why_it_matters_he'].strip())}")
        parts.append("")
    if f.get("source_url"):
        parts.append(f'🔗 <a href="{_esc(f["source_url"])}">{_esc(f.get("source_name"))}</a>')
        parts.append("")
    return parts


def post_to_telegram(feature, stories, date_str, html_path, image_bytes=None,
                     image_name=None, image_credit=""):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    parts = []
    if feature:
        caption = (f"<b>{BRAND_EMOJI} {BRAND_TITLE} - {date_str}</b>\n\n"
                   f"<b>{_esc(feature.get('title_he'))}</b>\n{_esc(feature.get('lead_he'))}")
        if image_credit:
            caption += f"\n<i>{_esc(image_credit)}</i>"
        if image_bytes:
            _send_photo(token, chat_id, image_bytes, image_name, caption[:1024])
            print("[telegram] נשלחה תמונה ראשית")
        else:
            parts.append(caption)
            parts.append("")
        parts.extend(_feature_text(feature))
        if stories:
            parts.append("<b>⚡ שאר ההיליטים של עולם הריצה</b>")
            parts.append("")
        start = 1
        rest = stories
    elif image_bytes and stories:
        caption = f"<b>{BRAND_EMOJI} {BRAND_TITLE} - {date_str}</b>\n\n" + _block(1, stories[0])
        if image_credit:
            caption += f"\n<i>{_esc(image_credit)}</i>"
        _send_photo(token, chat_id, image_bytes, image_name, caption[:1024])
        print("[telegram] נשלחה תמונה ראשית")
        rest = stories[1:]
        start = 2
    else:
        parts = [f"<b>{BRAND_EMOJI} {BRAND_TITLE} - {date_str}</b>", ""]
        rest = stories
        start = 1

    for i, s in enumerate(rest, start):
        parts.append(_block(i, s))
        parts.append("")
    url = _pages_url()
    if url:
        parts.append(f'📰 <a href="{url}">לצפייה בכתבה המלאה בדפדפן</a>')
    text = "\n".join(parts).strip()

    # טלגרם מגביל הודעה ל-4096 תווים - חוצים לפי שורות כדי לא לשבור תגיות HTML
    chunks, buf = [], ""
    for line in text.split("\n"):
        if len(buf) + len(line) + 1 > 3800:
            chunks.append(buf)
            buf = ""
        buf += line + "\n"
    if buf.strip():
        chunks.append(buf)

    for chunk in chunks:
        r = requests.post(
            API.format(token=token, method="sendMessage"),
            json={"chat_id": chat_id, "text": chunk.strip(), "parse_mode": "HTML",
                  "disable_web_page_preview": True},
            timeout=30,
        )
        r.raise_for_status()
    print(f"[telegram] נשלח מקבץ הידיעות ({len(chunks)} הודעות)")

    # קובץ ה-HTML כמסמך - פתיחה בדפדפן בלחיצה
    with open(html_path, "rb") as f:
        r = requests.post(
            API.format(token=token, method="sendDocument"),
            data={"chat_id": chat_id, "caption": f"📄 {BRAND_TITLE} - {date_str} (לפתיחה בדפדפן)"},
            files={"document": (os.path.basename(html_path), f, "text/html")},
            timeout=60,
        )
        r.raise_for_status()
    print("[telegram] נשלח קובץ ה-HTML")
