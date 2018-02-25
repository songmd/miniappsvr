# Generated by Django 2.0.2 on 2018-02-25 12:52

from django.db import migrations
import django.db.models.deletion
import estore.fields


class Migration(migrations.Migration):

    dependencies = [
        ('estore', '0021_auto_20180225_1924'),
    ]

    operations = [
        migrations.AddField(
            model_name='shopinfo',
            name='icon2',
            field=estore.fields.ForeignImgField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='dds', to='estore.Picture', verbose_name='店铺图标2'),
        ),
    ]
