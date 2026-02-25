# Generated migration - Update category choices: 0.5L, 0.9L, 3L, 5L

from django.db import migrations, models


def migrate_old_categories_to_new(apps, schema_editor):
    """Migre les anciennes catégories vers les nouvelles (1.5L->0.9L, bedon->3L)"""
    QRCode = apps.get_model('qr_codes', 'QRCode')
    QRCode.objects.filter(category='1.5L').update(category='0.9L')
    QRCode.objects.filter(category='bedon').update(category='3L')
    # 5L reste inchangé


def reverse_migrate(apps, schema_editor):
    """Rollback: 0.9L->1.5L, 3L->bedon"""
    QRCode = apps.get_model('qr_codes', 'QRCode')
    QRCode.objects.filter(category='0.9L').update(category='1.5L')
    QRCode.objects.filter(category='3L').update(category='bedon')


class Migration(migrations.Migration):

    dependencies = [
        ('qr_codes', '0007_qrcode_category'),
    ]

    operations = [
        migrations.RunPython(migrate_old_categories_to_new, reverse_migrate),
        migrations.AlterField(
            model_name='qrcode',
            name='category',
            field=models.CharField(
                choices=[
                    ('0.5L', 'Bouteille 0,5 L'),
                    ('0.9L', 'Bouteille 0,9 L'),
                    ('3L', 'Bouteille 3 L'),
                    ('5L', 'Bouteille 5 L'),
                ],
                default='0.5L',
                help_text='Catégorie de la bouteille',
                max_length=20,
            ),
        ),
    ]
