from django.db import migrations, models


def forward_map_statuses(apps, schema_editor):
    CIO = apps.get_model("profiles", "CIO")
    for cio in CIO.objects.all():
        if cio.status == "active":
            cio.status = "public"
        else:
            cio.status = "hidden"
        cio.save(update_fields=["status"])


def reverse_map_statuses(apps, schema_editor):
    CIO = apps.get_model("profiles", "CIO")
    for cio in CIO.objects.all():
        if cio.status == "public":
            cio.status = "active"
        else:
            cio.status = "pending"
        cio.save(update_fields=["status"])


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0003_cio"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cio",
            name="status",
            field=models.CharField(
                choices=[("public", "Public"), ("hidden", "Hidden")],
                default="hidden",
                max_length=20,
            ),
        ),
        migrations.RunPython(forward_map_statuses, reverse_map_statuses),
    ]
