#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gerenciador de Dados de Teste — Sistema de Chamadas

Ferramenta independente para popular o banco com dados fictícios,
resetar o banco para estado vazio e exibir resumo dos dados atuais.

Uso:
    python gerenciar_dados_teste.py
"""

import sys
import os
import random
from pathlib import Path
from datetime import date, timedelta
from typing import Optional, List, Dict, Any

# Adiciona o diretório raiz ao path para importar app
ROOT_DIR = Path(__file__).resolve().parent
APP_DIR = ROOT_DIR / "app"
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(APP_DIR))

# Muda para o diretório app para que imports relativos funcionem
os.chdir(APP_DIR)

from config import Config, DATA_DIR, BACKUPS_DIR
from extensions import db
import models  # noqa: F401
from models import (
    Curso,
    Turma,
    Aluno,
    Matricula,
    Chamada,
    Presenca,
    Contato,
    DIAS_SEMANA,
    STATUS_ALUNO,
    AUSENTE,
    FREQUENTE,
    REPOSICAO,
)
from flask import Flask


class GerenciadorDadosTeste:
    """Gerencia operações de dados de teste no banco SQLite."""

    # Prefixo para identificar dados de teste (não altera o schema)
    PREFIXO_TESTE = "[TESTE] "

    def __init__(self):
        self.app = self._criar_app()
        self.db_path = DATA_DIR / "sistema.db"
        self.backups_dir = BACKUPS_DIR

    def _criar_app(self) -> Flask:
        """Cria instância Flask com configuração do projeto."""
        app = Flask(__name__)
        app.config.from_object(Config)
        db.init_app(app)
        return app

    def _inicializar_banco(self) -> None:
        """Garante que as tabelas existam."""
        with self.app.app_context():
            db.create_all()

    def executar(self) -> None:
        """Loop principal do menu interativo."""
        self._inicializar_banco()

        while True:
            self._limpar_tela()
            self._exibir_cabecalho()
            self._exibir_menu()

            try:
                opcao = input("\nEscolha uma opção: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\nSaindo...")
                break

            if opcao == "1":
                self._popular_banco()
            elif opcao == "2":
                self._resetar_banco()
            elif opcao == "3":
                self._resetar_e_popular()
            elif opcao == "4":
                self._exibir_resumo()
            elif opcao == "0":
                print("\nSaindo...")
                break
            else:
                print("\nOpção inválida. Pressione Enter para continuar...")
                input()

    def _limpar_tela(self) -> None:
        os.system("cls" if os.name == "nt" else "clear")

    def _exibir_cabecalho(self) -> None:
        print("=" * 40)
        print(" GERENCIADOR DE DADOS DE TESTE")
        print("=" * 40)
        print(f"\nBanco encontrado:\n{self.db_path}")
        if self.db_path.exists():
            tamanho_kb = self.db_path.stat().st_size / 1024
            print(f"Tamanho: {tamanho_kb:.1f} KB")
        else:
            print("Status: Não existe (será criado na primeira operação)")

    def _exibir_menu(self) -> None:
        print("\nEscolha uma opção:")
        print()
        print("  1 - Popular banco com dados de teste")
        print("  2 - Resetar banco para zero")
        print("  3 - Resetar e popular (prático)")
        print("  4 - Exibir resumo dos dados")
        print("  0 - Sair")

    # ==================== OPERAÇÕES DE LEITURA ====================

    def _exibir_resumo(self) -> None:
        """Exibe contagem de registros por entidade."""
        self._limpar_tela()
        print("=" * 40)
        print(" RESUMO DOS DADOS NO BANCO")
        print("=" * 40)

        with self.app.app_context():
            contagens = {
                "Cursos": Curso.query.count(),
                "Turmas": Turma.query.count(),
                "Alunos": Aluno.query.count(),
                "Matrículas": Matricula.query.count(),
                "Chamadas": Chamada.query.count(),
                "Presenças": Presenca.query.count(),
                "Contatos": Contato.query.count(),
            }

            for entidade, count in contagens.items():
                print(f"  {entidade:<15}: {count}")

            # Informa quais tabelas não existem (para compatibilidade)
            print("\nPressione Enter para voltar ao menu...")
            input()

    # ==================== POPULAÇÃO ====================

    def _popular_banco(self) -> None:
        """Popula o banco com dados de teste variados."""
        self._limpar_tela()
        print("=" * 40)
        print(" POPULANDO BANCO COM DADOS DE TESTE")
        print("=" * 40)
        print()

        with self.app.app_context():
            try:
                # Verifica se já existem dados de teste
                ja_existem = self._verificar_dados_teste_existentes()
                if ja_existem:
                    print("[!] Dados de teste já existem no banco.")
                    resp = input("Deseja adicionar mais dados de teste? (s/N): ").strip().lower()
                    if resp != "s":
                        print("Operação cancelada.")
                        input("\nPressione Enter para voltar...")
                        return

                print("\nCriando dados de teste...")
                resultados = self._criar_dados_teste()

                print("\n[OK] População concluída com sucesso!")
                print("\nRegistros criados:")
                for entidade, qtd in resultados.items():
                    print(f"  {entidade:<15}: {qtd}")

            except Exception as e:
                print(f"\n[ERRO] Erro durante população: {e}")
                import traceback
                traceback.print_exc()

        print("\nPressione Enter para voltar ao menu...")
        input()

    def _verificar_dados_teste_existentes(self) -> bool:
        """Verifica se já existem dados de teste (pelo prefixo nos nomes)."""
        cursos_teste = Curso.query.filter(Curso.nome.like(f"{self.PREFIXO_TESTE}%")).count()
        return cursos_teste > 0

    def _criar_dados_teste(self) -> Dict[str, int]:
        """Cria todos os dados de teste e retorna contagens."""
        contadores = {
            "Cursos": 0,
            "Turmas": 0,
            "Alunos": 0,
            "Matrículas": 0,
            "Chamadas": 0,
            "Presenças": 0,
            "Contatos": 0,
        }

        # 1. Cursos
        cursos = self._criar_cursos()
        contadores["Cursos"] = len(cursos)

        # 2. Turmas
        turmas = self._criar_turmas(cursos)
        contadores["Turmas"] = len(turmas)

        # 3. Alunos
        alunos = self._criar_alunos()
        contadores["Alunos"] = len(alunos)

        # 4. Matrículas
        matriculas = self._criar_matriculas(alunos, turmas)
        contadores["Matrículas"] = len(matriculas)

        # 5. Chamadas
        chamadas = self._criar_chamadas(turmas)
        contadores["Chamadas"] = len(chamadas)

        # 6. Presenças
        presencas = self._criar_presencas(chamadas, matriculas)
        contadores["Presenças"] = len(presencas)

        # 7. Contatos
        contatos = self._criar_contatos(alunos)
        contadores["Contatos"] = len(contatos)

        db.session.commit()
        return contadores

    def _criar_cursos(self) -> List[Curso]:
        """Cria cursos de teste."""
        cursos_dados = [
            ("Informática Básica", "Curso introdutório de informática"),
            ("Excel e Power BI", "Planilhas avançadas e visualização de dados"),
            ("Desenvolvimento Web", "HTML, CSS, JavaScript e frameworks modernos"),
            ("Python para Iniciantes", "Lógica de programação com Python"),
            ("Redes de Computadores", "Fundamentos de redes e protocolos"),
        ]

        cursos = []
        for nome, desc in cursos_dados:
            nome_teste = f"{self.PREFIXO_TESTE}{nome}"
            curso = Curso.query.filter_by(nome=nome_teste).first()
            if not curso:
                curso = Curso(nome=nome_teste, descricao=desc)
                db.session.add(curso)
            cursos.append(curso)

        db.session.flush()
        return cursos

    def _criar_turmas(self, cursos: List[Curso]) -> List[Turma]:
        """Cria turmas variadas associadas aos cursos."""
        from datetime import time

        turmas_dados = [
            # (nome, curso_idx, dia_semana, inicio, fim, ativa)
            ("Turma Manhã A", 0, "segunda", time(8, 0), time(10, 0), True),
            ("Turma Tarde A", 0, "terca", time(14, 0), time(16, 0), True),
            ("Turma Noite A", 0, "quarta", time(19, 0), time(21, 0), True),
            ("Turma Excel Manhã", 1, "quinta", time(8, 0), time(11, 0), True),
            ("Turma Excel Noite", 1, "sexta", time(18, 30), time(21, 30), True),
            ("Turma Web Manhã", 2, "segunda", time(8, 0), time(11, 0), True),
            ("Turma Web Tarde", 2, "terca", time(14, 0), time(17, 0), True),
            ("Turma Web Sábado", 2, "sabado", time(9, 0), time(12, 0), True),
            ("Turma Python Noite", 3, "quarta", time(19, 0), time(22, 0), True),
            ("Turma Redes Tarde", 4, "quinta", time(14, 0), time(17, 0), False),  # inativa
        ]

        turmas = []
        for nome, curso_idx, dia, ini, fim, ativa in turmas_dados:
            nome_teste = f"{self.PREFIXO_TESTE}{nome}"
            turma = Turma.query.filter_by(nome=nome_teste).first()
            if not turma:
                turma = Turma(
                    nome=nome_teste,
                    curso_id=cursos[curso_idx].id,
                    dia_semana=dia,
                    horario_inicio=ini,
                    horario_fim=fim,
                    ativa=ativa,
                )
                db.session.add(turma)
            turmas.append(turma)

        db.session.flush()
        return turmas

    def _criar_alunos(self) -> List[Aluno]:
        """Cria 20 alunos variados com diferentes perfis."""
        from datetime import date

        # Lista de alunos com perfis variados
        alunos_dados = [
            # (nome, telefone, celular, comercial, responsavel, status, flag_coord, data_matricula_offset)
            ("Ana Souza", "(11) 99999-0001", "(11) 99999-0002", "(11) 3333-0001", "Maria Souza", "ativo", False, -30),
            ("Bruno Oliveira", "(11) 99999-0003", "(11) 99999-0004", "(11) 3333-0002", "José Oliveira", "ativo", False, -25),
            ("Carla Mendes", "(11) 99999-0005", None, None, None, "ativo", True, -20),  # flag coordenacao
            ("Diego Santos", None, "(11) 99999-0006", "(11) 3333-0004", "Ana Santos", "ativo", False, -15),
            ("Elisa Ferreira", "(11) 99999-0007", "(11) 99999-0008", None, "Carlos Ferreira", "ativo", False, -10),
            ("Felipe Costa", "(11) 99999-0009", "(11) 99999-0010", "(11) 3333-0006", "Lucia Costa", "ativo", False, -5),
            ("Gabriela Lima", "(11) 99999-0011", None, None, None, "inativo", False, -30),  # inativo
            ("Henrique Alves", "(11) 99999-0012", "(11) 99999-0013", "(11) 3333-0008", "Paulo Alves", "ativo", True, -20),  # flag
            ("Isabela Rocha", "(11) 99999-0014", "(11) 99999-0015", None, "Sandra Rocha", "ativo", False, -10),
            ("João Pereira", "(11) 99999-0016", None, "(11) 3333-0010", None, "ativo", False, -5),
            ("Karen Dias", "(11) 99999-0017", "(11) 99999-0018", "(11) 3333-0011", "Roberto Dias", "ativo", False, -30),
            ("Lucas Martins", None, None, None, None, "ativo", False, -15),  # sem telefones
            ("Mariana Nunes", "(11) 99999-0019", "(11) 99999-0020", "(11) 3333-0013", "Fernanda Nunes", "inativo", False, -10),  # inativa
            ("Nathan Cardoso", "(11) 99999-0021", "(11) 99999-0022", None, "Ricardo Cardoso", "ativo", True, -5),  # flag
            ("Olívia Ribeiro", "(11) 99999-0023", "(11) 99999-0024", "(11) 3333-0015", "Adriana Ribeiro", "ativo", False, -20),
            ("Pedro Gonçalves", "(11) 99999-0025", None, "(11) 3333-0016", None, "ativo", False, -10),
            ("Renata Barbosa", "(11) 99999-0026", "(11) 99999-0027", None, "Cláudia Barbosa", "ativo", False, -5),
            ("Samuel Teixeira", "(11) 99999-0028", "(11) 99999-0029", "(11) 3333-0018", "Marcos Teixeira", "ativo", True, -30),  # flag
            ("Tatiane Melo", "(11) 99999-0030", None, None, None, "ativo", False, -15),
            ("Vinícius Araújo", "(11) 99999-0031", "(11) 99999-0032", "(11) 3333-0020", "Patrícia Araújo", "inativo", True, -10),  # inativo + flag
        ]

        alunos = []
        hoje = date.today()
        for nome, tel, cel, com, resp, status, flag, offset in alunos_dados:
            nome_teste = f"{self.PREFIXO_TESTE}{nome}"
            aluno = Aluno.query.filter_by(nome=nome_teste).first()
            if not aluno:
                aluno = Aluno(
                    nome=nome_teste,
                    telefone=tel,
                    celular=cel,
                    comercial=com,
                    responsavel=resp,
                    data_matricula=hoje + timedelta(days=offset),
                    status=status,
                    flag_coordenacao=flag,
                )
                db.session.add(aluno)
            alunos.append(aluno)

        db.session.flush()
        return alunos

    def _criar_matriculas(self, alunos: List[Aluno], turmas: List[Turma]) -> List[Matricula]:
        """Cria matrículas variadas: alunos em 1 ou mais turmas, ativas e encerradas."""
        from datetime import date

        # Mapeia alunos ativos para distribuir
        alunos_ativos = [a for a in alunos if a.status == "ativo"]
        turmas_ativas = [t for t in turmas if t.ativa]

        matriculas = []
        hoje = date.today()

        # Cada aluno ativo matriculado em 1 a 3 turmas ativas
        for i, aluno in enumerate(alunos_ativos):
            # Define quantas turmas (1 a 3)
            num_turmas = 1 + (i % 3)
            turmas_aluno = turmas_ativas[i:i + num_turmas] if i + num_turmas <= len(turmas_ativas) else turmas_ativas[:num_turmas]

            for j, turma in enumerate(turmas_aluno):
                # Verifica se já existe matrícula
                matricula = Matricula.query.filter_by(aluno_id=aluno.id, turma_id=turma.id).first()
                if not matricula:
                    # Algumas matrículas encerradas (antigas)
                    ativa = True
                    data_fim = None
                    if j == 2 and i % 2 == 0:  # Terceira matrícula de alunos pares = encerrada
                        ativa = False
                        data_fim = hoje - timedelta(days=30)

                    matricula = Matricula(
                        aluno_id=aluno.id,
                        turma_id=turma.id,
                        data_inicio=aluno.data_matricula,
                        data_fim=data_fim,
                        ativa=ativa,
                    )
                    db.session.add(matricula)
                matriculas.append(matricula)

        # Alunos inativos sem matrícula (para testar listagem)
        # Alunos com flag_coordenacao já incluídos acima

        db.session.flush()
        return matriculas

    def _criar_chamadas(self, turmas: List[Turma]) -> List[Chamada]:
        """Cria chamadas em datas variadas (meses atuais e anteriores)."""
        from datetime import date

        hoje = date.today()
        chamadas = []

        # Gera chamadas para os últimos 3 meses
        for mes_offset in range(3):
            mes_base = hoje.month - mes_offset
            ano_base = hoje.year
            if mes_base <= 0:
                mes_base += 12
                ano_base -= 1

            # Para cada turma ativa, cria 2-4 chamadas no mês
            for turma in turmas:
                if not turma.ativa:
                    continue

                # Dias da semana da turma para dias reais
                dias_semana_idx = DIAS_SEMANA.index(turma.dia_semana)

                # Cria 2 a 4 chamadas no mês
                num_chamadas = 2 + (turma.id % 3)
                for k in range(num_chamadas):
                    # Calcula data aproximada
                    dia = 1 + (k * 7) + (turma.id * 2) % 7
                    if dia > 28:
                        dia = 28

                    try:
                        data_chamada = date(ano_base, mes_base, dia)
                    except ValueError:
                        continue

                    # Não criar chamadas futuras
                    if data_chamada > hoje:
                        continue

                    nome_teste = f"{self.PREFIXO_TESTE}{turma.nome} - {data_chamada.strftime('%d/%m/%Y')}"
                    chamada = Chamada.query.filter_by(turma_id=turma.id, data=data_chamada).first()
                    if not chamada:
                        conteudos = [
                            "Aula introdutória e apresentação do curso",
                            "Revisão de conceitos básicos",
                            "Exercícios práticos em laboratório",
                            "Prova teórica",
                            "Projeto prático em grupo",
                            "Revisão para avaliação final",
                        ]
                        chamada = Chamada(
                            turma_id=turma.id,
                            data=data_chamada,
                            conteudo=conteudos[k % len(conteudos)],
                            observacao="Chamada de teste gerada automaticamente",
                        )
                        db.session.add(chamada)
                    chamadas.append(chamada)

        db.session.flush()
        return chamadas

    def _criar_presencas(self, chamadas: List[Chamada], matriculas: List[Matricula]) -> List[Presenca]:
        """Cria presenças variadas para testar cenários de frequência."""
        import random

        # Agrupa matrículas por turma
        matriculas_por_turma: Dict[int, List[Matricula]] = {}
        for m in matriculas:
            if m.ativa:
                matriculas_por_turma.setdefault(m.turma_id, []).append(m)

        presencas = []
        random.seed(42)  # Reprodutível

        for chamada in chamadas:
            matriculas_turma = matriculas_por_turma.get(chamada.turma_id, [])
            if not matriculas_turma:
                continue

            for matricula in matriculas_turma:
                # Verifica se já existe presença
                presenca = Presenca.query.filter_by(
                    chamada_id=chamada.id,
                    aluno_id=matricula.aluno_id
                ).first()
                if presenca:
                    presencas.append(presenca)
                    continue

                # Define estado baseado em cenários de teste
                # Usa aluno_id para determinismo
                aluno_id = matricula.aluno_id
                idx = aluno_id % 10

                # Cenários específicos para testar regras:
                # - Aluno 1 (idx 1): 100% frequente
                # - Aluno 2 (idx 2): 75% frequente
                # - Aluno 3 (idx 3): 50% exato (limite)
                # - Aluno 4 (idx 4): 33% (abaixo)
                # - Aluno 5 (idx 5): 0% (todas ausente)
                # - Aluno 6 (idx 6): misto com reposição
                # - Outros: aleatório

                if idx == 1:
                    estado = FREQUENTE
                elif idx == 2:
                    estado = FREQUENTE if random.random() > 0.25 else AUSENTE
                elif idx == 3:
                    estado = FREQUENTE if random.random() > 0.5 else AUSENTE
                elif idx == 4:
                    estado = FREQUENTE if random.random() > 0.67 else AUSENTE
                elif idx == 5:
                    estado = AUSENTE
                elif idx == 6:
                    estado = random.choice([FREQUENTE, REPOSICAO, AUSENTE])
                else:
                    estado = random.choice([FREQUENTE, AUSENTE, REPOSICAO])

                presenca = Presenca(
                    chamada_id=chamada.id,
                    aluno_id=matricula.aluno_id,
                    estado=estado,
                    observacao="Presença de teste" if estado == REPOSICAO else None,
                )
                db.session.add(presenca)
                presencas.append(presenca)

        db.session.flush()
        return presencas

    def _criar_contatos(self, alunos: List[Aluno]) -> List[Contato]:
        """Cria alguns contatos de teste."""
        from datetime import date

        contatos = []
        hoje = date.today()

        # Tipos de contato variados
        tipos_contato = [
            ("Telefone mãe", "Contato com a mãe"),
            ("Telefone pai", "Contato com o pai"),
            ("Telefone avó", "Contato com a avó"),
            ("Responsável legal", "Contato com responsável"),
            ("Outro contato", "Outro responsável"),
        ]

        for i, aluno in enumerate(alunos[:10]):  # Apenas primeiros 10 alunos
            num_contatos = 1 + (i % 3)
            for j in range(num_contatos):
                tipo, desc = tipos_contato[(i + j) % len(tipos_contato)]
                data_contato = hoje - timedelta(days=random.randint(1, 60))

                contato = Contato(
                    aluno_id=aluno.id,
                    data=data_contato,
                    tipo=f"{self.PREFIXO_TESTE}{tipo}",
                    descricao=f"{self.PREFIXO_TESTE}{desc} - {aluno.nome}",
                )
                db.session.add(contato)
                contatos.append(contato)

        db.session.flush()
        return contatos

    # ==================== RESET ====================

    def _resetar_banco(self) -> None:
        """Reseta o banco (apaga dados, preserva estrutura) com backup prévio."""
        self._limpar_tela()
        print("=" * 40)
        print(" RESETAR BANCO DE DADOS")
        print("=" * 40)
        print()
        print("[!]  ATENÇÃO: Esta operação é DESTRUTIVA!")
        print(f"   Banco: {self.db_path}")
        print("   TODOS os registros serão apagados.")
        print("   A estrutura das tabelas será preservada.")
        print()

        # Confirmação explícita
        confirmacao = input("Digite 'RESETAR' para confirmar: ").strip()
        if confirmacao != "RESETAR":
            print("\nOperação cancelada (confirmação incorreta).")
            input("\nPressione Enter para voltar...")
            return

        # Backup antes de resetar
        if self.db_path.exists():
            backup_path = self._criar_backup()
            print(f"\n[OK] Backup criado: {backup_path}")
        else:
            print("\nℹ Banco não existe, nada para fazer backup.")

        # Apaga dados respeitando FKs (ordem reversa de dependência)
        with self.app.app_context():
            try:
                print("\nLimpando tabelas...")

                # Ordem: presencas -> chamadas -> matriculas -> contatos -> alunos -> turmas -> cursos
                db.session.query(Presenca).delete()
                db.session.query(Chamada).delete()
                db.session.query(Matricula).delete()
                db.session.query(Contato).delete()
                db.session.query(Aluno).delete()
                db.session.query(Turma).delete()
                db.session.query(Curso).delete()

                db.session.commit()
                print("[OK] Banco resetado com sucesso! Estrutura preservada.")

            except Exception as e:
                db.session.rollback()
                print(f"\n[ERRO] Erro ao resetar: {e}")
                import traceback
                traceback.print_exc()

        print("\nPressione Enter para voltar ao menu...")
        input()

    def _criar_backup(self) -> Path:
        """Cria backup do banco na pasta backups com timestamp."""
        from datetime import datetime

        self.backups_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        backup_path = self.backups_dir / f"sistema_{timestamp}.db"

        import shutil
        shutil.copy2(self.db_path, backup_path)

        return backup_path

    def _resetar_e_popular(self) -> None:
        """Reset + população em uma operação."""
        self._limpar_tela()
        print("=" * 40)
        print(" RESETAR E POPULAR")
        print("=" * 40)
        print()
        print("Esta operação vai:")
        print("  1. Criar backup do banco atual")
        print("  2. Apagar TODOS os dados")
        print("  3. Popular com dados de teste novos")
        print()

        confirmacao = input("Digite 'RESETAR' para confirmar: ").strip()
        if confirmacao != "RESETAR":
            print("\nOperação cancelada.")
            input("\nPressione Enter para voltar...")
            return

        # Backup
        if self.db_path.exists():
            backup_path = self._criar_backup()
            print(f"\n[OK] Backup criado: {backup_path}")

        # Reset
        with self.app.app_context():
            try:
                db.session.query(Presenca).delete()
                db.session.query(Chamada).delete()
                db.session.query(Matricula).delete()
                db.session.query(Contato).delete()
                db.session.query(Aluno).delete()
                db.session.query(Turma).delete()
                db.session.query(Curso).delete()
                db.session.commit()
                print("[OK] Dados apagados.")
            except Exception as e:
                db.session.rollback()
                print(f"[ERRO] Erro no reset: {e}")
                input("\nPressione Enter para voltar...")
                return

        # Popula
        print("\nPopulando com dados de teste...")
        with self.app.app_context():
            try:
                resultados = self._criar_dados_teste()
                print("\n[OK] Reset e população concluídos!")
                print("\nResumo final:")
                for entidade, qtd in resultados.items():
                    print(f"  {entidade:<15}: {qtd}")
            except Exception as e:
                print(f"\n[ERRO] Erro na população: {e}")
                import traceback
                traceback.print_exc()

        print("\nPressione Enter para voltar ao menu...")
        input()


def main():
    """Ponto de entrada principal."""
    try:
        gerenciador = GerenciadorDadosTeste()
        gerenciador.executar()
    except Exception as e:
        print(f"\nErro fatal: {e}")
        import traceback
        traceback.print_exc()
        input("\nPressione Enter para sair...")


if __name__ == "__main__":
    main()