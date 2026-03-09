"""
Testes unitários para a camada de banco de dados (db.py).

Cada teste utiliza SQLite in-memory via fixture `engine` para
isolamento total entre execuções.
"""

from datetime import datetime, timedelta

from sqlmodel import Session

from db import (
    Progress,
    Topic,
    export_all_progress_to_dict,
    get_all_progress,
    get_detailed_statistics_by_section,
    get_statistics,
    get_topic_distribution_by_section,
    get_topic_progress,
    get_topics_due_for_review,
    get_upcoming_reviews,
    get_weekly_review_data,
    import_topics_from_json,
    mark_review_complete,
    mark_topic_complete,
    unmark_topic_complete,
)


class TestImportTopics:
    """Testes para importação de tópicos do JSON."""

    def test_import_topics_from_json(self, engine, sample_json):
        """Deve importar 3 tópicos do JSON de teste."""
        count = import_topics_from_json(engine, sample_json)
        assert count == 3

    def test_import_idempotent(self, engine, sample_json):
        """Importar duas vezes não deve duplicar tópicos."""
        first = import_topics_from_json(engine, sample_json)
        second = import_topics_from_json(engine, sample_json)
        assert first == 3
        assert second == 0

    def test_import_real_data(self, populated_engine):
        """Deve importar dados reais do conteudo.json."""
        with Session(populated_engine) as session:
            from sqlalchemy import func
            from sqlmodel import select

            count = session.exec(select(func.count(Topic.id))).first()
            assert count is not None
            assert count > 300  # O banco deve ter ~344 tópicos


class TestMarkTopicComplete:
    """Testes para marcação de tópicos como concluídos."""

    def test_mark_topic_complete(self, engine, sample_json):
        """Deve marcar tópico e definir next_review_date."""
        import_topics_from_json(engine, sample_json)

        result = mark_topic_complete(engine, 1)
        assert result is True

        with Session(engine) as session:
            progress = session.get(Progress, 1)
            assert progress is not None
            assert progress.completed_at is not None
            assert progress.next_review_date is not None

    def test_mark_nonexistent_topic(self, engine):
        """Deve retornar False para tópico inexistente."""
        result = mark_topic_complete(engine, 9999)
        assert result is False

    def test_mark_already_completed(self, engine, sample_json):
        """Marcar tópico já concluído não deve alterar completed_at."""
        import_topics_from_json(engine, sample_json)
        mark_topic_complete(engine, 1)

        with Session(engine) as session:
            p1 = session.get(Progress, 1)
            original_completed_at = p1.completed_at

        # Marcar novamente
        mark_topic_complete(engine, 1)

        with Session(engine) as session:
            p2 = session.get(Progress, 1)
            assert p2.completed_at == original_completed_at


class TestUnmarkTopicComplete:
    """Testes para desmarcar tópicos."""

    def test_unmark_topic_complete(self, engine, sample_json):
        """Deve resetar completed_at para None."""
        import_topics_from_json(engine, sample_json)
        mark_topic_complete(engine, 1)

        result = unmark_topic_complete(engine, 1)
        assert result is True

        with Session(engine) as session:
            progress = session.get(Progress, 1)
            assert progress.completed_at is None

    def test_unmark_nonexistent(self, engine):
        """Deve retornar False para progress inexistente."""
        result = unmark_topic_complete(engine, 9999)
        assert result is False


class TestGetTopicProgress:
    """Testes para consulta de progresso individual."""

    def test_get_topic_progress(self, engine, sample_json):
        """Deve retornar dict com campos esperados."""
        import_topics_from_json(engine, sample_json)
        mark_topic_complete(engine, 1)

        result = get_topic_progress(engine, 1)
        assert result is not None
        assert "id" in result
        assert "codigo" in result
        assert "completed_at" in result
        assert result["completed_at"] is not None

    def test_get_nonexistent_topic_progress(self, engine):
        """Deve retornar None para tópico inexistente."""
        result = get_topic_progress(engine, 9999)
        assert result is None


