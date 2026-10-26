import pytest
from app.specification_search import matching_windows, section_hits


@pytest.mark.parametrize(
    "query",
    [
        "cuanto torque llevan las ruedas?",
        "par de apriete de los bulones de las ruedas",
        "torque tornillos de rueda",
        "cuantos Nm llevan las ruedas?",
        "cuanto torque llevan las ruedas?\nTema de la consulta: neumáticos",
    ],
)
def test_wheel_specification_inside_brake_procedure(query):
    text = (
        "Se ajustan los tornillos guía a 40 Nm y los de fijación de la rueda a 100 Nm."
    )
    assert matching_windows(query, text)
    sections = [{"id": "brakes", "chunks": [{"page_id": "p1", "text": text}]}]
    assert section_hits(query, sections) == {"brakes": ["p1"]}


@pytest.mark.parametrize(
    "text",
    [
        "Torque de fricción de los roda mientos del diferencial. Tornillos a 70 Nm.",
        "Se ajusta la tuerca de la maza de la rueda a 30 Nm.",
        "Tornillo de la rueda tensora a 45 Nm.",
        "Se remueve la rueda. Se ajustan los tornillos guía a 40 Nm.",
        "Neumáticos: presión de 30 psi.",
    ],
)
def test_wheel_fixings_do_not_match_other_fasteners(text):
    assert not matching_windows("torque ruedas", text)


def test_other_component_and_non_specification_queries():
    assert matching_windows(
        "torque tapa de bancada", "Tapa de bancada: tornillos a 65 Nm."
    )
    assert not matching_windows("torque tapa de bancada", "Tapa de válvulas a 10 Nm.")
    assert not matching_windows(
        "cómo cambio las ruedas", "Tornillos de rueda a 100 Nm."
    )


def test_followup_preserves_torque_instead_of_generic_measurement():
    from app import conversation

    state = conversation.resolve(
        [
            {"id": "1", "user": "cuanto torque llevan las ruedas?"},
            {"id": "2", "user": "¿Y atrás?"},
        ]
    )
    assert state["mode"] == "followup"
    assert "par de apriete" in state["query"]
    assert matching_windows(
        state["query"], "Se coloca la rueda y se ajustan los tornillos a 100 Nm."
    )
