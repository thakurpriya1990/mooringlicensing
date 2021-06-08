# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-06-03 08:47
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mooringlicensing', '0136_auto_20210603_1124'),
    ]

    operations = [
        migrations.CreateModel(
            name='MooringOnApproval',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, verbose_name='name')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('uploaded_date', models.DateTimeField(auto_now_add=True)),
                ('site_licensee', models.BooleanField()),
            ],
        ),
        migrations.RemoveField(
            model_name='approval',
            name='ria_selected_mooring',
        ),
        migrations.RemoveField(
            model_name='approval',
            name='ria_selected_mooring_bay',
        ),
        migrations.AddField(
            model_name='mooringonapproval',
            name='approval',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mooringlicensing.Approval'),
        ),
        migrations.AddField(
            model_name='mooringonapproval',
            name='mooring',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mooringlicensing.Mooring'),
        ),
        migrations.AddField(
            model_name='approval',
            name='moorings',
            field=models.ManyToManyField(through='mooringlicensing.MooringOnApproval', to='mooringlicensing.Mooring'),
        ),
    ]
