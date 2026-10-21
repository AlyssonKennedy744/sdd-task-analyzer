# sdd-task-analyzer — TaskAnalyzer

> **Bootcamp III** — Fase 3 (Final): DevOps, Testes Automatizados, Containerização e Governança Ética de IA
> **Aluno:** Alysson Kennedy De Oliveira Carvalho — RA 22450680
> **Curso:** Ciência da Computação

[![CI](https://github.com/AlyssonKennedy744/sdd-task-analyzer/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/AlyssonKennedy744/sdd-task-analyzer/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Testes](https://img.shields.io/badge/pytest-13%20passed-brightgreen)
![Docker](https://img.shields.io/badge/docker-python%3A3.11--slim-2496ED)

## Visão geral

O **TaskAnalyzer** é um módulo Python desenvolvido com **SDD (Spec-Driven Development)**.
Ele recebe uma lista de tarefas (datas, prazo, prioridade e status) e calcula, sem persistência:

- tempo médio de conclusão (minutos e horas), geral e por prioridade;
- taxa de atraso percentual, geral e por prioridade;
- totais de tarefas, concluídas, pendentes e canceladas.

O código foi gerado com assistente de IA guiado por `CONTEXT_RULES.md` e pelo contrato
`specs/task_analyzer_spec.md`, e validado pelo Test Harness em `tests/test_harness.py`.
Na Fase 3 o projeto ganhou **pipeline de CI no GitHub Actions** e **execução isolada em Docker**,
de modo que os 13 testes rodam automaticamente a cada push/PR e com um único comando em qualquer máquina.

## Estrutura do repositório

```
sdd-task-analyzer/
├── .github/
│   └── workflows/
│       └── ci.yml                    # Motor CI/CD (GitHub Actions)
├── Dockerfile                        # Empacotamento (python:3.11-slim, usuário não-root)
├── docker-compose.yml                # Orquestração: docker compose run --rm tests
├── .dockerignore
├── CONTEXT_RULES.md                  # Base de governança da IA (Fase 1 + regras IN da Fase 3)
├── specs/
│   ├── system_design_document.pdf    # SDD consolidado (Fases 1 a 3)
│   ├── requirements.yaml             # Requisitos em formato estruturado
│   └── task_analyzer_spec.md         # Contrato executável (fonte da verdade)
├── tests/
│   └── test_harness.py               # Test Harness com pytest (13 testes)
├── src/
│   └── task_analyzer.py              # Código gerado via IA e homologado
├── .gitignore
├── requirements.txt                  # Dependências autorizadas (pytest)
└── README.md
```

## Como executar

### Opção 1 — Docker (recomendado)

Pré-requisito: Docker com Docker Compose v2.

```bash
git clone https://github.com/AlyssonKennedy744/sdd-task-analyzer.git
cd sdd-task-analyzer
docker compose run --rm tests
```

Ou, sem o Compose:

```bash
docker build -t sdd-task-analyzer .
docker run --rm sdd-task-analyzer
```

### Opção 2 — Local

Pré-requisitos: Python 3.11+ e Git.

```bash
python -m pip install -r requirements.txt
pytest tests/test_harness.py -v
```

Resultado esperado nas duas opções: `13 passed` (100 % de aprovação).

## Integração Contínua (GitHub Actions)

O workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) roda em todo `push` e `pull_request`
para `main` e `develop`:

| Job | Ambiente | Passos |
|-----|----------|--------|
| `test` | `ubuntu-latest` + Python 3.11 | checkout → `pip install -r requirements.txt` → `pytest tests/test_harness.py -v` |
| `docker` | `ubuntu-latest` (depende de `test`) | `docker build` → `docker compose run --rm tests` |

Nenhum PR é mesclado sem os dois jobs verdes (regra IN-01).

## Exemplo de uso

```python
from src.task_analyzer import analyze_tasks

resultado = analyze_tasks([
    {
        "id_tarefa": 1,
        "prioridade": "alta",
        "status": "concluida",
        "data_criacao": "2026-09-01T07:00:00Z",
        "data_inicio": "2026-09-01T08:00:00Z",
        "data_conclusao": "2026-09-01T10:00:00Z",
        "prazo": "2026-09-01T12:00:00Z",
    },
])
# {'total_tarefas': 1, 'total_concluidas': 1, 'total_pendentes': 0, ...,
#  'tempo_medio_conclusao_horas': 2.0, 'taxa_atraso_percentual': 0.0, ...}
```

Também está disponível a API tipada do contrato da Fase 1: `analisar_tarefas(list[Tarefa]) -> RelatorioMetricas`.

## Cobertura do Test Harness

| Cenário | O que é validado | Testes |
|---------|------------------|--------|
| Cenário 1 (sucesso) | `total_tarefas`, `total_concluidas`, `total_pendentes`, tempo médio (geral e por prioridade) e `taxa_atraso_percentual` | `test_metricas_corretas_com_tarefas_validas`, `test_analyze_tasks_cenario_1_sucesso` |
| Cenário 2 (erro) | `data_conclusao` < `data_criacao`/`data_inicio` dispara `TaskValidationError` / `DatasInvalidasError` | `test_datas_inconsistentes_disparam_excecao`, `test_analyze_tasks_conclusao_anterior_a_criacao` |
| Casos de borda | Lista vazia ou só pendentes: retorno `0.0` em `analyze_tasks`; `SemTarefasConcluidasError` em `analisar_tarefas` | `test_analyze_tasks_casos_de_borda_retornam_zero`, `test_sem_tarefas_concluidas_dispara_excecao` |
| C3 a C7 | Conclusão no prazo, modo tolerante com log, prioridade inválida, datetime naive, prioridade sem tarefas | demais testes |

## Governança de IA e rastreabilidade (RI-06)

| Arquivo | Origem | Revisão humana |
|---------|--------|----------------|
| `specs/task_analyzer_spec.md` | Humano (Fase 1), com adendo da Fase 2 | — |
| `CONTEXT_RULES.md` | Humano (Fase 1) | — |
| `src/task_analyzer.py` | Gerado por IA a partir da spec + CONTEXT_RULES | Conferência de assinaturas, tipos, exceções, arredondamento e logging |
| `tests/test_harness.py` | Cenários definidos pelo humano; código de teste sugerido pela IA | Conferência 1:1 com a seção 2 da spec (PR-02) |
| `.github/workflows/ci.yml` | Gerado por IA a partir do adendo 5.1 da spec | Gatilhos, versão do Python, comando exato do pytest, ausência de `continue-on-error` (IN-02) |
| `Dockerfile` / `docker-compose.yml` | Gerados por IA a partir do adendo 5.2 da spec | Imagem `python:3.11-slim`, usuário não-root, sem rede, FS somente leitura (IN-03/IN-04) |
| `specs/requirements.yaml` / `system_design_document.pdf` | Derivados da spec pelo humano com apoio da IA | Valores esperados conferidos com a seção 2 da spec |

Pontos da homologação:

- **Contrato preservado (PR-05/PR-10):** `analisar_tarefas` continua retornando `RelatorioMetricas`.
  A função `analyze_tasks` exigida pela Fase 2 foi adicionada como fachada, sem alterar a API original.
- **Hierarquia de exceções:** `TaskValidationError` é a base dos erros de entrada; `DatasInvalidasError`
  e `ValorEnumInvalidoError` derivam dela, então a mesma falha atende aos dois contratos.
- **Divisão por zero:** `analyze_tasks` retorna `0.0`; `analisar_tarefas` mantém o fail-fast da RN-05.
- **Sem dependências externas (PR-01)** e **sem `datetime.now()` (PR-11)**; logs via `logging` (DA-07).

## Fluxo de versionamento

`feature/*` → Pull Request → `develop` → Pull Request → `main`.
Tags: `v0.1.0` (Fase 2) e `v1.0.0` (Fase 3, com CI e Docker).
Commits no padrão Conventional Commits; merge somente com o workflow `CI` verde.
