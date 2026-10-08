import sqlite3
from pathlib import Path
from datetime import date

# Datos personales guardados en una carpeta excluida de git
database_path = Path(__file__).parent / "data" / "private" / "demo.db"
database_path.parent.mkdir(parents=True, exist_ok=True)

connection = sqlite3.connect(database_path)

try:
    # Crear la tabla no borra datos si ya existe
    connection.execute("""
        CREATE TABLE IF NOT EXISTS maintenance (
            id INTEGER PRIMARY KEY,
            performed_on TEXT NOT NULL,
            odometer_km INTEGER NOT NULL CHECK (odometer_km >= 0),
            description TEXT NOT NULL
        )
    """)

    # Datos
    performed_on = input("Fecha del trabajo (YYYY-MM-DD): ").strip()
    date.fromisoformat(performed_on)

    odometer_km = int(input("Kilometraje: ").strip())
    if odometer_km < 0:
        raise ValueError("El kilometraje no puede ser negativo.")

    description = input("Trabajo realizado: ").strip()
    if not description:
        raise ValueError("La descripción no puede estar vacía.")

    record = (
        performed_on,
        odometer_km,
        description,
    )

    connection.execute(
        """
        INSERT INTO maintenance (
            performed_on, odometer_km, description
        )
        VALUES (?, ?, ?)
        """,
        record,
    )

    # Confirmamos que quede guardado
    connection.commit()

    records = connection.execute("""
        SELECT id, performed_on, odometer_km, description
        FROM maintenance
        ORDER BY id
    """).fetchall()

    for record in records:
        print(record)

finally:
    connection.close()