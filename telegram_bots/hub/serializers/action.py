from rest_framework import serializers

from ...models import Action, ActionMessageDeletion
from .connection import ConnectionSerializer


class ActionMessageDeletionSerializer(
    serializers.ModelSerializer[ActionMessageDeletion]
):
    class Meta:
        model = ActionMessageDeletion
        fields = ['target']


class ActionSerializer(serializers.ModelSerializer[Action]):
    message_deletion = ActionMessageDeletionSerializer()
    source_connections = ConnectionSerializer(many=True)

    class Meta:
        model = Action
        fields = ['id', 'message_deletion', 'source_connections']
