# Generated by Django 2.0.2 on 2018-02-25 10:33

from django.db import migrations
import django.db.models.deletion
import estore.fields


class Migration(migrations.Migration):

    dependencies = [
        ('estore', '0017_auto_20180225_1719'),
    ]

    operations = [
        migrations.AlterField(
            model_name='picture',
            name='pic',
            field=estore.fields.ImageFieldEx(unique=True, upload_to='estorepics', verbose_name='图片'),
        ),
        migrations.AlterField(
            model_name='shopinfo',
            name='icon',
            field=estore.fields.ForeignImgField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='estore.Picture', to_field='pic', verbose_name='店铺图标'),
        ),
    ]