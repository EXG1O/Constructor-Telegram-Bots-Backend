from rest_framework import serializers

from ...models import Action, ActionDefaultKeyboardRemoval, ActionMessageDeletion
from .connection import ConnectionSerializer


class ActionMessageDeletionSerializer(
    serializers.ModelSerializer[ActionMessageDeletion]
):
    class Meta:
        model = ActionMessageDeletion
        fields = ['target']


class ActionDefaultKeyboardRemovalSerializer(
    serializers.ModelSerializer[ActionDefaultKeyboardRemoval]
):
    class Meta:
        model = ActionDefaultKeyboardRemoval
        fields = []  # type: ignore [var-annotated]


class ActionSerializer(serializers.ModelSerializer[Action]):
    message_deletion = ActionMessageDeletionSerializer()
    default_keyboard_removal = ActionDefaultKeyboardRemovalSerializer()
    source_connections = ConnectionSerializer(many=True)

    class Meta:
        model = Action
        fields = [
            'id',
            'message_deletion',
            'default_keyboard_removal',
            'source_connections',
        ]
