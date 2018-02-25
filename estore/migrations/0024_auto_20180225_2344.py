# Generated by Django 2.0.2 on 2018-02-25 15:44

from django.db import migrations
import estore.fields


class Migration(migrations.Migration):

    dependencies = [
        ('estore', '0023_auto_20180225_2230'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='shopinfo',
            name='icon2',
        ),
        migrations.AlterField(
            model_name='product',
            name='pics',
            field=estore.fields.ManyToManyImgField(blank=True, related_name='pics', to='estore.Picture', verbose_name='细节图片集'),
        ),
    ]
