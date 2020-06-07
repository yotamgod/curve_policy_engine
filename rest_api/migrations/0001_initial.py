# Generated by Django 3.0.6 on 2020-06-06 08:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Rule',
            fields=[
                ('rule_id', models.AutoField(primary_key=True, serialize=False)),
                ('created_datetime', models.DateTimeField(auto_now_add=True)),
                ('amount', models.IntegerField(default=-1)),
                ('currency', models.CharField(default='satoshi', max_length=10)),
            ],
            options={
                'ordering': ['created_datetime'],
            },
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.IntegerField()),
                ('destination', models.CharField(max_length=100)),
                ('approved', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='Destination',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('destination_name', models.CharField(max_length=100)),
                ('rule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='destinations', to='rest_api.Rule')),
            ],
        ),
    ]