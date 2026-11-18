# Audio asset policy

Add a sound file only after documenting the source, exact licence, credit and permission to redistribute it in this offline application.

Candidates:
- Nahw Arabic Tashkeel Speech Dataset (CC BY 4.0): human-recorded MSA sentence clips; select suitable clips unchanged for listening exercises and include attribution.
- Nabra-7M-Distill (Apache 2.0): optional locally generated MSA speech; synthetic, not an original speaker recording.
- No Palestinian dialect recordings are approved for bundling yet. Do not edit or redistribute the Casablanca CC BY-NC-ND corpus as lesson clips.


Additional source evaluated:
- Alconost Arabic Emotional Speech demo: 100 real recordings, including 20 Jordanian clips, CC BY-NC 4.0, 39MB. It does not contain Palestinian dialect. It may be considered for a separately-labelled Jordanian comparison lesson in a non-commercial version, but it is not the source for the core Palestinian track.
  https://huggingface.co/datasets/alconost/arabic-speech-5dialects-9emotions-demo
- The Jordanian speech demo is explicitly labelled Jordanian/South Levantine. Do not present it as Palestinian speech.


## בדיקה נוספת: מקור פלסטיני ייעודי

נבדק גם מאגר **Lahgtna v3 small**:
- https://huggingface.co/datasets/oddadmix/lahgtna-v3-small
- מציג תת-קבוצה פלסטינית מסומנת (ps) עם 4,000 הקלטות אימון ו-200 הקלטות בדיקה; לפי כרטיס המאגר, סך המאגר המעורב הוא כ-29.7GB.
- בבדיקה של כרטיס המאגר ב-Hugging Face לא נמצא שדה רישיון או היתר מפורש להפצה מחדש ולהטמעה באפליקציה. לכן אין להוריד, לערוך או לארוז קטעים ממנו עד לקבלת תנאי שימוש מפורשים מבעל המאגר.
- המאגר מכיל דיבור חופשי ממגוון נושאים ולא רק חומר לימודי. גם לאחר אישור רישוי, יהיה צורך לסנן ולבדוק כל תמלול לפני בחירת קטעים לשיעורים.

מקור השוואתי: Bayanat Labs פרסמו סקירה מעודכנת של מאגרי דיבור בערבית ורישיונותיהם בספטמבר 2026, עם עדכון בנובמבר 2026. הסקירה מדגישה שרוב המאגר הפומבי הוא MSA/שידורי/קריאה ושחומר דיבור דיאלקטי פתוח ומותר להפצה הוא מצומצם. אין בכך אישור רישוי למאגר Lahgtna:
https://www.bayanatlabs.com/insights/arabic-speech-datasets

**החלטה:** בגרסה הנוכחית נכללים רק שני קטעי Nahw המאושרים ברישיון CC BY 4.0, והם מסומנים במפורש כערבית כללית/ספרותית. במסלול הפלסטיני לא מוצגת הקלטה שאינה פלסטינית כאילו היא פלסטינית. נרחיב אותו עם שמע רק לאחר אימות רישוי ותוכן.