class TestGetAllProgress:
    """Testes para consulta de progresso de todos os tópicos."""

    def test_get_all_progress(self, engine, sample_json):
        """Deve retornar lista com todos os tópicos."""
        import_topics_from_json(engine, sample_json)
        # Limpa cache do Streamlit para evitar dados stale
        get_all_progress.clear()
        result = get_all_progress(engine)
        assert isinstance(result, list)
        assert len(result) == 3

    def test_all_progress_fields(self, engine, sample_json):
        """Cada item deve ter os campos obrigatórios."""
        import_topics_from_json(engine, sample_json)
        get_all_progress.clear()
        result = get_all_progress(engine)
        assert isinstance(result, list)
        required_fields = {
            "id",
            "codigo",
            "secao",
            "subsecao",
            "titulo",
            "completed_at",
            "last_reviewed_at",
            "review_count",
            "next_review_date",
        }
        for item in result:
            assert isinstance(item, dict)
            assert required_fields.issubset(item.keys())

    def test_get_all_progress_real_dataset_not_truncated(self, populated_engine):
        """No dataset real, retorno padrão não pode truncar em 100."""
        get_all_progress.clear()
        result = get_all_progress(populated_engine)
        assert isinstance(result, list)
        assert len(result) > 300

    def test_get_all_progress_pagination(self, engine, sample_json):
        """Quando paginado, deve retornar dict com data + total."""
        import_topics_from_json(engine, sample_json)
        get_all_progress.clear()
        result = get_all_progress(engine, offset=0, limit=2)
        assert isinstance(result, dict)
        assert result["total"] == 3
        assert len(result["data"]) == 2

    def test_cache_invalidation_after_mark_topic_complete(self, engine, sample_json):
        """Após marcar, get_all_progress deve refletir alteração sem aguardar TTL."""
        import_topics_from_json(engine, sample_json)
        get_all_progress.clear()

        before = get_all_progress(engine)
        before_item = next((p for p in before if p["id"] == 1), None)
        assert before_item is not None
        assert before_item["completed_at"] is None

        assert mark_topic_complete(engine, 1) is True

        after = get_all_progress(engine)
        after_item = next((p for p in after if p["id"] == 1), None)
        assert after_item is not None
        assert after_item["completed_at"] is not None

    def test_cache_invalidation_after_unmark_topic_complete(
        self, engine, sample_json
    ):
        """Após desmarcar, get_all_progress deve refletir alteração sem aguardar TTL."""
        import_topics_from_json(engine, sample_json)
        assert mark_topic_complete(engine, 1) is True
        get_all_progress.clear()

        before = get_all_progress(engine)
        before_item = next((p for p in before if p["id"] == 1), None)
        assert before_item is not None
        assert before_item["completed_at"] is not None

        assert unmark_topic_complete(engine, 1) is True

        after = get_all_progress(engine)
        after_item = next((p for p in after if p["id"] == 1), None)
        assert after_item is not None
        assert after_item["completed_at"] is None


