from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent


def run_step(name: str, script_relative_path: str, stdin_text: str | None = None) -> None:
    script_path = ROOT_DIR / script_relative_path
    if not script_path.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado para a etapa '{name}': {script_path}")

    print(f"\n=== {name} ===")
    cmd = [sys.executable, str(script_path)]

    result = subprocess.run(
        cmd,
        text=True,
        input=stdin_text,
        cwd=str(ROOT_DIR),
    )
    if result.returncode != 0:
        raise RuntimeError(f"Etapa '{name}' falhou com codigo {result.returncode}.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Executa o pipeline completo: extracao, transformacao, carga e analise."
    )
    parser.add_argument(
        "--analise-opcao",
        default=None,
        help=(
            "Opcao do menu de analises para executar automaticamente no fim. "
            "Informe 1-6 para executar automaticamente, ou nao passe nada para modo interativo."
        ),
    )
    parser.add_argument(
        "--analise-interativa",
        action="store_true",
        help="Abre o menu de analises em modo interativo ao final (sem opcao automatica).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    run_step("Extracao", "etl/extracao.py")
    run_step("Transformacao", "etl/transformacao.py")
    run_step("Carga DW", "etl/carga_dw.py")

    if args.analise_interativa:
        run_step("Analise (menu interativo)", "analises/analises.py")
    else:
        selected_option = args.analise_opcao
        if selected_option is None:
            run_step("Analise", "analises/analises.py")
        else:
            selected_option = str(selected_option).strip()
            if selected_option not in {"1", "2", "3", "4", "5", "6"}:
                raise ValueError("A opcao de analise deve ser um numero entre 1 e 6.")
            run_step("Analise", "analises/analises.py", stdin_text=f"{selected_option}\n0\n")

    print("\nPipeline finalizado com sucesso.")


if __name__ == "__main__":
    main()
