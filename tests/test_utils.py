"""
Testes unitários para funções utilitárias (utils.py).
"""

import json

import pytest

from utils import INTERVALS, calculate_next_review, format_date, load_content


class TestCalculateNextReview:
    """Testes para cálculo de próximo intervalo SRS."""

    def test_success_level_0(self):
        """Nível 0 com sucesso → intervalo de 7 dias (nível 1)."""
        result = calculate_next_review(0, success=True)
        assert result == INTERVALS[1]  # 7

    def test_success_level_1(self):
        """Nível 1 com sucesso → intervalo de 15 dias."""
        result = calculate_next_review(1, success=True)
        assert result == INTERVALS[2]  # 15

    def test_success_level_2(self):
        """Nível 2 com sucesso → intervalo de 30 dias."""
        result = calculate_next_review(2, success=True)
        assert result == INTERVALS[3]  # 30

    def test_success_max_level(self):
        """Nível máximo (3+) com sucesso → mantém 30 dias."""
        result = calculate_next_review(3, success=True)
        assert result == INTERVALS[3]  # 30

    def test_failure_resets(self):
        """Falha em qualquer nível → reset para nível 0 (1 dia)."""
        for level in range(4):
            result = calculate_next_review(level, success=False)
            assert result == INTERVALS[0]  # 1

    def test_intervals_are_ordered(self):
        """Intervalos devem ser crescentes."""
        for i in range(len(INTERVALS) - 1):
            assert INTERVALS[i] < INTERVALS[i + 1]


class TestFormatDate:
    """Testes para formatação de datas."""

    def test_format_iso_date(self):
        """Deve formatar YYYY-MM-DD para DD/MM/YYYY."""
        result = format_date("2026-03-08")
        assert result == "08/03/2026"

    def test_format_iso_datetime(self):
        """Deve formatar ISO datetime extraindo apenas a data."""
        result = format_date("2026-03-08T22:30:00")
        assert result == "08/03/2026"

    def test_format_none(self):
        """None deve retornar string vazia."""
        result = format_date(None)
        assert result == ""

    def test_format_empty_string(self):
        """String vazia deve retornar string vazia."""
        result = format_date("")
        assert result == ""

    def test_format_invalid_date(self):
        """Data inválida deve retornar string vazia."""
        result = format_date("not-a-date")
        assert result == ""


class TestLoadContent:
    """Testes para carregamento e validação do JSON."""

    def test_load_valid_content(self, sample_json):
        """Deve carregar JSON válido com sucesso."""
        content = load_content(sample_json)
        assert isinstance(content, list)
        assert len(content) == 2

    def test_load_nonexistent_file(self):
        """Deve levantar FileNotFoundError para arquivo inexistente."""
        with pytest.raises(FileNotFoundError):
            load_content("/caminho/inexistente/arquivo.json")

    def test_load_invalid_json(self, tmp_path):
        """Deve levantar ValueError para JSON malformado."""
        path = tmp_path / "invalid.json"
        path.write_text("{invalid json}", encoding="utf-8")
        with pytest.raises(ValueError, match="Arquivo JSON inválido"):
            load_content(str(path))

    def test_load_non_list_json(self, tmp_path):
        """Deve levantar ValueError quando JSON não é lista."""
        path = tmp_path / "dict.json"
        path.write_text('{"key": "value"}', encoding="utf-8")
        with pytest.raises(ValueError, match="Esperado lista"):
            load_content(str(path))

    def test_load_section_without_titulo(self, tmp_path):
        """Deve levantar ValueError quando seção não tem 'titulo'."""
        data = [{"subsecoes": []}]
        path = tmp_path / "no_titulo.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        with pytest.raises(ValueError, match="titulo"):
            load_content(str(path))

    def test_load_empty_list(self, tmp_path):
        """Lista vazia deve ser aceita (com warning via logging)."""
        path = tmp_path / "empty.json"
        path.write_text("[]", encoding="utf-8")
        content = load_content(str(path))
        assert content == []
