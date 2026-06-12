import django.db.models.deletion
import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_remove_organisation_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='organisation',
            name='company_address',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='organisation',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='organisation',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='user',
            name='organisation',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user', to='accounts.organisation'),
        ),

        # Step 1 — add new uuid column alongside existing bigint id
        migrations.RunSQL(
            sql="ALTER TABLE accounts_organisation ADD COLUMN new_id uuid DEFAULT gen_random_uuid();",
            reverse_sql="ALTER TABLE accounts_organisation DROP COLUMN new_id;",
        ),

        # Step 2 — populate new_id for any existing rows
        migrations.RunSQL(
            sql="UPDATE accounts_organisation SET new_id = gen_random_uuid() WHERE new_id IS NULL;",
            reverse_sql=migrations.RunSQL.noop,
        ),

        # Step 3 — drop the default so it's not auto-applied going forward
        migrations.RunSQL(
            sql="ALTER TABLE accounts_organisation ALTER COLUMN new_id DROP DEFAULT;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        
        # Step 3b — drop foreign key constraint on user table first
        migrations.RunSQL(
            sql="""
                ALTER TABLE accounts_user 
                DROP CONSTRAINT IF EXISTS accounts_user_organisation_id_fkey;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),

        # Step 3c — drop the organisation_id column from user temporarily  
        migrations.RunSQL(
            sql="ALTER TABLE accounts_user DROP COLUMN IF EXISTS organisation_id;",
            reverse_sql=migrations.RunSQL.noop,
        ),

        # Step 4 — drop old primary key constraint
        migrations.RunSQL(
            sql="ALTER TABLE accounts_organisation DROP CONSTRAINT accounts_organisation_pkey;",
            reverse_sql=migrations.RunSQL.noop,
        ),

        # Step 5 — drop old id column
        migrations.RunSQL(
            sql="ALTER TABLE accounts_organisation DROP COLUMN id;",
            reverse_sql=migrations.RunSQL.noop,
        ),

        # Step 6 — rename new_id to id
        migrations.RunSQL(
            sql="ALTER TABLE accounts_organisation RENAME COLUMN new_id TO id;",
            reverse_sql=migrations.RunSQL.noop,
        ),

        # Step 7 — set as primary key with not null
        migrations.RunSQL(
            sql="ALTER TABLE accounts_organisation ADD PRIMARY KEY (id);",
            reverse_sql=migrations.RunSQL.noop,
        ),

        # Replace Step 8 (the AlterField) with this:
        migrations.SeparateDatabaseAndState(
            database_operations=[],  # do nothing in DB — raw SQL already handled it
            state_operations=[
                migrations.AlterField(
                    model_name='organisation',
                    name='id',
                    field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
                ),
            ]
        ),
        
        # Step 9 — re-add organisation_id to user as uuid
        migrations.RunSQL(
            sql="""
                ALTER TABLE accounts_user 
                ADD COLUMN organisation_id uuid NULL 
                REFERENCES accounts_organisation(id) 
                ON DELETE SET NULL;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]