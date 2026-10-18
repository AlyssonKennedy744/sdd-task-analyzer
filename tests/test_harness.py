"""Test Harness do TaskAnalyzer.

Traduz os cenários de aceite de ``specs/task_analyzer_spec.md`` (seção 2) em
testes automatizados com pytest. Execução: ``pytest -q`` na raiz do repositório.
"""

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.task_analyzer import (  # noqa: E402
    DatasInvalidasError,
    IndicadorPrioridade,
    SemTarefasConcluidasError,
    Tarefa,
    TaskValidationError,
    ValorEnumInvalidoError,
    analisar_tarefas,
    analyze_tasks,
)


def utc(hora: int, minuto: int = 0) -> datetime:
    """Retorna uma data de 01/09/2026 em UTC no horário informado."""
    return datetime(2026, 9, 1, hora, minuto, tzinfo=timezone.utc)


def tarefa(
    id_tarefa: int,
    prioridade: str,
    status: str,
    prazo: datetime,
    data_inicio: datetime | None = None,
    data_conclusao: datetime | None = None,
    data_criacao: datetime = utc(7),
) -> Tarefa:
    """Atalho para construir uma ``Tarefa`` nos testes."""
    return Tarefa(
        id_tarefa=id_tarefa,
        data_criacao=data_criacao,
        prazo=prazo,
        prioridade=prioridade,
        status=status,
        data_inicio=data_inicio,
        data_conclusao=data_conclusao,
    )


def como_dict(item: Tarefa) -> dict[str, Any]:
    """Converte uma ``Tarefa`` no formato de dicionário (datas em ISO 8601)."""
    return {
        campo: valor.isoformat() if isinstance(valor, datetime) else valor
        for campo, valor in vars(item).items()
    }


@pytest.fixture
def tarefas_referencia() -> list[Tarefa]:
    """Conjunto de dados de referência da seção 2.1 da spec."""
    return [
        tarefa(1, "alta", "concluida", utc(12), utc(8), utc(10)),
        tarefa(2, "alta", "concluida", utc(11), utc(9), utc(12)),
        tarefa(3, "media", "concluida", utc(9), utc(8), utc(8, 30)),
        tarefa(4, "baixa", "concluida", utc(8, 30), utc(8), utc(9)),
        tarefa(5, "media", "pendente", utc(18)),
        tarefa(6, "alta", "cancelada", utc(10), utc(7)),
    ]


@pytest.fixture
def tarefas_referencia_dict(tarefas_referencia: list[Tarefa]) -> list[dict[str, Any]]:
    """Mesmo conjunto de referência no formato de entrada de ``analyze_tasks``."""
    return [como_dict(item) for item in tarefas_referencia]


# ---------------------------------------------------------------- Cenário 1


def test_metricas_corretas_com_tarefas_validas(tarefas_referencia: list[Tarefa]) -> None:
    relatorio = analisar_tarefas(tarefas_referencia)

    assert relatorio.tempo_medio_conclusao_min == 97.50
    assert relatorio.taxa_atraso_percentual == 50.00
    assert relatorio.quantidade_tarefas == 4
    assert relatorio.indicadores_por_prioridade == {
        "alta": IndicadorPrioridade(150.00, 50.00, 2),
        "media": IndicadorPrioridade(30.00, 0.00, 1),
        "baixa": IndicadorPrioridade(60.00, 100.00, 1),
    }


def test_analyze_tasks_cenario_1_sucesso(tarefas_referencia_dict: list[dict[str, Any]]) -> None:
    resultado = analyze_tasks(tarefas_referencia_dict)

    assert resultado["total_tarefas"] == 6
    assert resultado["total_concluidas"] == 4
    assert resultado["total_pendentes"] == 1
    assert resultado["total_canceladas"] == 1
    assert resultado["tempo_medio_conclusao_min"] == 97.50
    assert resultado["tempo_medio_conclusao_horas"] == 1.62  # 97,5 / 60 = 1,625 -> round(x, 2)
    assert resultado["taxa_atraso_percentual"] == 50.00
    assert resultado["metricas_por_prioridade"] == {
        "baixa": {"total_concluidas": 1, "tempo_medio_conclusao_horas": 1.0, "taxa_atraso_percentual": 100.0},
        "media": {"total_concluidas": 1, "tempo_medio_conclusao_horas": 0.5, "taxa_atraso_percentual": 0.0},
        "alta": {"total_concluidas": 2, "tempo_medio_conclusao_horas": 2.5, "taxa_atraso_percentual": 50.0},
    }


