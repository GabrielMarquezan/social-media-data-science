"""Interface web Streamlit para o pipeline de coleta de dados do Instagram.

Execute a partir da raiz do projeto com:

    streamlit run app.py
"""

import logging
import os
import time
from io import BytesIO
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
from typing import Any
from uuid import uuid4

os.environ.setdefault("MPLBACKEND", "Agg")

import pandas as pd
import streamlit as st

from social_media.src.config import build_config
from social_media.src.dependencies import build_dependencies
from social_media.src.ui.progress import (
    PHASE_ERROR,
    PHASE_EXPORT_COMPLETED,
    PHASE_EXTRACTION_COMPLETED,
    PHASE_EXTRACTION_STARTED,
    PHASE_FINISHED,
    PHASE_PIPELINE_STEP,
    ProgressEvent,
)
from social_media.src.ui.runner import start_run_in_thread
from social_media.src.ui.runs import (
    METRICS_FILENAME,
    RunInfo,
    get_run_info,
    list_runs,
    resolve_output_dir,
)
from social_media.src.ui.validation import (
    EXPECTED_FORMAT,
    find_invalid_links,
    parse_links,
)

logger = logging.getLogger(__name__)

_VIEW_NEW_RUN = "Nova execução"
_VIEW_RESULTS = "Resultados"
_VIEW_PAST_RUNS = "Execuções anteriores"
_VIEWS = [_VIEW_NEW_RUN, _VIEW_RESULTS, _VIEW_PAST_RUNS]

_PHASE_ICONS = {
    PHASE_EXTRACTION_STARTED: "🔄",
    PHASE_EXTRACTION_COMPLETED: "✅",
    PHASE_PIPELINE_STEP: "⚙️",
    PHASE_EXPORT_COMPLETED: "✅",
    PHASE_FINISHED: "🎉",
    PHASE_ERROR: "❌",
}

# Título da aba da UI -> nome da aba no metrics.xlsx
_KEY_SHEETS: dict[str, str] = {
    "Posts": "Posts",
    "Comentários": "Comentários",
    "Termos das legendas": "Termos_da_Legenda",
    "Termos dos comentários": "Termos_dos_Comentários",
    "Tópicos": "Tópicos_dos_Comentários",
    "Termos por sentimento": "Termos_por_Sentimento",
}

# Nome do arquivo PNG -> título amigável exibido na UI
_CHART_TITLES: dict[str, str] = {
    "likes_comments_timeline": "Curtidas e comentários ao longo do tempo",
    "top_posts_engagement": "Top posts por engajamento",
    "posts_by_type": "Posts por tipo",
    "caption_word_count_vs_engagement": "Palavras na legenda vs. comentários por curtida",
    "engagement_heatmap_hour_weekday": "Heatmap de comentários por curtida (hora × dia da semana)",
    "avg_likes_comments_by_weekday": "Média de curtidas e comentários por dia da semana",
}

_XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

_POLL_INTERVAL_SECONDS = 0.5