class TestReviews:
    """Testes para sistema de revisões (SRS)."""

    def test_get_topics_due_for_review_empty(self, engine, sample_json):
        """Sem tópicos concluídos, nenhum deve estar pendente."""
        import_topics_from_json(engine, sample_json)
        today = datetime.now().strftime("%Y-%m-%d")
        result = get_topics_due_for_review(engine, today)
        assert len(result) == 0

    def test_get_topics_due_for_review_after_complete(self, engine, sample_json):
        """Tópico concluído deve aparecer como pendente no dia seguinte."""
        import_topics_from_json(engine, sample_json)
        mark_topic_complete(engine, 1)

        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        result = get_topics_due_for_review(engine, tomorrow)
        assert len(result) >= 1
        assert result[0]["id"] == 1

    def test_mark_review_complete(self, engine, sample_json):
        """Deve incrementar review_count e agendar próxima revisão."""
        import_topics_from_json(engine, sample_json)
        mark_topic_complete(engine, 1)

        result = mark_review_complete(engine, 1, 7)
        assert result is True

        with Session(engine) as session:
            progress = session.get(Progress, 1)
            assert progress.review_count == 1
            assert progress.last_reviewed_at is not None
            assert progress.next_review_date is not None

    def test_cache_invalidation_after_mark_review_complete(self, engine, sample_json):
        """Após revisão, cache de progresso deve refletir review_count atualizado."""
        import_topics_from_json(engine, sample_json)
        assert mark_topic_complete(engine, 1) is True
        get_all_progress.clear()

        before = get_all_progress(engine)
        before_item = next((p for p in before if p["id"] == 1), None)
        assert before_item is not None
        assert before_item["review_count"] == 0

        assert mark_review_complete(engine, 1, 7) is True

        after = get_all_progress(engine)
        after_item = next((p for p in after if p["id"] == 1), None)
        assert after_item is not None
        assert after_item["review_count"] == 1

    def test_mark_review_nonexistent(self, engine):
        """Deve retornar False para progress inexistente."""
        result = mark_review_complete(engine, 9999, 7)
        assert result is False

    def test_get_upcoming_reviews(self, engine, sample_json):
        """Tópicos com next_review_date futuro devem aparecer."""
        import_topics_from_json(engine, sample_json)
        mark_topic_complete(engine, 1)

        # A marcação define next_review_date para amanhã (1 dia)
        result = get_upcoming_reviews(engine, days=7)
        assert len(result) >= 1


class TestStatistics:
    """Testes para funções de estatísticas."""

    def test_get_statistics_empty(self, engine, sample_json):
        """Estatísticas com nenhum tópico concluído."""
        import_topics_from_json(engine, sample_json)
        stats = get_statistics(engine)

        assert stats["total_topics"] == 3
        assert stats["completed_topics"] == 0
        assert stats["pending_topics"] == 3
        assert stats["completion_rate"] == 0

    def test_get_statistics_with_progress(self, engine, sample_json):
        """Estatísticas após concluir 1 tópico."""
        import_topics_from_json(engine, sample_json)
        mark_topic_complete(engine, 1)
        stats = get_statistics(engine)

        assert stats["completed_topics"] == 1
        assert stats["completion_rate"] > 0

    def test_detailed_statistics_by_section(self, engine, sample_json):
        """Deve retornar uma entrada por seção."""
        import_topics_from_json(engine, sample_json)
        result = get_detailed_statistics_by_section(engine)
        assert len(result) == 2  # Seção A e Seção B
        assert all("secao" in item for item in result)

    def test_topic_distribution(self, engine, sample_json):
        """Deve retornar distribuição correta por seção."""
        import_topics_from_json(engine, sample_json)
        result = get_topic_distribution_by_section(engine)
        assert len(result) == 2
        totals = {item["secao"]: item["total"] for item in result}
        assert totals["Seção Teste A"] == 2
        assert totals["Seção Teste B"] == 1

    def test_weekly_review_data_empty(self, engine, sample_json):
        """Sem revisões, deve retornar lista vazia."""
        import_topics_from_json(engine, sample_json)
        result = get_weekly_review_data(engine)
        assert result == []


class TestExport:
    """Testes para exportação de dados."""

    def test_export_all_progress(self, engine, sample_json):
        """Deve exportar todos os tópicos com campos corretos."""
        import_topics_from_json(engine, sample_json)
        mark_topic_complete(engine, 1)

        result = export_all_progress_to_dict(engine)
        assert len(result) == 3

        required_keys = {
            "codigo",
            "secao",
            "subsecao",
            "titulo",
            "completed_at",
            "last_reviewed_at",
            "review_count",
            "next_review_date",
        }
        for item in result:
            assert required_keys.issubset(item.keys())
