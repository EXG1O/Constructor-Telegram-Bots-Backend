from django.conf import settings

from docker.errors import DockerException

from constructor_telegram_bots.docker import docker_client

from ..models import TelegramBotsHub

from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
import concurrent.futures
import os


def force_delete_hub_docker_container(id: str) -> None:
    with suppress(DockerException):
        docker_client.containers.get(id).remove(force=True)
    with suppress(FileNotFoundError):
        os.remove(settings.SOCKETS_DIR / f'{id[:12]}.sock')


def force_delete_all_hubs() -> None:
    with ThreadPoolExecutor(max_workers=12) as executor:
        concurrent.futures.wait(
            executor.submit(force_delete_hub_docker_container, container_id)
            for container_id in TelegramBotsHub.objects.values_list(
                'container_id', flat=True
            )
        )
    TelegramBotsHub.objects.all().delete()
