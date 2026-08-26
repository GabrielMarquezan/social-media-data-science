import logging
from typing import Callable

import pandas as pd

from social_media.src.config import Config
from social_media.src.dependencies import Dependencies

logger = logging.getLogger(__name__)

Step = Callable[
    [dict[str, pd.DataFrame], Config, Dependencies], dict[str, pd.DataFrame]
]


def run_pipeline(
    steps: list[Step],
    dfs: dict[str, pd.DataFrame],
    config: Config,
    deps: Dependencies,
    *,
    progress_callback: Callable[[str], None] | None = None,
) -> dict[str, pd.DataFrame]:
    """Executa uma sequência de steps funcionais sobre um dicionário de DataFrames.

    Args:
        steps: Sequência de steps a executar.
        dfs: Dicionário inicial de DataFrames.
        config: Configuração da aplicação.
        deps: Dependências injetáveis.
        progress_callback: Callback opcional chamado com o nome de cada step
            antes de sua execução (usado pela interface web para progresso).
    """
    for step in steps:
        step_name = step.__name__
        if progress_callback is not None:
            progress_callback(step_name)
        shapes = {name: df.shape for name, df in dfs.items() if isinstance(df, pd.DataFrame)}
        logger.debug(
            "Iniciando step: %s",
            step_name,
            extra={"step": step_name, "shapes": shapes},
        )
        dfs = step(dfs, config, deps)
        new_shapes = {name: df.shape for name, df in dfs.items() if isinstance(df, pd.DataFrame)}
        logger.debug(
            "Step finalizado: %s",
            step_name,
            extra={"step": step_name, "shapes": new_shapes},
        )
    return dfs
