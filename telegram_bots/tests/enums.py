from django.apps import apps
from django.test import SimpleTestCase

from ..enums import ConnectionObjectType


class ConnectionObjectTypeTests(SimpleTestCase):
    def test_object_type_mapping_correctness(self) -> None:
        for (
            model_label_lower,
            expected_enum_value,
        ) in ConnectionObjectType._OBJECT_TYPE_MAP.items():
            with self.subTest(label=model_label_lower):
                self.assertEqual(
                    ConnectionObjectType.from_model(apps.get_model(model_label_lower)),
                    expected_enum_value,
                )
