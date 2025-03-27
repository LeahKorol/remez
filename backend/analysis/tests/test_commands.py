from django.core.management import call_command, CommandError
from django.test import TestCase
from analysis.models import DrugList, ReactionList

from io import StringIO
import tempfile
import shutil
from pathlib import Path
import pandas as pd


class LoadTermsCommandTests(TestCase):
    def setUp(self):
        # Create a temp directory to simulate input_dir
        self.test_dir = tempfile.mkdtemp()
        self.input_path = Path(self.test_dir)

    def tearDown(self):
        # Remove the temp directory after tests
        shutil.rmtree(self.test_dir)

    def _create_csv(self, filename, field_name, values):
        df = pd.DataFrame({field_name: values})
        df.to_csv(self.input_path / filename, index=False)

    def test_load_drug_terms(self):
        self._create_csv(
            "drug_sample.csv", "drugname", ["ASPIRIN", "IBUPROFEN", "ASPIRIN"]
        )  # duplicate on purpose

        out = StringIO()
        call_command(
            "load_faers_terms", "--dir_in", self.test_dir, "--no_reactions", stdout=out
        )

        self.assertEqual(DrugList.objects.count(), 2)  # no duplicate drugs
        self.assertTrue(DrugList.objects.filter(name="ASPIRIN").exists())
        self.assertTrue(DrugList.objects.filter(name="IBUPROFEN").exists())

    def test_load_reaction_terms(self):
        self._create_csv(
            "reac_sample.csv", "pt", ["NAUSEA", "HEADACHE", "NAUSEA"]
        )  # duplicate on purpose

        out = StringIO()
        call_command(
            "load_faers_terms", "--dir_in", self.test_dir, "--no_drugs", stdout=out
        )

        self.assertEqual(ReactionList.objects.count(), 2)  # no duplicate reactions
        self.assertTrue(ReactionList.objects.filter(name="NAUSEA").exists())
        self.assertTrue(ReactionList.objects.filter(name="HEADACHE").exists())

    def test_raises_error_if_missing_field_column(self):
        # Missing 'pt' column for reaction
        self._create_csv("reac_invalid.csv", "some_other_field", ["foo", "bar"])

        out = StringIO()
        with self.assertRaises(CommandError):
            call_command(
                "load_faers_terms", "--dir_in", self.test_dir, "--no_drugs", stdout=out
            )

    def test_does_not_duplicate_existing_drugs_and_reactions(self):
        # Create initial drug and reaction entries
        DrugList.objects.create(name="ASPIRIN")
        ReactionList.objects.create(name="NAUSEA")

        # CSV includes one existing and one new item for both drugs and reactions
        self._create_csv("drug_sample.csv", "drugname", ["ASPIRIN", "IBUPROFEN"])
        self._create_csv("reac_sample.csv", "pt", ["NAUSEA", "HEADACHE"])

        out = StringIO()
        call_command("load_faers_terms", "--dir_in", self.test_dir, stdout=out)

        # Ensure no duplicates and both new terms were added
        self.assertEqual(DrugList.objects.count(), 2)
        self.assertTrue(DrugList.objects.filter(name="ASPIRIN").exists())
        self.assertTrue(DrugList.objects.filter(name="IBUPROFEN").exists())

        self.assertEqual(ReactionList.objects.count(), 2)
        self.assertTrue(ReactionList.objects.filter(name="NAUSEA").exists())
        self.assertTrue(ReactionList.objects.filter(name="HEADACHE").exists())
