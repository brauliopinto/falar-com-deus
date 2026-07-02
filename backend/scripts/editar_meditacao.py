#!/usr/bin/env python3
"""
Visualiza e edita meditações no banco de dados.

Uso dentro do container:
    python scripts/editar_meditacao.py              # lista meditações disponíveis
    python scripts/editar_meditacao.py 26/06/2026   # abre meditação específica

Via docker:
    docker exec -it meditacao-backend python scripts/editar_meditacao.py 26/06/2026
"""

import os
import subprocess
import sys
import tempfile

from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("Erro: variável DATABASE_URL não definida.")
    sys.exit(1)

# Campos exibidos e editáveis, na ordem de apresentação.
FIELDS: list[tuple[str, str]] = [
    ("titulo_raw",       "Título          [raw]"),
    ("titulo",           "Título          [ES normalizado]"),
    ("titulo_pt",        "Título          [PT]"),
    ("subtitulo_raw",    "Subtítulo       [raw]"),
    ("subtitulo",        "Subtítulo       [ES normalizado]"),
    ("subtitulo_pt",     "Subtítulo       [PT]"),
    ("leitura_ref_raw",  "Leitura/ref     [raw]"),
    ("leitura_ref",      "Leitura/ref     [ES normalizado]"),
    ("leitura_ref_pt",   "Leitura/ref     [PT]"),
    ("conteudo_i_raw",   "Conteúdo I      [raw]"),
    ("conteudo_i",       "Conteúdo I      [ES normalizado]"),
    ("conteudo_i_pt",    "Conteúdo I      [PT]"),
    ("conteudo_ii_raw",  "Conteúdo II     [raw]"),
    ("conteudo_ii",      "Conteúdo II     [ES normalizado]"),
    ("conteudo_ii_pt",   "Conteúdo II     [PT]"),
    ("conteudo_iii_raw", "Conteúdo III    [raw]"),
    ("conteudo_iii",     "Conteúdo III    [ES normalizado]"),
    ("conteudo_iii_pt",  "Conteúdo III    [PT]"),
]

DIVIDER = "─" * 60


def _find_editor() -> str | None:
    for candidate in [os.environ.get("EDITOR", ""), "nano", "vi", "vim"]:
        if candidate and subprocess.run(["which", candidate], capture_output=True).returncode == 0:
            return candidate
    return None


def _edit_in_editor(content: str, editor: str) -> str:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(content)
        path = f.name
    subprocess.call([editor, path])
    with open(path, encoding="utf-8") as f:
        result = f.read()
    os.unlink(path)
    return result.strip()


def _edit_inline(current: str, label: str) -> str:
    """Coleta texto multi-linha via stdin. Termina com '.' em linha isolada."""
    print(f"\n{DIVIDER}")
    print(f"  Editando: {label}")
    print(DIVIDER)
    print(current or "(vazio)")
    print(DIVIDER)
    print("Cole o novo valor abaixo.")
    print("Termine com uma linha contendo apenas '.' para confirmar.")
    print("Deixe em branco e pressione Enter (seguido de '.') para manter o valor atual.")
    print()
    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == ".":
            break
        lines.append(line)
    new_value = "\n".join(lines).strip()
    return new_value if new_value else current


def list_meditations(conn) -> None:
    rows = conn.execute(
        text("SELECT data, titulo FROM meditacoes ORDER BY data DESC")
    ).fetchall()
    if not rows:
        print("Nenhuma meditação encontrada no banco.")
        return
    print(f"\n{DIVIDER}")
    print("  Meditações disponíveis")
    print(DIVIDER)
    for row in rows:
        print(f"  {row.data}  —  {row.titulo[:55]}")
    print()


def show_record(record: dict, modified: set[str]) -> None:
    print(f"\n{DIVIDER}")
    print(f"  Meditação: {record['data']}")
    print(DIVIDER)
    for i, (col, label) in enumerate(FIELDS, 1):
        value = record.get(col, "")
        preview = (value[:80] + "…") if len(value) > 80 else value
        preview = preview.replace("\n", "↵") if preview else "(vazio)"
        flag = "  *" if col in modified else ""
        print(f"  {i:2}. {label}{flag}")
        print(f"      {preview}")
    print(DIVIDER)
    if modified:
        print(f"  (* campos com alterações não salvas: {len(modified)})")
    print()


def main() -> None:
    engine = create_engine(DATABASE_URL)
    editor = _find_editor()
    if editor:
        print(f"[editor disponível: {editor}]")

    with engine.connect() as conn:
        if len(sys.argv) < 2:
            list_meditations(conn)
            print("Uso: python scripts/editar_meditacao.py DD/MM/YYYY")
            return

        data = sys.argv[1]
        row = conn.execute(
            text("SELECT * FROM meditacoes WHERE data = :data"),
            {"data": data},
        ).mappings().fetchone()

        if row is None:
            print(f"Nenhuma meditação encontrada para {data}.")
            sys.exit(1)

        record = dict(row)
        modified: set[str] = set()

        while True:
            show_record(record, modified)
            print("  Opções:")
            print("   [número]    editar campo")
            print("   v [número]  visualizar campo completo")
            print("   s           salvar alterações")
            print("   q           sair sem salvar")
            print()

            choice = input("Escolha: ").strip().lower()

            if choice == "q":
                if modified:
                    confirm = input("Há alterações não salvas. Deseja sair mesmo assim? (s/n): ").strip().lower()
                    if confirm != "s":
                        continue
                print("Saindo sem salvar.")
                break

            if choice == "s":
                if not modified:
                    print("Nenhuma alteração para salvar.")
                    continue
                updates = {col: record[col] for col, _ in FIELDS if col in record}
                set_clause = ", ".join(f"{col} = :{col}" for col in updates)
                conn.execute(
                    text(f"UPDATE meditacoes SET {set_clause} WHERE data = :data"),
                    {**updates, "data": data},
                )
                conn.commit()
                print(f"\n✓ {len(modified)} campo(s) salvos para {data}.")
                modified.clear()
                continue

            if choice.startswith("v ") and choice[2:].isdigit():
                idx = int(choice[2:]) - 1
                if 0 <= idx < len(FIELDS):
                    col, label = FIELDS[idx]
                    value = record.get(col, "") or "(vazio)"
                    print(f"\n{DIVIDER}")
                    print(f"  {label.strip()}")
                    print(DIVIDER)
                    print(value)
                    print(DIVIDER)
                else:
                    print("  Número de campo inválido.")
                continue

            if choice.isdigit() and 1 <= int(choice) <= len(FIELDS):
                idx = int(choice) - 1
                col, label = FIELDS[idx]
                current = record.get(col, "")

                if editor:
                    new_value = _edit_in_editor(current, editor)
                else:
                    new_value = _edit_inline(current, label)

                if new_value != current:
                    record[col] = new_value
                    modified.add(col)
                    print(f"  Campo '{label.strip()}' atualizado (não salvo ainda).")
                else:
                    print("  Nenhuma alteração detectada.")
                continue

            print("  Opção inválida.")


if __name__ == "__main__":
    main()
