import pytest
import pandas as pd
from pathlib import Path
from io import StringIO
from typing import Callable


from django.core.management import call_command, CommandError
from analysis.models import DrugName, ReactionName


@pytest.mark.django_db
class TestLoadFaersTerms:
    def test_loads_drug_terms_for_specific_quarters(
        self,
        create_zipped_csv: Callable[[pd.DataFrame, str, Path], Path],
        tmp_path: Path,
    ):
        """
        Should load drug terms only for the specified quarters (2020q1 to 2020q2),
        and ignore files outside that range.
        """
        create_zipped_csv(
            pd.DataFrame({"drugname": ["aspirin"]}), "drug2020q1", tmp_path
        )
        create_zipped_csv(
            pd.DataFrame({"drugname": ["ibupropen"]}), "drug2020q2", tmp_path
        )
        create_zipped_csv(
            pd.DataFrame({"drugname": ["paracetamol"]}), "drug2020q3", tmp_path
        )  # ignored

        out = StringIO()
        call_command(
            "load_faers_terms",
            "2020q1",
            "2020q3",
            "--dir_in",
            tmp_path,
            "--no_reactions",
            stdout=out,
        )

        assert DrugName.objects.count() == 2
        assert DrugName.objects.filter(name="aspirin").exists()
        assert DrugName.objects.filter(name="ibupropen").exists()
        assert not DrugName.objects.filter(name="paracetamol").exists()

    def test_loads_reaction_terms_for_specific_quarters(
        self,
        create_zipped_csv: Callable[[pd.DataFrame, str, Path], Path],
        tmp_path: Path,
    ):
        """
        Should load only reaction terms within the given quarter range (2022q1),
        and skip earlier ones like 2021q4.
        """
        create_zipped_csv(pd.DataFrame({"pt": ["nausea"]}), "reac2021q4", tmp_path)
        create_zipped_csv(pd.DataFrame({"pt": ["headache"]}), "reac2022q1", tmp_path)

        out = StringIO()
        call_command(
            "load_faers_terms",
            "2022q1",
            "2022q2",
            "--dir_in",
            tmp_path,
            "--no_drugs",
            stdout=out,
        )

        assert ReactionName.objects.count() == 1
        assert ReactionName.objects.filter(name="headache").exists()
        assert not ReactionName.objects.filter(name="nausea").exists()

    def test_skips_existing_terms(
        self,
        create_zipped_csv: Callable[[pd.DataFrame, str, Path], Path],
        tmp_path: Path,
    ):
        """
        Should not duplicate terms that already exist in the database.
        """
        DrugName.objects.create(name="aspirin")
        ReactionName.objects.create(name="nausea")

        create_zipped_csv(
            pd.DataFrame({"drugname": ["aspirin", "ibupropen"]}), "drug2020q1", tmp_path
        )
        create_zipped_csv(
            pd.DataFrame({"pt": ["nausea", "headache"]}), "reac2020q1", tmp_path
        )

        out = StringIO()
        call_command(
            "load_faers_terms",
            "2020q1",
            "2020q2",
            "--dir_in",
            tmp_path,
            stdout=out,
        )

        assert DrugName.objects.count() == 2
        assert DrugName.objects.filter(name="ibupropen").exists()

        assert ReactionName.objects.count() == 2
        assert ReactionName.objects.filter(name="headache").exists()

    def test_raises_error_if_required_file_missing(self, tmp_path):
        """
        Should raise CommandError if an expected file for the given quarter is missing.
        """
        out = StringIO()
        with pytest.raises(CommandError) as exc_info:
            call_command(
                "load_faers_terms",
                "2020q1",
                "2020q2",
                "--dir_in",
                tmp_path,
                stdout=out,
            )

        assert "Required file not found" in str(exc_info.value)

    def test_raises_error_if_column_missing(
        self,
        create_zipped_csv: Callable[[pd.DataFrame, str, Path], Path],
        tmp_path: Path,
    ):
        """
        Should raise CommandError if the expected column (e.g. 'pt' or 'drugname') is missing.
        """
        create_zipped_csv(pd.DataFrame({"wrong_col": ["oops"]}), "reac2020q1", tmp_path)

        out = StringIO()
        with pytest.raises(CommandError):
            call_command(
                "load_faers_terms",
                "2020q1",
                "2020q2",
                "--dir_in",
                tmp_path,
                "--no_drugs",
                stdout=out,
            )
