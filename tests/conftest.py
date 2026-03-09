"""
Fixtures compartilhadas para testes do GayATCU.

Utiliza SQLite in-memory com StaticPool conforme padrão oficial do SQLModel:
https://sqlmodel.tiangolo.com/tutorial/fastapi/tests
"""

import json
import os

import pytest
from sqlmodel import SQLModel, create_engine
from sqlmodel.pool import StaticPool

from db import import_topics_from_json


@pytest.fixture
def engine():
    """Cria engine SQLite in-memory com todas as tabelas do schema."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine


@pytest.fixture
def populated_engine(engine):
    """Engine com dados importados do conteudo.json real."""
    json_path = os.path.join(os.path.dirname(__file__), "..", "conteudo.json")
    import_topics_from_json(engine, json_path)
    return engine


@pytest.fixture
def sample_json(tmp_path):
    """Cria um arquivo JSON de teste mínimo."""
    data = [
        {
            "titulo": "Seção Teste A",
            "subsecoes": [
                {
                    "titulo": "Sub A1",
                    "topicos": [
                        {"codigo": "A1.1", "titulo": "Tópico A1.1"},
                        {"codigo": "A1.2", "titulo": "Tópico A1.2"},
                    ],
                }
            ],
        },
        {
            "titulo": "Seção Teste B",
            "subsecoes": [
                {
                    "titulo": "Sub B1",
                    "topicos": [
                        {"codigo": "B1.1", "titulo": "Tópico B1.1"},
                    ],
                }
            ],
        },
    ]
    path = tmp_path / "test_conteudo.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return str(path)
