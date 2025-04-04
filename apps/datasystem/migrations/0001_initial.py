# Generated by Django 5.1.1 on 2025-01-16 05:54

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CsvExportHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('progress', models.IntegerField(default=0)),
                ('total_records', models.IntegerField(default=0)),
                ('credits', models.FloatField(default=0.0)),
                ('exported_by', models.DateTimeField(default=django.utils.timezone.now)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='CsvImportHistroy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_records', models.IntegerField(default=0)),
                ('created_by', models.DateTimeField(default=django.utils.timezone.now)),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='DataEntry',
            fields=[
                ('peolloid', models.BigAutoField(primary_key=True, serialize=False)),
                ('first_name', models.CharField(blank=True, max_length=255)),
                ('last_name', models.CharField(blank=True, max_length=255)),
                ('title', models.CharField(blank=True, max_length=255)),
                ('company', models.CharField(blank=True, max_length=255)),
                ('company_name_for_emails', models.CharField(blank=True, max_length=255)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('email_status', models.CharField(blank=True, max_length=255)),
                ('email_confidence', models.CharField(blank=True, max_length=255)),
                ('primary_email_catch_allstatus', models.CharField(blank=True, max_length=255)),
                ('primary_email_last_verified_at', models.CharField(blank=True, max_length=255)),
                ('seniority', models.CharField(blank=True, max_length=255)),
                ('department', models.CharField(blank=True, max_length=255)),
                ('contact_owner', models.CharField(blank=True, max_length=255)),
                ('first_phone', models.CharField(blank=True, max_length=255)),
                ('work_direct_phone', models.CharField(blank=True, max_length=255)),
                ('home_phone', models.CharField(blank=True, max_length=255)),
                ('mobile_phone', models.CharField(blank=True, max_length=255)),
                ('corporate_phone', models.CharField(blank=True, max_length=255)),
                ('other_phone', models.CharField(blank=True, max_length=255)),
                ('stage', models.CharField(blank=True, max_length=255)),
                ('lists', models.CharField(blank=True, max_length=255)),
                ('last_contacted', models.CharField(blank=True, max_length=255)),
                ('account_owner', models.CharField(blank=True, max_length=255)),
                ('employees', models.IntegerField(blank=True, null=True)),
                ('industry', models.CharField(blank=True, max_length=255)),
                ('keywords', models.JSONField(blank=True, null=True)),
                ('person_linkedin_url', models.CharField(blank=True, max_length=255)),
                ('website', models.CharField(blank=True, max_length=255)),
                ('company_linkedin_url', models.CharField(blank=True, max_length=255)),
                ('facebook_url', models.CharField(blank=True, max_length=255)),
                ('twitter_url', models.CharField(blank=True, max_length=255)),
                ('city', models.CharField(blank=True, max_length=255)),
                ('state', models.CharField(blank=True, max_length=255)),
                ('country', models.CharField(blank=True, max_length=255)),
                ('company_address', models.TextField(blank=True)),
                ('company_city', models.CharField(blank=True, max_length=255)),
                ('company_state', models.CharField(blank=True, max_length=255)),
                ('company_country', models.CharField(blank=True, max_length=255)),
                ('company_phone', models.CharField(blank=True, max_length=255)),
                ('seo_description', models.TextField(blank=True)),
                ('technologies', models.JSONField(blank=True, null=True)),
                ('annual_revenue', models.BigIntegerField(blank=True, null=True)),
                ('total_funding', models.CharField(blank=True, max_length=255)),
                ('latest_funding', models.CharField(blank=True, max_length=255)),
                ('latest_funding_amount', models.CharField(blank=True, max_length=255)),
                ('last_raised_at', models.CharField(blank=True, max_length=255)),
                ('email_sent', models.CharField(blank=True, max_length=255)),
                ('email_open', models.CharField(blank=True, max_length=255)),
                ('email_bounced', models.CharField(blank=True, max_length=255)),
                ('replied', models.CharField(blank=True, max_length=255)),
                ('demoed', models.CharField(blank=True, max_length=255)),
                ('number_of_retailed_locations', models.CharField(blank=True, max_length=255)),
                ('apollo_contact_id', models.CharField(blank=True, max_length=255)),
                ('apollo_account_id', models.CharField(blank=True, max_length=255)),
                ('primary_email_source', models.CharField(blank=True, max_length=255)),
                ('secondary_email', models.CharField(blank=True, max_length=255)),
                ('secondary_email_source', models.CharField(blank=True, max_length=255)),
                ('tertiary_email', models.CharField(blank=True, max_length=255)),
                ('tertiary_email_source', models.CharField(blank=True, max_length=255)),
                ('primary_intent_topic', models.CharField(blank=True, max_length=255)),
                ('primary_intent_score', models.CharField(blank=True, max_length=255)),
                ('secondary_intent_topic', models.CharField(blank=True, max_length=255)),
                ('secondary_intent_score', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SavedData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('saved_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('data', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='datasystem.dataentry')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SavedList',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('folder_name', models.CharField(blank=True, max_length=255, null=True)),
                ('saved_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_modified_at', models.DateTimeField(auto_now=True)),
                ('data', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='datasystem.dataentry')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserDataPurchase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_purchased', models.BooleanField(default=False)),
                ('purchase_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('data', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='datasystem.dataentry')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'data')},
            },
        ),
    ]
