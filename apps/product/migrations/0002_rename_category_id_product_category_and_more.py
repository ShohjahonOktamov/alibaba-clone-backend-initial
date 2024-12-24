# Generated by Django 4.2.14 on 2024-12-23 16:14

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='category_id',
            new_name='category',
        ),
        migrations.RenameField(
            model_name='product',
            old_name='name',
            new_name='title',
        ),
        migrations.AlterField(
            model_name='category',
            name='id',
            field=models.UUIDField(default=uuid.UUID('4e90c70f-fecd-4b0f-af82-5a7c310e2164'), primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='color',
            name='id',
            field=models.UUIDField(default=uuid.UUID('b6406a33-fadc-4e15-a06b-40fe2fe0029f'), primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='image',
            name='id',
            field=models.UUIDField(default=uuid.UUID('907fac49-b981-4c7b-9177-ca57ff7cb707'), primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='product',
            name='id',
            field=models.UUIDField(default=uuid.UUID('2c2212d2-6a2f-4288-a597-cad6cee39520'), primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='size',
            name='id',
            field=models.UUIDField(default=uuid.UUID('8c46c469-6958-48c1-a211-d6315ae2f960'), primary_key=True, serialize=False),
        ),
    ]
