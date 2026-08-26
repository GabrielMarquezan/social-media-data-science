"""Testes da interface Streamlit usando o framework de testes do próprio Streamlit.

Os testes clicam apenas em cenários que não disparam a thread de execução
(entrada vazia ou inválida), portanto nenhuma chamada ao Apify é feita.
"""

from io import BytesIO
from pathlib import Path
from queue import Queue
from unittest.mock import MagicMock

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from social_media.src.ui.app import _df_to_xlsx_bytes

APP_PATH = Path(__file__).resolve().parents[2] / "app.py"
_DEFAULT_TIMEOUT = 120


def _run_app() -> AppTest:
    at = AppTest.from_file(str(APP_PATH), default_timeout=_DEFAULT_TIMEOUT)
    at.run()
    return at


def test_app_initial_render() -> None:
    at = _run_app()

    assert not at.exception
    assert at.sidebar.radio[0].label == "Navegação"
    assert len(at.text_area) == 1
    assert at.button(key="start_button").label == "Iniciar execução"
    assert at.session_state["run_status"] == "idle"


def test_app_rejects_empty_input() -> None:
    at = _run_app()

    at.button(key="start_button").click().run()

    assert not at.exception
    assert len(at.error) == 1
    assert "pelo menos uma URL" in at.error[0].value
    assert at.session_state["run_status"] == "idle"


def test_app_rejects_invalid_links_and_preserves_input() -> None:
    at = _run_app()

    invalid_text = "https://instagram.com/p/SEM-WWW/\nnão-é-url"
    at.text_area(key="links_input").set_value(invalid_text)
    at.button(key="start_button").click().run()

    assert not at.exception
    assert len(at.error) == 1
    assert "inválidas" in at.error[0].value
    assert at.session_state["run_status"] == "idle"
    # O texto digitado é preservado para o usuário corrigir e tentar de novo.
    assert at.session_state["links_input"] == invalid_text


def test_app_past_runs_view_renders() -> None:
    at = _run_app()

    at.sidebar.radio(key="nav").set_value("Execuções anteriores").run()

    assert not at.exception


def test_app_auto_switches_to_results_after_run(tmp_path: Path) -> None:
    """Simula uma execução concluída: a UI deve ir para Resultados sem exceção."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    at = _run_app()

    dead_thread = MagicMock()
    dead_thread.is_alive.return_value = False
    run_dir = tmp_path / "run-123"
    charts_dir = run_dir / "charts"
    charts_dir.mkdir(parents=True)

    # metrics.xlsx: habilita as abas de tabelas e os downloads XLSX por tabela
    with pd.ExcelWriter(run_dir / "metrics.xlsx", engine="openpyxl") as writer:
        pd.DataFrame({"id": [1, 2]}).to_excel(writer, sheet_name="Posts", index=False)
        pd.DataFrame({"termo": ["amo"], "relevância": [0.9]}).to_excel(
            writer, sheet_name="Termos_dos_Comentários", index=False
        )

    # PNGs válidos para exercitar a renderização dos gráficos em duas colunas
    for name in ("posts_by_type", "likes_comments_timeline", "top_posts_engagement"):
        fig, ax = plt.subplots()
        ax.plot([1, 2], [1, 2])
        fig.savefig(charts_dir / f"{name}.png")
        plt.close(fig)

    # CSV sem colunas ("\n"): simula execuções antigas de tópicos vazios —
    # a UI deve mostrar mensagem amigável em vez de quebrar (EmptyDataError).
    (run_dir / "comment_topics.csv").write_text("\n", encoding="utf-8")

    at.session_state["run_status"] = "running"
    at.session_state["run_thread"] = dead_thread
    at.session_state["run_queue"] = Queue()
    at.session_state["run_result"] = {"status": "success", "output_dir": str(run_dir)}
    at.session_state["current_run_id"] = "run-123"
    at.run()

    assert not at.exception
    assert at.session_state["run_status"] == "success"
    assert at.session_state["nav"] == "Resultados"
    assert at.session_state["pending_nav"] is None

    # Download XLSX por tabela (um botão por aba não vazia do metrics.xlsx)
    sheet_downloads = [
        btn for btn in at.download_button if btn.label.endswith("(.xlsx)")
    ]
    assert len(sheet_downloads) == 2  # Posts + Termos dos comentários


def test_df_to_xlsx_bytes_roundtrip() -> None:
    df = pd.DataFrame({"termo": ["amo", "linda"], "relevância": [0.9, 0.8]})

    data = _df_to_xlsx_bytes(df, "Termos_dos_Comentários")

    assert isinstance(data, bytes)
    loaded = pd.read_excel(BytesIO(data), sheet_name="Termos_dos_Comentários")
    pd.testing.assert_frame_equal(loaded, df)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
