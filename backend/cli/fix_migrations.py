"""Reparar el estado de migraciones desde la terminal (sin abrir el manager).

    backend\\venv\\Scripts\\python -m backend.cli.fix_migrations

Hace lo mismo que el manager > Base de datos > Migraciones > [7]: quita de alembic_version la
revisión e3f4a5b6c7d8 (su archivo ya no está en la cadena) y aplica las migraciones pendientes.

Antes este script hacía `stamp head`: marcaba la base como al día sin crear las tablas ni
columnas que faltaban.
"""
from backend.cli.modules.db.migrations.fix_state import fix_state


def main():
    fix_state()


if __name__ == "__main__":
    main()
