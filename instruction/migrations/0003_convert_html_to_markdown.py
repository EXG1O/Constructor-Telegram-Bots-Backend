from django.db import migrations

from constructor_telegram_bots.utils.migrations import convert_html_to_markdown


class Migration(migrations.Migration):
    dependencies = [('instruction', '0002_alter_section_position')]
    operations = [
        migrations.RunPython(
            convert_html_to_markdown(
                app_label='instruction', model_name='Section', fields=['text']
            )
        )
    ]
