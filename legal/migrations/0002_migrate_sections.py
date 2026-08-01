from django.db import migrations, connection
from django.apps.registry import Apps
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from typing import TYPE_CHECKING
from ..enums import DocumentType
from django.db.backends.utils import CursorWrapper
import string

if TYPE_CHECKING:
    from ..models import Document


def _migrate_sections(
    cursor: CursorWrapper,
    document_model: type[Document],
    table_name: str,
    type: DocumentType,
) -> None:
    cursor.execute(f'SELECT title_en, text_en FROM {table_name} ORDER BY position')
    if rows := cursor.fetchall():
        content: str = ''

        for row in rows:
            title: str = row[0]
            text: str = row[1]
            content += f'### {title}\n\n{text.rstrip(string.whitespace)}\n\n'

        document_model.objects.create(type=type, content=content)
    cursor.execute(f'DROP TABLE {table_name}')


def migrate_sections(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    document_model: type[Document] = apps.get_model('legal', 'Document')

    with connection.cursor() as cursor:
        tables: list[str] = connection.introspection.table_names()

        if 'terms_of_service_section' in tables:
            _migrate_sections(
                cursor,
                document_model,
                'terms_of_service_section',
                DocumentType.TERMS_OF_SERVICE,
            )

        if 'privacy_policy_section' in tables:
            _migrate_sections(
                cursor,
                document_model,
                'privacy_policy_section',
                DocumentType.PRIVACY_POLICY,
            )


class Migration(migrations.Migration):
    dependencies = [('legal', '0001_initial')]
    operations = [
        migrations.RunPython(migrate_sections, reverse_code=migrations.RunPython.noop)
    ]
