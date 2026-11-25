# ריצה יומית (אוטומטית, בלי אישור)

ערוצי Buffer (organization "My organization", id 6aafb708220e9efd7eabd768):
- youtube  6b06fd408541f09ecb9e7d6a
- tiktok   6b06fd018541f09ecb9e7a68
- instagram 6b0701ee8541f09ecb9eae26

## שלבים
1. לקרוא SERIES.md, STATE.md ואת כל episodes/*.json. N = "הפרק הבא" ב-STATE.md.
   אם videos/s01eNN.mp4 כבר קיים ו-STATE אומר שפורסם: לעצור (אין כפילויות). אם N > 30: לעצור ולדווח שהעונה נגמרה.
2. לכתוב episodes/s01eNN.json לפי כללי SERIES.md. לבדוק שה-JSON תקין.
3. סביבה: python3 עם numpy ו-playwright (pip install --break-system-packages numpy playwright), ffmpeg, Chrome (channel="chrome"; אם אין: `playwright install chromium` ולהחליף ב-render.py את channel).
4. לרנדר:
   python3 render.py episodes/s01eNN.json videos/s01eNN.mp4
   python3 render.py episodes/s01eNN.json videos/s01eNN_wide.mp4 --wide
   לבדוק ב-ffprobe: 1080x1920 ו-1920x1080, אורך 70 עד 110 שניות. אם חורג: לתקן את הפרק ולרנדר שוב. לפתוח פריים אחד מ-*_work ולוודא שהעברית תקינה.
5. אם N מתחלק ב-7: python3 weekly.py videos/week{N/7}.mp4 <7 קובצי ה-wide של השבוע>.
6. לעדכן STATE.md (פרק אחרון, הבא, תקציר, חוטים פתוחים, יומן), commit ו-push ל-main.
7. לוודא שהקישורים מחזירים 200:
   https://raw.githubusercontent.com/idobits261/maklida/main/videos/s01eNN.mp4 (וגם _wide)
8. לפרסם דרך כלי Buffer (create_post, mode "shareNow", schedulingType "automatic"), 4 פוסטים:
   - youtube short: אנכי. metadata.youtube {type:"short", title:"נשלח בטעות | פרק N", categoryId:"24"}
   - youtube regularVideo: רוחבי. {type:"regularVideo", title:"נשלח בטעות | פרק N | דרמה בהודעות", categoryId:"24"}, טקסט: "נשלח בטעות, פרק N. <שורת טיזר>. דרמה בהודעות, פרק חדש כל יום. הסיפור בדיוני."
   - tiktok: אנכי.
   - instagram: אנכי. metadata.instagram {type:"reel", shouldShareToFeed:true}
   טקסט לאנכיים: "נשלח בטעות | פרק N. <שורת טיזר בלי ספוילר>. פרק חדש כל יום. #סיפורבהודעות #דרמה #מתח #סדרה"
   אם יש פרק שבועי: עוד פוסט youtube regularVideo, title "נשלח בטעות | פרקים A עד B ברצף".
9. לבדוק ב-list_posts שהארבעה במצב sent/sending בלי error. לרשום ביומן ב-STATE.md ולדחוף.
10. אם שלב נכשל: לא לפרסם חלקית בלי לרשום. לרשום ב-STATE.md מה נכשל ולמה, לדחוף, ולדווח לעידו בעברית קצרה.
