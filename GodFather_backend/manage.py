#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# Port 8000 is often taken by Cursor IDE on Windows — prefer 8001+ for local API
_RUNSERVER_PORT_CANDIDATES = (8001, 8002, 8003, 8888)


def _pick_runserver_addrport():
    import socket

    for port in _RUNSERVER_PORT_CANDIDATES:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
                return f"127.0.0.1:{port}"
            except OSError:
                continue
    return "127.0.0.1:8001"


def _patch_runserver_argv():
    """Use a free port when `python manage.py runserver` is run with no address/port."""
    if len(sys.argv) < 2 or sys.argv[1] != "runserver":
        return
    has_addrport = any(not a.startswith("-") for a in sys.argv[2:])
    if has_addrport:
        return
    os.environ.setdefault("DJANGO_SKIP_KNOWLEDGE_AUTO", "1")
    sys.argv.append(_pick_runserver_addrport())


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
    _patch_runserver_argv()
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
