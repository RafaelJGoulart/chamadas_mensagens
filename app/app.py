import base64
import hmac
import logging
import os
import secrets
import sys
from pathlib import Path

# Garante que imports irmãos (config, extensions, models...) funcionem
# independente de como o Python foi invocado (instalado vs. portátil/embeddable,
# CWD diferente, PYTHONSAFEPATH, python._pth isolado etc.).
sys.path.insert(0, str(Path(__file__).resolve().parent))

from flask import Flask, abort, request, session
from sqlalchemy import text

from config import Config, DATA_DIR
from extensions import db
import models  # noqa: F401  (registra os modelos no SQLAlchemy)
from models import Curso, Materia
from routes.cursos import cursos_bp
from routes.turmas import turmas_bp
from routes.alunos import alunos_bp
from routes.matriculas import matriculas_bp
from routes.chamadas import chamadas_bp
from routes.dashboard import dashboard_bp
from routes.contato import contato_bp
from routes.relatorio import relatorio_bp
from routes.importacao import importacao_bp
from routes.materias import materias_bp
from services.materias import MATERIAS_PADRAO_INFORMATICA, MATERIA_NEUTRA


def _secret_key_persistente():
    """Chave fixa por instalação, guardada fora do código (data/secret_key)."""
    chave_env = os.environ.get("SISTEMA_SECRET_KEY", "").strip()
    if chave_env:
        return chave_env
    arquivo = DATA_DIR / "secret_key"
    try:
        if arquivo.exists():
            conteudo = arquivo.read_text(encoding="utf-8").strip()
            if conteudo:
                return conteudo
        chave = secrets.token_urlsafe(48)
        arquivo.write_text(chave, encoding="utf-8")
        return chave
    except OSError:
        return "sistema-chamadas-fallback-local"


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["SECRET_KEY"] = _secret_key_persistente()

    db.init_app(app)

    app.register_blueprint(cursos_bp)
    app.register_blueprint(turmas_bp)
    app.register_blueprint(alunos_bp)
    app.register_blueprint(matriculas_bp)
    app.register_blueprint(chamadas_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(contato_bp)
    app.register_blueprint(relatorio_bp)
    app.register_blueprint(importacao_bp)
    app.register_blueprint(materias_bp)

    app.context_processor(_injetar_csrf)
    app.before_request(_validar_csrf)

    with app.app_context():
        try:
            db.create_all()
        except Exception:
            logging.exception("Falha ao inicializar o banco de dados")
        _garantir_colunas_telefone()
        _migrar_materias()
        _garantir_backfill_presencas()

    return app


def _injetar_csrf():
    return {
        "csrf_token": lambda: _token_csrf(),
    }


def _token_csrf():
    """Token CSRF gravado na sessão local (usuário único, sem login)."""
    if "_csrf" not in session:
        session["_csrf"] = base64.urlsafe_b64encode(secrets.token_bytes(24)).decode()
    return session["_csrf"]


def _validar_csrf():
    """Exige token CSRF em toda requisição POST (forms e fetch com X-CSRF-Token)."""
    if request.method != "POST":
        return None
    enviado = (
        request.form.get("csrf_token")
        or request.headers.get("X-CSRF-Token", "")
        or ""
    )
    esperado = session.get("_csrf", "")
    if not esperado or not hmac.compare_digest(enviado, esperado):
        abort(400)
    return None


def _garantir_colunas_telefone():
    """Migração idempotente: garante celular/comercial em bancos antigos.

    Bancos novos já nascem com as colunas via create_all().
    O número do antigo telefone_responsavel é copiado para celular
    (somente onde celular estiver vazio) para não perder contato.
    """
    try:
        with db.engine.begin() as conn:
            colunas = {
                linha[1]
                for linha in conn.exec_driver_sql("PRAGMA table_info(alunos)")
            }
            if "celular" not in colunas:
                conn.exec_driver_sql(
                    "ALTER TABLE alunos ADD COLUMN celular VARCHAR(30)"
                )
            if "comercial" not in colunas:
                conn.exec_driver_sql(
                    "ALTER TABLE alunos ADD COLUMN comercial VARCHAR(30)"
                )
            if "telefone_responsavel" in colunas:
                conn.exec_driver_sql(
                    "UPDATE alunos SET celular = telefone_responsavel "
                    "WHERE (celular IS NULL OR celular = '') "
                    "AND telefone_responsavel IS NOT NULL "
                    "AND telefone_responsavel != ''"
                )
    except Exception:
        logging.exception("Falha na migração das colunas de telefone")


def _migrar_materias():
    """Adiciona o conceito de matéria ao banco existente (idempotente).

    - Cria a coluna materia_id em chamadas (bancos antigos).
    - Cria o índice por data (buscas mensais).
    - Cria a matéria "Neutra" por curso e associa as chamadas sem matéria.
    - Faz o seed das matérias padrão do curso de Informática.
    """
    try:
        with db.engine.begin() as conn:
            colunas = {
                linha[1]
                for linha in conn.exec_driver_sql("PRAGMA table_info(chamadas)")
            }
            if "materia_id" not in colunas:
                conn.exec_driver_sql(
                    "ALTER TABLE chamadas ADD COLUMN materia_id INTEGER"
                )
            conn.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS ix_chamadas_data ON chamadas (data)"
            )
    except Exception:
        logging.exception("Falha na migração das colunas de chamadas")
        return

    try:
        cursos = Curso.query.order_by(Curso.nome).all()
        curso_informatica = next(
            (c for c in cursos if c.nome == "Informatica"), None
        )
        for curso in cursos:
            neutra = (
                Materia.query.filter_by(curso_id=curso.id, nome=MATERIA_NEUTRA)
                .first()
            )
            if neutra is None:
                neutra = Materia(curso_id=curso.id, nome=MATERIA_NEUTRA)
                db.session.add(neutra)
                db.session.flush()
            # Mesma conexão da sessão (o SQLite bloqueia escritor concorrente).
            db.session.execute(
                text(
                    "UPDATE chamadas SET materia_id = :mid "
                    "WHERE materia_id IS NULL "
                    "AND turma_id IN (SELECT id FROM turmas WHERE curso_id = :cid)"
                ),
                {"mid": neutra.id, "cid": curso.id},
            )
        # Matérias padrão SÓ no curso "Informatica" (os demais cursos nascem
        # só com a "Neutra"; o professor gerencia as matérias de cada um).
        if curso_informatica is not None:
            for nome in MATERIAS_PADRAO_INFORMATICA:
                existe = Materia.query.filter_by(
                    curso_id=curso_informatica.id, nome=nome
                ).first()
                if existe is None:
                    db.session.add(
                        Materia(curso_id=curso_informatica.id, nome=nome)
                    )
        db.session.commit()
    except Exception:
        db.session.rollback()
        logging.exception("Falha ao popular as matérias")


def _garantir_backfill_presencas():
    """Preenche ausência de alunos ativos em chamadas antigas (uma vez).

    Antes esse preenchimento acontecia dentro do GET da matriz; agora é feito
    aqui (e no cadastro de matrícula), mantendo o banco íntegro sem efeito
    colateral em leitura.
    """
    try:
        db.session.execute(
            text(
                "INSERT OR IGNORE INTO presencas (chamada_id, aluno_id, estado) "
                "SELECT c.id, m.aluno_id, 'ausente' "
                "FROM chamadas c "
                "JOIN matriculas m ON m.turma_id = c.turma_id AND m.ativa = 1 "
                "JOIN alunos a ON a.id = m.aluno_id AND a.status = 'ativo'"
            )
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        logging.exception("Falha no backfill de presenças")


app = create_app()


if __name__ == "__main__":
    debug = os.environ.get("SISTEMA_DEBUG", "1") == "1"
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=debug,
        use_reloader=False,
    )