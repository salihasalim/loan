# Generated by Django 5.1 on 2025-03-12 09:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('UserApp', '0004_profileupdate'),
    ]

    operations = [
        migrations.AddField(
            model_name='staffmodel',
            name='account_no',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='staffmodel',
            name='adhaar_img',
            field=models.FileField(blank=True, null=True, upload_to='adhaar/'),
        ),
        migrations.AddField(
            model_name='staffmodel',
            name='adhaar_no',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='staffmodel',
            name='bank_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='staffmodel',
            name='branch',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='staffmodel',
            name='cancelled_check',
            field=models.FileField(blank=True, null=True, upload_to='cancelled_check/'),
        ),
        migrations.AddField(
            model_name='staffmodel',
            name='ifsc_code',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='staffmodel',
            name='pan_img',
            field=models.FileField(blank=True, null=True, upload_to='pancard/'),
        ),
        migrations.AddField(
            model_name='staffmodel',
            name='pan_no',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='staffmodel',
            name='profile_completed',
            field=models.BooleanField(default=False),
        ),
        migrations.DeleteModel(
            name='ProfileUpdate',
        ),
    ]
