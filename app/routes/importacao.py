import os
import tempfile
from pathlib import Path

from flask import (
    Blueprint,
    current_app,
    flash,
    render_template,
    request,
)

from services.importacao_excel import importar

importacao_bp = Blueprint("importacao", __name__)


def _arquivo_valido(upload):
    if upload is None or not upload.filename:
        return False
    return upload.filename.lower().endswith(".xlsx")


@importacao_bp.route("/importacao")
def listar():
    return render_template("importacao/listar.html", resultado=None)


@importacao_bp.route("/importacao", methods=["POST"])
def processar():
    cadastro = request.files.get("cadastro")
    chamadas = request.files.get("chamadas")

    if not _arquivo_valido(cadastro):
        flash("Selecione o arquivo de cadastro (Export_F10.xlsx).", "erro")
        return render_template("importacao/listar.html", resultado=None)
    if not _arquivo_valido(chamadas):
        flash("Selecione o arquivo de chamadas (Export_F10 - Chamadas.xlsx).", "erro")
        return render_template("importacao/listar.html", resultado=None)

    pasta = Path(tempfile.mkdtemp(prefix="importacao_"))
    try:
        caminho_cadastro = pasta / "cadastro.xlsx"
        caminho_chamadas = pasta / "chamadas.xlsx"
        cadastro.save(caminho_cadastro)
        chamadas.save(caminho_chamadas)

        resultado = importar(caminho_cadastro, caminho_chamadas)
        flash(
            "Importação concluída: todos os dados antigos foram substituídos.",
            "sucesso",
        )
        return render_template(
            "importacao/listar.html", resultado=resultado
        )
    except Exception as exc:
        current_app.logger.exception("Falha ao importar planilhas")
        flash(
            f"Não foi possível importar: {exc}",
            "erro",
        )
        return render_template("importacao/listar.html", resultado=None)
    finally:
        try:
            for arquivo in pasta.iterdir():
                arquivo.unlink(missing_ok=True)
            pasta.rmdir()
        except OSError:
            pass