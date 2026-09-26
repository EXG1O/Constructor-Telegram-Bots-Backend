from django.apps.registry import Apps
from django.conf import settings
from django.db import models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

from html2text import HTML2Text

from collections.abc import Callable

html2text = HTML2Text(bodywidth=0)


def convert_html_to_markdown(
    app_label: str, model_name: str, fields: list[str]
) -> Callable[[Apps, BaseDatabaseSchemaEditor], None]:
    def wrapper(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
        Model: type[models.Model] = apps.get_model(app_label, model_name)

        for instance in Model.objects.iterator():  # type: ignore [attr-defined]
            update_fields: list[str] = []

            for field in fields:
                setattr(instance, field, html2text.handle(getattr(instance, field)))
                update_fields.append(field)

                for lang_code, _ in settings.LANGUAGES:
                    lang_field: str = f'{field}_{lang_code}'

                    if hasattr(instance, lang_field):
                        setattr(
                            instance,
                            lang_field,
                            html2text.handle(getattr(instance, lang_field)),
                        )
                        update_fields.append(lang_field)

            instance.save(update_fields=update_fields)

    return wrapper
