from django.core.management import call_command, CommandError
from django.test import TestCase
from analysis.models import DrugName, ReactionName

from io import StringIO
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import zipfile


class LoadTermsCommandTests(TestCase):
    def setUp(self):
        # Create a temporary directory to simulate input_dir for FAERS files
        self.test_dir = tempfile.mkdtemp()
        self.input_path = Path(self.test_dir)

    def tearDown(self):
        # Clean up the temporary directory after each test
        shutil.rmtree(self.test_dir)

    def _create_zipped_csv(self, filename, field_name, values):
        """
        Helper to create a zipped CSV file with given values in the specified field/column.
        """
        csv_path = self.input_path / filename.replace(".zip", "")
        df = pd.DataFrame({field_name: values})
        df.to_csv(csv_path, index=False)
        zip_path = self.input_path / filename
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.write(csv_path, arcname=csv_path.name)
        csv_path.unlink()  # remove unzipped file after creating the zip

    def test_load_drug_terms_for_specific_quarters(self):
        """
        Should load drug terms only for the specified quarters (2020q1 to 2020q2),
        and ignore files outside that range.
        """
        self._create_zipped_csv("drug2020q1.csv.zip", "drugname", ["ASPIRIN"])
        self._create_zipped_csv("drug2020q2.csv.zip", "drugname", ["IBUPROFEN"])
        self._create_zipped_csv(
            "drug2020q3.csv.zip", "drugname", ["PARACETAMOL"]
        )  # should be ignored

        out = StringIO()
        call_command(
            "load_faers_terms",
            "2020q1",
            "2020q3",
            "--dir_in",
            self.test_dir,
            "--no_reactions",
            stdout=out,
        )

        self.assertEqual(DrugName.objects.count(), 2)
        self.assertTrue(DrugName.objects.filter(name="ASPIRIN").exists())
        self.assertTrue(DrugName.objects.filter(name="IBUPROFEN").exists())
        self.assertFalse(DrugName.objects.filter(name="PARACETAMOL").exists())

    def test_load_reaction_terms_for_specific_quarters(self):
        """
        Should load only reaction terms within the given quarter range (2022q1),
        and skip earlier ones like 2021q4.
        """
        self._create_zipped_csv("reac2021q4.csv.zip", "pt", ["NAUSEA"])
        self._create_zipped_csv("reac2022q1.csv.zip", "pt", ["HEADACHE"])

        out = StringIO()
        call_command(
            "load_faers_terms",
            "2022q1",
            "2022q2",
            "--dir_in",
            self.test_dir,
            "--no_drugs",
            stdout=out,
        )

        self.assertEqual(ReactionName.objects.count(), 1)
        self.assertTrue(ReactionName.objects.filter(name="HEADACHE").exists())
        self.assertFalse(ReactionName.objects.filter(name="NAUSEA").exists())

    def test_skips_already_existing_terms(self):
        """
        Should not duplicate terms that already exist in the database.
        """
        DrugName.objects.create(name="ASPIRIN")
        ReactionName.objects.create(name="NAUSEA")

        self._create_zipped_csv(
            "drug2020q1.csv.zip", "drugname", ["ASPIRIN", "IBUPROFEN"]
        )
        self._create_zipped_csv("reac2020q1.csv.zip", "pt", ["NAUSEA", "HEADACHE"])

        out = StringIO()
        call_command(
            "load_faers_terms",
            "2020q1",
            "2020q2",
            "--dir_in",
            self.test_dir,
            stdout=out,
        )

        self.assertEqual(DrugName.objects.count(), 2)
        self.assertTrue(DrugName.objects.filter(name="IBUPROFEN").exists())

        self.assertEqual(ReactionName.objects.count(), 2)
        self.assertTrue(ReactionName.objects.filter(name="HEADACHE").exists())

    def test_raises_error_if_required_file_missing(self):
        """
        Should raise CommandError if an expected file for the given quarter is missing.
        """
        out = StringIO()
        with self.assertRaises(CommandError) as cm:
            call_command(
                "load_faers_terms",
                "2020q1",
                "2020q2",
                "--dir_in",
                self.test_dir,
                stdout=out,
            )
        self.assertIn("Required file not found", str(cm.exception))

    def test_raises_error_if_column_missing(self):
        """
        Should raise CommandError if the expected column (e.g. 'pt' or 'drugname') is missing from the CSV.
        """
        self._create_zipped_csv("reac2020q1.csv.zip", "wrong_col", ["oops"])
        out = StringIO()
        with self.assertRaises(CommandError):
            call_command(
                "load_faers_terms",
                "2020q1",
                "2020q2",
                "--dir_in",
                self.test_dir,
                "--no_drugs",
                stdout=out,
            )
