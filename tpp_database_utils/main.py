import os
import sys

from custom_medication_dictionary import (
    CustomMedicationDictionary,
)
from maintenance_mode import in_maintenance_mode
from mssql_connection import pymssql_connect


def main():
    if len(sys.argv) < 2:
        print("Please specify a command to run")
        return

    command = sys.argv[1]

    tpp_connection = pymssql_connect()
    match command:
        case "in_maintenance_mode":
            mode = in_maintenance_mode(tpp_connection)

            # This should be the only output on stdout,
            # anything else needs to be on stderr
            if mode:
                print("db-maintenance")

        case "update_custom_medication_dictionary":
            temp_database_name = os.environ["TEMP_DATABASE_NAME"]
            dictionary = CustomMedicationDictionary(tpp_connection, temp_database_name)
            dictionary.update()

        case "get_custom_medication_dictionary":
            temp_database_name = os.environ["TEMP_DATABASE_NAME"]
            dictionary = CustomMedicationDictionary(tpp_connection, temp_database_name)
            current_dictionary_contents = dictionary.get()
            # nb. This is not very nicely printed, but it should be plenty for
            # our purposes at the moment
            print(current_dictionary_contents)


if __name__ == "__main__":
    main()
