import os
import sys
from django.core.management import execute_from_command_line


def main():
    """Punto de entrada CLI para el proyecto"""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HIMFG.settings")
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
