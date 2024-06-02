from urllib.parse import urlencode

from django.utils.html import format_html

from tests.models import Persona


def link_whatsapp(persona: Persona, msg: str, title: str) -> str:
    telefono = persona.telefono

    if telefono.startswith('+'):
        telefono = telefono[1:]

    return format_html(
        '<a href="https://wa.me/{}/?{}" target="blank">{}</a>',
        telefono,
        urlencode({'text': msg, }),
        title,
    )
