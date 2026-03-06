
# بوت تلجرام GeoSeer 🌍

هذا البوت يتيح لك البحث عن البيانات المكانية (Spatial Data) باستخدام GeoSeer API مباشرة من تطبيق تلجرام.

## المتطلبات 📋
- Python 3.7 أو أحدث.
- مفتاح GeoSeer API (الذي زودتني به تم تضمينه بالفعل في الكود).
- توكن بوت تلجرام (من @BotFather).

## التثبيت 🛠️
1. قم بتثبيت المكتبات اللازمة:
   ```bash
   pip install python-telegram-bot requests
   ```

2. قم بتعديل ملف `geoseer_telegram_bot.py` لإضافة التوكن الخاص بك:
   ابحث عن السطر التالي واستبدل `YOUR_TELEGRAM_BOT_TOKEN_HERE` بالتوكن الخاص بك:
   ```python
   TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
   ```

## التشغيل 🚀
قم بتشغيل البوت باستخدام الأمر التالي:
```bash
python geoseer_telegram_bot.py
```

## كيفية الاستخدام 🔍
- أرسل `/start` لبدء المحادثة.
- أرسل أي نص (مثل "mountains" أو "rivers") للبحث عن البيانات المكانية المتعلقة به.
- سيقوم البوت بعرض أفضل 5 نتائج مع وصف مختصر ونوع الخدمة.

---
تم التطوير بواسطة **Manus AI**
