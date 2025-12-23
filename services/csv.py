#

# Std
import csv
from collections import Counter
from typing import Dict

from meemoo_mtd.mediahaven.fields import (
    fields as mh_known_fields,
    identifier_fields,
)

class CsvInvalidError(Exception):
    pass


# TODO: Read and parse the CSV-file only once!
class CsvParser:
    """Wrapper class around the CSV."""
    def __init__(self, csv_filepath: str, delimiter: str = ','):
        self.csv_filepath = csv_filepath
        self.delimiter = delimiter
        self.cols = self.get_header_cols()
        self.id_col = self.cols[0]
        self.data_cols = self.cols[1:] if len(self.cols) > 1 else []
    #
    def get_header_cols(self):
        with open(self.csv_filepath) as csvfile:
            reader = csv.reader(csvfile, delimiter=self.delimiter)
            return next(reader)
    #
    def get_column_values(self, column: int = 1):
        assert not(column < 1), f"column needs to be a positive integer, starting from 1: {column}"
        val_list = []
        with open(self.csv_filepath, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=self.delimiter)
            for row in reader:
                val_list.append(row[column-1])
        return val_list
    #
    def get_duplicates_in_column(self, column: int = 1) -> Dict:
        """Detect and return duplicate values in a specific column in a CSV-file.
        Defaults to the first column"""
        # Get all values in the column
        val_list = self.get_column_values(column)
        # Count and return duplicates
        counts = Counter(val_list)
        return {item: count for item, count in counts.items() if count > 1}
    #
    def check_identifier_field(self):
        """Function to check  if a certain field is an allowed "identifier-field".
        """
        if not self.id_col in identifier_fields:
            raise CsvInvalidError(f"Following columnames are not recognized as MediaHaven identifier fieldnames: {self.id_col}")
    #
    def validate_structure(self):
        # Validate row lengths
        with open(self.csv_filepath, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=self.delimiter)
            header = next(reader)
            expected_columns = len(header)
            for row_num, row in enumerate(reader, 2):
                if len(row) != expected_columns:
                    raise CsvInvalidError(f"Error in row {row_num}: Column mismatch. Row: {row}")
    #
    def check_fieldnames(self):
        """Method to check a list or set of fieldnames for unknown or disallowed
        fieldnames."""
        unkown_fieldnames =  set(self.data_cols) - mh_known_fields
        if unkown_fieldnames:
            raise CsvInvalidError(f"Following columnames are not recognized as MediaHaven fieldnames: {unkown_fieldnames}")
    #
    def check_unique_identifiers(self):
        """Method to check the unicity of the identifiers (by convention: the
        values in the first column) of a CSV-file."""
        duplicates = self.get_duplicates_in_column(1)
        if duplicates:
            raise CsvInvalidError(f"Duplicate values found in identifier column: {duplicates}")
    #
    def validate(self):
        # Validate row lengths
        self.validate_structure()
        # Validate id_col
        self.check_identifier_field()
        # Validate known fieldnames
        self.check_fieldnames()
        # Check for unicity of identifier values
        self.check_unique_identifiers()
    #
    def iterator(self):
        with open(self.csv_filepath, newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=self.delimiter)
            for row in reader:
                yield row

