# نظام إدارة المحاسبة
# Accounting Management System

نظام محاسبة متكامل جاهز للإنتاج مع واجهة عربية حديثة.

## المتطلبات
- Python 3.11+
- SQL Server 2019+
- ODBC Driver 17 for SQL Server
- Windows (للطباعة الحرارية)

## التثبيت

### 1. إعداد قاعدة البيانات
إنشاء قاعدة بيانات جديدة في SQL Server:
```sql
CREATE DATABASE AccountingDB;
```

### 2. إعداد البيئة الخلفية (Backend)
```bash
cd backend
pip install -r requirements.txt

# تحديث إعدادات قاعدة البيانات
# قم بتعديل config/settings/local.py

# تشغيل الترحيلات
python manage.py migrate

# إنشاء مستخدم مشرف
python manage.py createsuperuser

# تشغيل الخادم
python manage.py runserver
```

### 3. إعداد الواجهة الأمامية (Frontend)
```bash
cd frontend
pip install -r requirements.txt

# تشغيل التطبيق
python main.py
```

## الوصول للنظام
- **لوحة الإدارة**: http://localhost:8000/admin/
- **API Documentation**: http://localhost:8000/api/docs/
- **تطبيق سطح المكتب**: تشغيل `python main.py` من مجلد frontend

## الميزات
- ✅ إدارة المنتجات والمخزون
- ✅ إدارة العملاء والموردين
- ✅ نقطة البيع (POS)
- ✅ الفواتير (نقدي/آجل/مرتجع)
- ✅ المشتريات وأوامر الشراء
- ✅ المصروفات
- ✅ التقارير والإحصائيات
- ✅ طباعة فواتير A4
- ✅ طباعة حرارية (58mm/80mm)
- ✅ دعم الباركود
- ✅ واجهة عربية RTL
- ✅ الوضع الليلي/النهاري

## هيكل المشروع
```
ERP/
├── backend/                  # Django API
│   ├── config/              # إعدادات Django
│   ├── apps/                # التطبيقات
│   │   ├── core/           # النماذج الأساسية
│   │   ├── accounts/       # المستخدمين
│   │   ├── inventory/      # المخزون
│   │   ├── purchases/      # المشتريات
│   │   ├── sales/          # المبيعات
│   │   ├── expenses/       # المصروفات
│   │   └── reports/        # التقارير
│   └── api/                 # نقاط API
├── frontend/                 # PySide6 Desktop
│   ├── src/
│   │   ├── config/         # الإعدادات
│   │   ├── services/       # خدمات API
│   │   ├── views/          # الشاشات
│   │   ├── widgets/        # المكونات
│   │   ├── printing/       # الطباعة
│   │   └── styles/         # المظهر
│   └── main.py             # نقطة البداية
├── ARCHITECTURE.md          # توثيق المعمارية
└── TODO.md                  # قائمة المهام
```

## الترخيص
هذا النظام مطور للاستخدام التجاري.