def _init_session_state() -> None:
    """Inicializa as chaves de estado da sessão usadas pela UI."""
    defaults: dict[str, Any] = {
        "nav": _VIEW_NEW_RUN,
        "pending_nav": None,
        "run_status": "idle",  # idle | running | success | error
        "run_events": [],
        "run_thread": None,
        "run_queue": None,
        "run_result": None,
        "current_run_id": None,
        "current_output_dir": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _start_run(links: list[str]) -> None:
    """Valida a configuração e inicia a execução em thread de fundo."""
    try:
        config = build_config()
    except ValueError as exc:
        st.error(f"Configuração inválida: {exc}")
        return

    run_id = str(uuid4())
    thread, events, result = start_run_in_thread(links, run_id, config)

    st.session_state.run_status = "running"
    st.session_state.run_events = []
    st.session_state.run_thread = thread
    st.session_state.run_queue = events
    st.session_state.run_result = result
    st.session_state.current_run_id = run_id
    st.session_state.current_output_dir = None

    logger.info(
        "Execução iniciada pela interface web.",
        extra={"run_id": run_id, "links_count": len(links)},
    )
    st.rerun()


def _drain_events() -> None:
    """Move os eventos pendentes da fila da thread para o estado da sessão."""
    queue: Queue[ProgressEvent] | None = st.session_state.run_queue
    if queue is None:
        return
    while True:
        try:
            event = queue.get_nowait()
        except Empty:
            break
        st.session_state.run_events.append(event)


def _render_progress() -> None:
    """Renderiza a lista de eventos de progresso acumulados."""
    for event in st.session_state.run_events:
        icon = _PHASE_ICONS.get(event.phase, "ℹ️")
        st.markdown(f"{icon} {event.message}")


def _finalize_run() -> None:
    """Encerra a execução atual e agenda a navegação para os resultados."""
    result: dict[str, Any] = st.session_state.run_result or {}
    if result.get("status") == "success":
        st.session_state.run_status = "success"
        st.session_state.current_output_dir = result.get("output_dir")
        # O radio com key="nav" já foi instanciado neste ciclo, então `nav`
        # não pode ser alterado agora. Agenda a troca para o próximo rerun.
        st.session_state.pending_nav = _VIEW_RESULTS
    else:
        st.session_state.run_status = "error"


def _render_new_run_view() -> None:
    """Visao de entrada de links e acompanhamento de progresso."""
    st.header("Nova execucao")
    st.caption("Cole uma URL de post ou reel do Instagram por linha.")
    st.info(
        "Dica: na primeira execucao, os modelos de IA sao baixados automaticamente. "
        "Use o botao 'Preparar modelos agora' na barra lateral para acelerar o processo.",
        icon="💡",
    )

    running = st.session_state.run_status == "running"

    st.text_area(
        "Links do Instagram",
        key="links_input",
        height=160,
        placeholder="https://www.instagram.com/p/ABC123/\nhttps://www.instagram.com/reel/DEF456/",
        disabled=running,
    )

    if st.button(
        "Iniciar execução",
        type="primary",
        disabled=running,
        key="start_button",
    ):
        links = parse_links(st.session_state.links_input)
        invalid = find_invalid_links(links)
        if not links:
            st.error("Cole pelo menos uma URL de post ou reel do Instagram.")
        elif invalid:
            st.error(
                "URLs inválidas encontradas. Formato esperado: "
                f"`{EXPECTED_FORMAT}`\n\n" + "\n".join(f"- `{link}`" for link in invalid)
            )
        else:
            _start_run(links)

    if st.session_state.run_status == "error":
        result: dict[str, Any] = st.session_state.run_result or {}
        st.error(
            "A execução falhou. Corrija o problema e tente novamente — "
            "os links foram mantidos acima."
        )
        if result.get("traceback"):
            with st.expander("Detalhes técnicos"):
                st.code(result["traceback"], language="text")

    if st.session_state.run_status == "success":
        st.success(
            f"Execução `{st.session_state.current_run_id}` concluída. "
            f"Veja a aba **{_VIEW_RESULTS}**."
        )

    if running:
        st.subheader("Progresso")
        _drain_events()
        _render_progress()
        thread: Thread | None = st.session_state.run_thread
        if thread is not None and not thread.is_alive():
            _drain_events()
            _finalize_run()
            st.rerun()
        with st.spinner("Execução em andamento..."):
            time.sleep(_POLL_INTERVAL_SECONDS)
        st.rerun()


def _read_sheet(xlsx_path: Path, sheet_name: str) -> pd.DataFrame | None:
    """Lê uma aba do XLSX, retornando None em caso de falha."""
    try:
        return pd.read_excel(xlsx_path, sheet_name=sheet_name)
    except (ValueError, OSError) as exc:
        logger.warning(
            "Falha ao ler aba do XLSX.",
            extra={"xlsx_path": str(xlsx_path), "sheet": sheet_name, "error": str(exc)},
        )
        return None


def _df_to_xlsx_bytes(df: pd.DataFrame, sheet_name: str) -> bytes:
    """Serializa um DataFrame como arquivo XLSX em memória (aba única)."""
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    return buffer.getvalue()


def _render_run_artifacts(run: RunInfo, key_prefix: str) -> None:
    """Renderiza downloads, tabelas e gráficos de uma execução."""
    st.code(str(run.path), language=None)

    if not run.complete:
        st.warning(
            "Execução incompleta — `metrics.xlsx` ou gráficos ausentes.",
            icon="⚠️",
        )

    col_posts, col_comments = st.columns(2)
    col_posts.metric(
        "Posts processados",
        run.posts_count if run.posts_count is not None else "—",
    )
    col_comments.metric(
        "Comentários processados",
        run.comments_count if run.comments_count is not None else "—",
    )

    if run.xlsx_path is not None:
        st.download_button(
            "Baixar metrics.xlsx",
            data=run.xlsx_path.read_bytes(),
            file_name=METRICS_FILENAME,
            mime=_XLSX_MIME,
            key=f"{key_prefix}_xlsx",
        )

        st.markdown("#### Tabelas")
        tabs = st.tabs(list(_KEY_SHEETS))
        for tab, (title, sheet_name) in zip(tabs, _KEY_SHEETS.items()):
            with tab:
                df = _read_sheet(run.xlsx_path, sheet_name)
                if df is None or df.empty:
                    st.info(f"Tabela '{title}' não disponível nesta execução.")
                else:
                    st.dataframe(df, use_container_width=True)
                    st.download_button(
                        f"Baixar {title} (.xlsx)",
                        data=_df_to_xlsx_bytes(df, sheet_name),
                        file_name=f"{sheet_name.lower()}.xlsx",
                        mime=_XLSX_MIME,
                        key=f"{key_prefix}_sheet_{sheet_name}",
                    )

    # CSVs só existem em execuções antigas (anteriores à exportação em XLSX)
    if run.csv_files:
        st.markdown("#### Arquivos CSV (formato antigo)")
        for csv_path in run.csv_files:
            with st.expander(csv_path.name):
                st.download_button(
                    f"Baixar {csv_path.name}",
                    data=csv_path.read_bytes(),
                    file_name=csv_path.name,
                    mime="text/csv",
                    key=f"{key_prefix}_{csv_path.stem}",
                )
                try:
                    st.dataframe(pd.read_csv(csv_path), use_container_width=True)
                except pd.errors.EmptyDataError:
                    # CSV gerado sem colunas (ex.: tópicos vazios de execuções
                    # anteriores à correção) — exibe mensagem em vez de quebrar.
                    st.info("Este CSV está vazio (sem dados nesta execução).")
                except (pd.errors.ParserError, UnicodeDecodeError, OSError) as exc:
                    st.warning(f"Não foi possível visualizar o CSV: {exc}")

    if run.chart_files:
        st.markdown("#### Gráficos")
        # Uma linha de colunas por par de gráficos: cada linha fica alinhada
        # pelo topo, independentemente da altura dos PNGs da linha anterior.
        for row_start in range(0, len(run.chart_files), 2):
            row = run.chart_files[row_start : row_start + 2]
            columns = st.columns(2)
            for column, chart_path in zip(columns, row):
                with column:
                    st.image(
                        str(chart_path),
                        caption=_CHART_TITLES.get(chart_path.stem, chart_path.stem),
                        use_container_width=True,
                    )


def _render_results_view() -> None:
    """Visão dos resultados da execução mais recente."""
    st.header("Resultados")

    run: RunInfo | None = None
    if st.session_state.current_output_dir:
        run = get_run_info(Path(st.session_state.current_output_dir))
    else:
        runs = list_runs(resolve_output_dir())
        if runs:
            run = runs[0]

    if run is None:
        st.info("Nenhuma execução concluída ainda. Inicie uma nova execução.")
        return

    st.markdown(f"**ID da execução:** `{run.run_id}`")
    _render_run_artifacts(run, key_prefix=f"latest_{run.run_id}")


def _render_past_runs_view() -> None:
    """Visão das execuções anteriores encontradas em disco."""
    st.header("Execuções anteriores")

    output_dir = resolve_output_dir()
    runs = list_runs(output_dir)
    if not runs:
        st.info(f"Nenhuma execução encontrada em `{output_dir}`.")
        return

    summary = pd.DataFrame(
        {
            "Execução": [run.run_id for run in runs],
            "Criada em": [run.created_at.strftime("%d/%m/%Y %H:%M:%S") for run in runs],
            "Posts": [run.posts_count for run in runs],
            "Comentários": [run.comments_count for run in runs],
            "Status": ["completa" if run.complete else "incompleta" for run in runs],
        }
    )
    st.dataframe(summary, use_container_width=True, hide_index=True)

    selected_id = st.selectbox(
        "Selecione uma execução para ver gráficos, tabelas e downloads:",
        options=[run.run_id for run in runs],
        key="past_run_select",
    )
    selected = next((run for run in runs if run.run_id == selected_id), None)
    if selected is not None:
        st.markdown(f"**ID da execução:** `{selected.run_id}`")
        _render_run_artifacts(selected, key_prefix=f"past_{selected.run_id}")


def _render_model_warmup() -> None:
    """Botao opcional na sidebar para pre-baixar modelos de IA."""
    with st.sidebar.expander("Modelos de IA"):
        st.caption(
            "Na primeira execucao, os modelos de sentimento, embeddings e topicos "
            "sao baixados automaticamente. Isso pode levar alguns minutos."
        )
        if st.button("Preparar modelos agora", key="warmup_models"):
            with st.spinner("Verificando modelos..."):
                try:
                    config = build_config()
                    deps = build_dependencies(config)
                    deps.get_sentiment_analyzer()
                    deps.get_spacy_nlp()
                    deps.get_embedding_model()
                    st.success("Modelos prontos!")
                except Exception as exc:
                    st.error(f"Falha ao preparar modelos: {exc}")


def main() -> None:
    """Ponto de entrada da interface web."""
    st.set_page_config(
        page_title="Extração e Análise",
        page_icon="📊",
        layout="wide",
    )
    _init_session_state()

    # Aplica navegação agendada ANTES de instanciar o radio com key="nav"
    # (o Streamlit não permite alterar o estado de um widget já instanciado).
    if st.session_state.pending_nav is not None:
        st.session_state.nav = st.session_state.pending_nav
        st.session_state.pending_nav = None

    st.sidebar.title("Coleta de Dados")
    view = st.sidebar.radio("Navegação", _VIEWS, key="nav")
    if st.session_state.run_status == "running":
        st.sidebar.info("Execução em andamento...")

    _render_model_warmup()

    if view == _VIEW_NEW_RUN:
        _render_new_run_view()
    elif view == _VIEW_RESULTS:
        _render_results_view()
    else:
        _render_past_runs_view()


if __name__ == "__main__":
    main()
