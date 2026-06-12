from django.db import migrations


def drop_police_verification_columns(apps, schema_editor):
    if schema_editor.connection.vendor != "mysql":
        return

    tables = [
        "wings_employeeprofile",
        "wings_employeesignupapplication",
    ]

    with schema_editor.connection.cursor() as cursor:
        for table in tables:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = %s
                  AND COLUMN_NAME = 'police_verification'
                """,
                [table],
            )
            if cursor.fetchone()[0]:
                schema_editor.execute(
                    f"ALTER TABLE `{table}` DROP COLUMN `police_verification`"
                )


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('wings', '0002_alter_user_is_active'),
    ]

    operations = [
        migrations.RunPython(
            drop_police_verification_columns,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
