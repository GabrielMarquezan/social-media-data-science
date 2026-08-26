"""Launcher standalone para o Coleta de Dados (Windows).

Este arquivo e o correspondente `coleta-dados.spec` sao usados pelo
PyInstaller para gerar um executavel Windows que inicia a interface
Streamlit com duplo clique.

O launcher:
- Garante que o modelo spaCy esteja instalado; se nao estiver, faz o
  download automaticamente.
- Inicia o Streamlit em segundo plano.
- Aguarda o servidor ficar disponivel.
- Abre o navegador padrao em http://localhost:8501.
- Mantem o processo vivo ate o usuario fechar a aplicacao.
"""

import os
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path


_STREAMLIT_PORT = 8501
_STREAMLIT_URL = f"http://127.0.0.1:{_STREAMLIT_PORT}"


def _resource_path(relative: str) -> Path:
    """Resolve caminho relativo dentro do bundle PyInstaller ou no codigo fonte."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    return base / relative


def _show_error(message: str) -> None:
    """Exibe uma messagebox nativa do Windows com o erro."""
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(0, message, "Coleta de Dados", 0x10)
    except Exception:
        # Fallback caso nao esteja no Windows ou ctypes falhe.
        print(message, file=sys.stderr)


def _ensure_spacy_model(model_name: str = "pt_core_news_sm") -> bool:
    """Verifica se o modelo spaCy esta disponivel; baixa se necessario.

    Returns:
        True se o modelo estiver disponivel ao final, False caso contrario.
    """
    try:
        import spacy

        spacy.load(model_name)
        return True
    except OSError:
        pass

    try:
        subprocess.run(
            [sys.executable, "-m", "spacy", "download", model_name],
            check=True,
        )
        import spacy

        spacy.load(model_name)
        return True
    except Exception as exc:
        _show_error(
            f"Nao foi possivel baixar o modelo spaCy '{model_name}'.\n\n{exc}"
        )
        return False


def _start_streamlit() -> subprocess.Popen:
    """Inicia o Streamlit apontando para app.py."""
    app_path = _resource_path("app.py")
    env = os.environ.copy()
    env["STREAMLIT_SERVER_HEADLESS"] = "true"
    env["STREAMLIT_SERVER_ADDRESS"] = "127.0.0.1"
    env["STREAMLIT_SERVER_PORT"] = str(_STREAMLIT_PORT)

    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(app_path),
            "--server.address=127.0.0.1",
            f"--server.port={_STREAMLIT_PORT}",
        ],
        env=env,
    )


def _wait_for_server(url: str = _STREAMLIT_URL, timeout: int = 60) -> bool:
    """Aguarda o servidor Streamlit responder."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1):
                return True
        except Exception:
            time.sleep(0.5)
    return False


def main() -> None:
    """Ponto de entrada do executavel."""
    if not _ensure_spacy_model():
        sys.exit(1)

    process = _start_streamlit()

    if _wait_for_server():
        webbrowser.open(_STREAMLIT_URL)
    else:
        _show_error(
            "A interface nao ficou pronta a tempo. "
            "Verifique se a porta 8501 ja esta em uso."
        )
        process.terminate()
        sys.exit(1)

    try:
        process.wait()
    except KeyboardInterrupt:
        process.terminate()


if __name__ == "__main__":
    main()
