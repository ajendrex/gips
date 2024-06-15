import logging
from typing import Optional

from django.contrib import messages
from django.http import HttpRequest

logger = logging.getLogger(__name__)


class GIPSService:
    def __init__(self, request: Optional[HttpRequest] = None):
        self.request = request
        self._post_init()

    def _post_init(self):
        pass

    def _add_error_message(self, message: str):
        logger.error(message, exc_info=True)
        if self.request:
            messages.error(self.request, message)

    def _add_success_message(self, message: str):
        if self.request:
            messages.success(self.request, message)
        else:
            logger.info(message)
