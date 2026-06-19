SEIF Laboratory Management System Pro V2

طريقة التشغيل الآمنة:
1) افتحي STOP_OLD_STREAMLIT.bat لو كان فيه سيرفر قديم شغال.
2) افتحي CMD داخل نفس فولدر المشروع.
3) اكتبي:
   pip install -r requirements.txt
   python -m streamlit run app.py --server.port 8503
4) افتحي:
   http://localhost:8503

بيانات الدخول الافتراضية:
username: admin
password: admin123

ملاحظات مهمة:
- ملف الويب الصحيح اسمه app.py.
- لا تشغلي ملف tkinter القديم بـ streamlit.
- لو ظهر لك Created on Sun Jun... يبقى ما زال هناك ملف قديم شغال أو المتصفح مفتوح على سيرفر قديم.
- احذفي/اقفلي أي نافذة Desktop قديمة قبل التصوير.
