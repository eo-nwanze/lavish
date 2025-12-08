# Generated migration to fix SEO fields constraint

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0005_alter_shopifyproduct_created_at_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shopifyproduct',
            name='seo_title',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='shopifyproduct',
            name='seo_description',
            field=models.TextField(blank=True),
        ),
    ]