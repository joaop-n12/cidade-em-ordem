"""Mostra o que esta salvo no banco do receptor."""

import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent / "dados" / "iot.db"

con = sqlite3.connect(DB)
for tabela in ("status_veiculo", "leituras", "buracos"):
    linhas = con.execute(f"SELECT * FROM {tabela}").fetchall()
    colunas = [d[0] for d in con.execute(f"SELECT * FROM {tabela} LIMIT 0").description]
    print(f"\n=== {tabela} ({len(linhas)} registros) ===")
    print(" | ".join(c for c in colunas if c != "payload"))
    for l in linhas[-15:]:
        print(" | ".join(str(v) for c, v in zip(colunas, l) if c != "payload"))
