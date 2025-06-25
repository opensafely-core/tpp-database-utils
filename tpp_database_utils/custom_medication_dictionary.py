import csv
import pathlib

from pymssql import OperationalError


CUSTOM_MEDICATION_DICTIONARY_CSV = pathlib.Path(__file__).with_name(
    "custom_medication_dictionary.csv"
)


class CustomMedicationDictionary:
    def __init__(self, tpp_connection, temp_database_name):
        self.tpp_connection = tpp_connection
        self.temp_database_name = temp_database_name
        self.cursor = self.tpp_connection.cursor()

    @property
    def table_name(self):
        return f"{self.temp_database_name}..CustomMedicationDictionary"

    def drop(self):
        table = self.table_name
        self.cursor.execute(
            f"""
            IF OBJECT_ID('{table}', 'U') IS NOT NULL
                DROP TABLE {table}
            """
        )

    def create(self):
        table = self.table_name
        self.cursor.execute(
            f"""
            CREATE TABLE {table} (
                DMD_ID VARCHAR(50) COLLATE Latin1_General_CI_AS,
                MultilexDrug_ID VARCHAR(767),
            )
            """
        )

    def update(self):
        """Create & populate CustomMedicationDictionary table"""
        table = self.table_name
        try:
            self.drop()
            self.create()
            self.cursor.executemany(
                f"INSERT INTO {table} VALUES (%s, %s)",
                self.load_csv(),
            )
            self.tpp_connection.commit()
        except OperationalError:
            # If we attempt to insert invalid data, we want to reinstate
            # the table from before we dropped it!
            self.tpp_connection.rollback()
            raise

    def get(self):
        table = self.table_name
        self.cursor.execute(
            f"""
            SELECT *
            FROM {table}
            ORDER BY DMD_ID, MultilexDrug_ID
            """
        )
        return list(self.cursor)

    @staticmethod
    def load_csv():
        with CUSTOM_MEDICATION_DICTIONARY_CSV.open(newline="") as f:
            reader = csv.reader(f)
            next(reader)  # skip header row
            return [tuple(x) for x in reader]
