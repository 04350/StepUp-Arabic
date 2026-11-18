# StepUp Arabic — תוכנת לימוד ערבית אופליין

פרויקט מקביל ל-StepUp English: יישום לימוד אחד, ארוז לתוכנת Windows עצמאית ולאפליקציית Android.

## מטרות
- לימוד מאפס מוחלט: 28 האותיות, צורות החיבור, ניקוד וקריאה.
- שני מסלולים נפרדים: ערבית מדוברת פלסטינית וערבית ספרותית (MSA).
- שיעורים, תרגילים, מבחנים, הקלטות והתקדמות מקומיים.
- ממשק בעברית RTL עם הצגה נכונה של ערבית מימין לשמאל.
- שימוש ללא אינטרנט אחרי ההתקנה.

## מבנה
- index.html — ממשק ותוכן לימוד.
- desktop/ — מעטפת Windows באמצעות Go ו-Microsoft WebView2.
- android/ — מעטפת Android באמצעות WebView מקומי וללא הרשאת INTERNET.
- .github/workflows/ — בניית EXE ו-APK.
- tests/ — בדיקות תוכן ו-JavaScript.
- docs/ — אפיון ומקורות מדיה.

## מצב התחלתי
המאגר נפתח כעת עם אב-טיפוס תשתיתי: מסכי בית, אלפבית, שני מסלולים, שיעורי דוגמה, תרגיל הדגמה, שמירת התקדמות וגיבוי/שחזור. אין לראות בשלב זה קורס שלם או חבילת התקנה מוכנה.

## אסטרטגיית שמע ורישוי
1. Nahw Arabic Tashkeel Speech Dataset: יותר מ-1,000 הקלטות של דוברי ערבית ילידיים, תמלול מנוקד, WAV 16 kHz ורישיון CC BY 4.0. נבחר קטעים שמתאימים לתרגילי הבנת הנשמע בערבית ספרותית, עם קרדיט ורישיון מתאים.
2. Nabra-7M-Distill: מודל TTS קטן (Apache 2.0, כ-28.7MB), שמיועד ל-MSA ויכול להפיק קול במכשיר. זהו קול מסונתז, לא הקלטה אנושית, והוא יסומן בהתאם.
3. ערבית מדוברת פלסטינית: לא נארוז מאגר לפני שנאמת הרשאה מפורשת להפצה ולהטמעה אופליין. מאגר Casablanca Palestine שנבדק הוא CC BY-NC-ND 4.0, ולכן לא נחתוך או נערוך ממנו קטעים. עד למציאת מקור מתאים, המסלול המדובר יוכל להתחיל בטקסט ובתרגול כתוב.

Common Voice Arabic 27 הוא CC0, אבל דף המאגר אוסר במפורש re-host/re-share שלו. לא נעתיק את המאגר לתוך התקנות.

## קישורים למקורות שנבדקו
- Nahw dataset: https://huggingface.co/datasets/NahwAI/arabic-tashkeel-speech
- Nahw licensing: https://www.nahw.ai/blog/arabic-speech-dataset
- Nabra model: https://huggingface.co/oddadmix/Nabra-7M-Distill
- Nabra browser implementation: https://github.com/Oddadmix/nabra-tts
- Common Voice Arabic 27: https://mozilladatacollective.com/datasets/cmu5wom3z00ceo107guxtg4xa
- Casablanca Palestine: https://huggingface.co/datasets/UBC-NLP/Casablanca/tree/main/Palestine

כל קובץ שמע שייכנס בפועל יתועד עם מקור, רישיון וקרדיט ב-audio/ATTRIBUTION.md.

## בנייה
- Windows: GitHub Actions → Build StepUp Arabic desktop app.
- Android: GitHub Actions → Build StepUp Arabic Android APK.

היישומים יארזו את התוכן והמדיה בתוך קובצי ההתקנה. לא תהיה תלות בשרת בזמן הלימוד.


## Human listening samples
The build workflow attempts to fetch two unmodified, neutral MSA clips from Nahw.ai's CC BY 4.0 dataset:
- في الصباح
- في مدينة صغيرة

The clips are packaged in the Windows executable and Android APK when the dataset fetch succeeds. The app remains usable without them; unavailable audio controls explain that the clip is not included. These clips are MSA/general Arabic speech, not Palestinian-dialect recordings. Attribution and the source manifest are included in audio/.
