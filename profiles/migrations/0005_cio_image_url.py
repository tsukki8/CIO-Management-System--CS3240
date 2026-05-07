from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0004_cio_status_hidden_public"),
    ]

    operations = [
        migrations.AddField(
            model_name="cio",
            name="image_url",
            field=models.CharField(
                blank=True,
                help_text="S3 URL for CIO profile image. Set by S3 integration.",
                max_length=500,
                null=True,
            ),
        ),
    ]
