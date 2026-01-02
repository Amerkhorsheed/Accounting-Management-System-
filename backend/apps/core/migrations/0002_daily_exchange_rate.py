from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DailyExchangeRate",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث"),
                ),
                (
                    "rate_date",
                    models.DateField(unique=True, verbose_name="تاريخ سعر الصرف"),
                ),
                (
                    "usd_to_syp_old",
                    models.DecimalField(
                        decimal_places=6,
                        max_digits=18,
                        verbose_name="سعر صرف الدولار مقابل الليرة القديمة",
                    ),
                ),
                (
                    "usd_to_syp_new",
                    models.DecimalField(
                        decimal_places=6,
                        max_digits=18,
                        verbose_name="سعر صرف الدولار مقابل الليرة الجديدة",
                    ),
                ),
                (
                    "notes",
                    models.TextField(
                        blank=True,
                        null=True,
                        verbose_name="ملاحظات",
                    ),
                ),
            ],
            options={
                "verbose_name": "سعر صرف يومي",
                "verbose_name_plural": "أسعار الصرف اليومية",
                "ordering": ["-rate_date"],
            },
        ),
    ]
