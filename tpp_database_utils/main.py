import os
import sys

import maintenance_mode
from custom_medication_dictionary import (
    CustomMedicationDictionary,
)
from mssql_connection import pymssql_connect


def in_maintenance_mode(tpp_connection):
    mode = maintenance_mode.in_maintenance_mode(tpp_connection)

    # This should be the only output on stdout,
    # anything else needs to be on stderr
    if mode:
        print("db-maintenance")


def update_custom_medication_dictionary(tpp_connection, temp_database_name):
    dictionary = CustomMedicationDictionary(tpp_connection, temp_database_name)
    dictionary.update()


def get_custom_medication_dictionary(tpp_connection, temp_database_name):
    dictionary = CustomMedicationDictionary(tpp_connection, temp_database_name)
    current_dictionary_contents = dictionary.get()
    # nb. This is not very nicely printed, but it should be plenty for
    # our purposes at the moment
    print(current_dictionary_contents)


def error(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def main():
    if len(sys.argv) < 2:
        error("Please specify a command to run")

    command = sys.argv[1]

    tpp_connection = pymssql_connect()
    match command:
        case "in_maintenance_mode":
            in_maintenance_mode(tpp_connection)

        case "update_custom_medication_dictionary":
            temp_database_name = os.environ["TEMP_DATABASE_NAME"]
            update_custom_medication_dictionary(tpp_connection, temp_database_name)

        case "get_custom_medication_dictionary":
            temp_database_name = os.environ["TEMP_DATABASE_NAME"]
            get_custom_medication_dictionary(tpp_connection, temp_database_name)

        case _:
            error("Unknown command")


if __name__ == "__main__":
    main()