# ---------------------------------------------------------------- Cenário 2


def test_datas_inconsistentes_disparam_excecao(tarefas_referencia: list[Tarefa]) -> None:
    invalida = tarefa(7, "media", "concluida", utc(12), data_inicio=utc(9), data_conclusao=utc(8))

    with pytest.raises(DatasInvalidasError, match=r"Tarefa 7") as erro:
        analisar_tarefas([*tarefas_referencia, invalida])

    assert "2026-09-01 08:00 UTC" in str(erro.value)
    assert "2026-09-01 09:00 UTC" in str(erro.value)


def test_analyze_tasks_conclusao_anterior_a_criacao() -> None:
    invalida = tarefa(
        8, "alta", "concluida", utc(18),
        data_criacao=utc(10), data_inicio=utc(10), data_conclusao=utc(8),
    )

    with pytest.raises(TaskValidationError, match=r"data_conclusao .* anterior a data_criacao"):
        analyze_tasks([como_dict(invalida)])


@pytest.mark.parametrize(
    "tarefas",
    [
        [],
        [tarefa(5, "media", "pendente", utc(18)), tarefa(6, "alta", "cancelada", utc(10))],
    ],
    ids=["lista_vazia", "apenas_pendentes_e_canceladas"],
)
def test_sem_tarefas_concluidas_dispara_excecao(tarefas: list[Tarefa]) -> None:
    with pytest.raises(SemTarefasConcluidasError, match=r"Nenhuma tarefa concluída válida"):
        analisar_tarefas(tarefas)


# ---------------------------------------------------------------- Casos de borda


@pytest.mark.parametrize(
    "tarefas",
    [
        [],
        [como_dict(tarefa(5, "media", "pendente", utc(18))), como_dict(tarefa(9, "baixa", "pendente", utc(20)))],
    ],
    ids=["lista_vazia", "apenas_pendentes"],
)
def test_analyze_tasks_casos_de_borda_retornam_zero(tarefas: list[dict[str, Any]]) -> None:
    resultado = analyze_tasks(tarefas)

    assert resultado["total_concluidas"] == 0
    assert resultado["total_pendentes"] == len(tarefas)
    assert resultado["tempo_medio_conclusao_horas"] == 0.0
    assert resultado["taxa_atraso_percentual"] == 0.0
    for metricas in resultado["metricas_por_prioridade"].values():
        assert metricas == {"total_concluidas": 0, "tempo_medio_conclusao_horas": 0.0, "taxa_atraso_percentual": 0.0}


# ---------------------------------------------------------------- Complementares


def test_conclusao_no_prazo_nao_e_atraso() -> None:
    no_prazo = tarefa(10, "alta", "concluida", prazo=utc(10), data_inicio=utc(8), data_conclusao=utc(10))

    relatorio = analisar_tarefas([no_prazo])

    assert relatorio.taxa_atraso_percentual == 0.0


def test_modo_tolerante_descarta_e_loga(
    tarefas_referencia: list[Tarefa], caplog: pytest.LogCaptureFixture
) -> None:
    invalida = tarefa(7, "media", "concluida", utc(12), data_inicio=utc(9), data_conclusao=utc(8))

    with caplog.at_level(logging.WARNING):
        relatorio = analisar_tarefas([*tarefas_referencia, invalida], ignorar_inconsistentes=True)

    assert any(r.levelno == logging.WARNING and "Tarefa 7" in r.getMessage() for r in caplog.records)
    assert relatorio.quantidade_tarefas == 4
    assert relatorio.tempo_medio_conclusao_min == 97.50


def test_prioridade_invalida() -> None:
    urgente = tarefa(2, "urgente", "concluida", utc(12), utc(8), utc(10))

    with pytest.raises(ValorEnumInvalidoError, match=r"Valores aceitos: baixa, media, alta"):
        analisar_tarefas([urgente])


def test_datetime_naive_e_rejeitado() -> None:
    naive = tarefa(11, "media", "concluida", utc(12), utc(8), datetime(2026, 9, 1, 10, 0))

    with pytest.raises(DatasInvalidasError, match=r"UTC timezone-aware"):
        analisar_tarefas([naive])


def test_prioridade_sem_tarefas_retorna_zeros() -> None:
    sem_baixa = [tarefa(1, "alta", "concluida", utc(12), utc(8), utc(10))]

    relatorio = analisar_tarefas(sem_baixa)

    assert relatorio.indicadores_por_prioridade["baixa"] == IndicadorPrioridade(0.0, 0.0, 0)
