import pytest

from analysis.faers_analysis.src.utils import QuestionConfig


@pytest.mark.parametrize(
    "json_object,expected",
    [
        (
            {
                "name": "test1",
                "drug": ["Aspirin", " Ibuprofen "],
                "reaction": ["Headache", " nausea "],
                "control": ["Placebo"],
            },
            {
                "name": "test1",
                "drugs": ["aspirin", "ibuprofen"],
                "reactions": ["headache", "nausea"],
                "control": ["placebo"],
            },
        ),
        (
            {
                "name": "test2",
                "drug": ["Paracetamol"],
                "reaction": ["Fever"],
                # no control
            },
            {
                "name": "test2",
                "drugs": ["paracetamol"],
                "reactions": ["fever"],
                "control": None,
            },
        ),
        (
            {
                "name": "test3",
                "drug": ["DrugA"],
                "reaction": ["ReactionA"],
                "control": [],
            },
            {
                "name": "test3",
                "drugs": ["druga"],
                "reactions": ["reactiona"],
                "control": None,
            },
        ),
    ],
)
def test_config_from_json_object_success(json_object, expected):
    config = QuestionConfig.config_from_json_object(json_object)
    assert config.name == expected["name"]
    assert config.drugs == expected["drugs"]
    assert config.reactions == expected["reactions"]
    assert config.control == expected["control"]


@pytest.mark.parametrize(
    "json_object,missing_key",
    [
        ({"drug": ["A"], "reaction": ["B"]}, "name"),
        ({"name": "x", "reaction": ["B"]}, "drug"),
        ({"name": "x", "drug": ["A"]}, "reaction"),
    ],
)
def test_config_from_json_object_missing_keys(json_object, missing_key):
    with pytest.raises(KeyError) as excinfo:
        QuestionConfig.config_from_json_object(json_object)
    assert missing_key in str(excinfo.value)
