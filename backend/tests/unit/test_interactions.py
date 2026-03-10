"""Unit tests for interaction filtering logic."""

from app.models.interaction import InteractionLog
from app.routers.interactions import _filter_by_item_id


def _make_log(id: int, learner_id: int, item_id: int, kind: str = "attempt") -> InteractionLog:
    return InteractionLog(id=id, learner_id=learner_id, item_id=item_id, kind=kind)


def test_filter_returns_all_when_item_id_is_none() -> None:
    interactions = [_make_log(1, 1, 1), _make_log(2, 2, 2)]
    result = _filter_by_item_id(interactions, None)
    assert result == interactions


def test_filter_returns_empty_for_empty_input() -> None:
    result = _filter_by_item_id([], 1)
    assert result == []


def test_filter_returns_interaction_with_matching_ids() -> None:
    interactions = [_make_log(1, 1, 1), _make_log(2, 2, 2)]
    result = _filter_by_item_id(interactions, 1)
    assert len(result) == 1
    assert result[0].id == 1


def test_filter_excludes_interaction_with_different_learner_id() -> None:
    interactions = [_make_log(1, 2, 1), _make_log(2, 1, 2)]
    result = _filter_by_item_id(interactions, 1)
    assert len(result) == 1
    assert result[0].id == 1
    assert result[0].learner_id == 2


def test_filter_returns_multiple_matches_for_same_item_id() -> None:
    """Тест проверяет, что фильтр возвращает все совпадения, когда несколько
    взаимодействий имеют одинаковый item_id.
    
    Крайний случай: множественные совпадения по item_id."""
    interactions = [
        _make_log(1, 1, 5),
        _make_log(2, 2, 5),
        _make_log(3, 3, 5),
        _make_log(4, 1, 10),
    ]
    result = _filter_by_item_id(interactions, 5)
    assert len(result) == 3
    assert all(interaction.item_id == 5 for interaction in result)
    assert set(interaction.id for interaction in result) == {1, 2, 3}


def test_filter_handles_negative_item_id() -> None:
    """Тест проверяет работу фильтра с отрицательными значениями item_id.
    
    Граничное значение: отрицательные целые числа для ID."""
    interactions = [
        _make_log(1, 1, -1),
        _make_log(2, 2, 1),
        _make_log(3, 3, -100),
    ]
    result_negative_one = _filter_by_item_id(interactions, -1)
    assert len(result_negative_one) == 1
    assert result_negative_one[0].id == 1
    assert result_negative_one[0].item_id == -1
    
    result_negative_hundred = _filter_by_item_id(interactions, -100)
    assert len(result_negative_hundred) == 1
    assert result_negative_hundred[0].id == 3


def test_filter_with_empty_string_kind() -> None:
    """Тест проверяет создание взаимодействия с пустой строкой в поле kind.
    
    Крайний случай: пустая строка для обязательного поля kind."""
    interaction = _make_log(id=1, learner_id=1, item_id=1, kind="")
    assert interaction.kind == ""
    assert interaction.learner_id == 1
    assert interaction.item_id == 1


def test_filter_with_special_characters_in_kind() -> None:
    """Тест проверяет обработку специальных символов в поле kind.
    
    Крайний случай: специальные символы, Unicode, emoji в kind."""
    special_kinds = [
        _make_log(1, 1, 1, kind="attempt<script>alert('xss')</script>"),
        _make_log(2, 2, 2, kind="view_👀_tracking"),
        _make_log(3, 3, 3, kind="null\0byte"),
        _make_log(4, 4, 4, kind="кириллица_测试"),
    ]
    for interaction in special_kinds:
        result = _filter_by_item_id([interaction], interaction.item_id)
        assert len(result) == 1
        assert result[0].kind == interaction.kind


def test_filter_with_zero_values() -> None:
    """Тест проверяет работу фильтра с нулевыми значениями ID.
    
    Граничное значение: ноль как значение для learner_id и item_id."""
    interactions = [
        _make_log(1, 0, 0),
        _make_log(2, 0, 1),
        _make_log(3, 1, 0),
        _make_log(4, 1, 1),
    ]
    result_item_zero = _filter_by_item_id(interactions, 0)
    assert len(result_item_zero) == 2
    assert all(interaction.item_id == 0 for interaction in result_item_zero)
    
    result_all = _filter_by_item_id(interactions, 1)
    assert len(result_all) == 2
    assert all(interaction.item_id == 1 for interaction in result_all)
