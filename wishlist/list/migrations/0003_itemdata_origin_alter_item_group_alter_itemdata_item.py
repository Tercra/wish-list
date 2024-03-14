# Generated by Django 4.2.10 on 2024-03-14 06:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('list', '0002_item_itemdata'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemdata',
            name='origin',
            field=models.CharField(default='Republic', max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='item',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='list.group'),
        ),
        migrations.AlterField(
            model_name='itemdata',
            name='item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='idata', to='list.item'),
        ),
    ]