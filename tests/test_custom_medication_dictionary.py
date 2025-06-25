import pytest
from pymssql import OperationalError

from tpp_database_utils import custom_medication_dictionary
from tpp_database_utils.custom_medication_dictionary import CustomMedicationDictionary


@pytest.fixture()
def temp_database_name(monkeypatch):
    temp_database_name = "OPENCoronaTempTables"
    monkeypatch.setenv("TEMP_DATABASE_NAME", temp_database_name)
    return temp_database_name


@pytest.fixture()
def mapping_csv_path(tmp_path, monkeypatch):
    mapping_csv_path = tmp_path / "custom_medication_dictionary.csv"
    # Nb. this is going to affect the CSV path for everything else under test
    monkeypatch.setattr(
        custom_medication_dictionary,
        "CUSTOM_MEDICATION_DICTIONARY_CSV",
        mapping_csv_path,
    )
    return mapping_csv_path


@pytest.fixture()
def write_mapping_csv(mapping_csv_path):
    def _write_mapping_csv(rows):
        mapping_csv_path.write_text(
            "\n".join(",".join(row) for row in rows)
        )  # overwrites

    return _write_mapping_csv


@pytest.fixture()
def test_custom_medication_dictionary(tpp_connection, temp_database_name):
    test_custom_medication_dictionary = CustomMedicationDictionary(
        tpp_connection, temp_database_name
    )
    yield test_custom_medication_dictionary
    test_custom_medication_dictionary.drop()
    # nb. autocommit is turned off by default
    tpp_connection.commit()


def test_update_custom_medication_dictionary(
    tmp_path, test_custom_medication_dictionary, write_mapping_csv
):
    write_mapping_csv(
        [
            ("DMD_ID", "MultilexDrug_ID", "FullName"),
            ("111111", "a", "full name for a"),
            ("222222", "b", "full name for b"),
        ]
    )
    test_custom_medication_dictionary.update()

    assert test_custom_medication_dictionary.get() == [
        ("111111", "a"),
        ("222222", "b"),
    ]


def test_update_custom_medication_dictionary_table_dropped(
    tmp_path, write_mapping_csv, test_custom_medication_dictionary
):
    # Load previous data
    write_mapping_csv(
        [
            ("DMD_ID", "MultilexDrug_ID", "FullName"),
            ("111111", "a", "full name for a"),
            ("222222", "b", "full name for b"),
        ]
    )
    test_custom_medication_dictionary.update()

    assert test_custom_medication_dictionary.get() == [
        ("111111", "a"),
        ("222222", "b"),
    ]

    # Overwrite the table with new contents
    write_mapping_csv(
        [
            ("DMD_ID", "MultilexDrug_ID", "FullName"),
            ("333333", "c", "full name for c"),
            ("444444", "d", "full name for d"),
        ]
    )
    test_custom_medication_dictionary.update()

    assert test_custom_medication_dictionary.get() == [
        ("333333", "c"),
        ("444444", "d"),
    ]


def test_update_custom_medication_dictionary_table_not_dropped(
    tmp_path, write_mapping_csv, test_custom_medication_dictionary
):
    write_mapping_csv(
        [
            ("DMD_ID", "MultilexDrug_ID", "FullName"),
            ("111111", "a", "full name for a"),
            ("222222", "b", "full name for b"),
        ]
    )
    test_custom_medication_dictionary.update()

    assert test_custom_medication_dictionary.get() == [
        ("111111", "a"),
        ("222222", "b"),
    ]

    # Force the INSERT to error, by passing a DM+D ID that's too long.
    # The transaction should rollback.
    write_mapping_csv(
        [
            ("DMD_ID", "MultilexDrug_ID", "FullName"),
            (f"{'5' * 60}", "e", "full name for e"),
        ],
    )
    try:
        test_custom_medication_dictionary.update()
    except OperationalError:
        pass

    # Table still contains the original data
    assert test_custom_medication_dictionary.get() == [
        ("111111", "a"),
        ("222222", "b"),
    ]
