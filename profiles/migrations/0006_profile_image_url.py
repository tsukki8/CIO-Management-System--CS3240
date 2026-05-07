from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0005_cio_image_url"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="image_url",
            field=models.CharField(
                blank=True,
                help_text="S3 URL for user profile image. Set by S3 integration.",
                max_length=500,
                null=True,
            ),
        ),
    ]
