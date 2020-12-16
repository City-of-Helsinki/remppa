import csv
import json
import os
import psycopg2
import time
import logging
from datetime import datetime
from hasher import create_hash


class DB:
    """Database handling class

    Args read from environment variables
        POSTGRES_DB: Database name
        POSTGRES_PASSWORD: Database password
        POSTGRES_USER: Database user name
        POSTGRES_HOST: Database server host name
        POSTGRES_PORT: Database server port number
        DATABASE_IMPORT: Filename for a CSV file with register plate information
                         to be inserted at database at start time.

    """

    def __init__(self):
        logging.basicConfig(level=logging.INFO)

        self.database = os.getenv("POSTGRES_DB")
        self.password = os.getenv("POSTGRES_PASSWORD")
        self.user = os.getenv("POSTGRES_USER")
        self.host = os.getenv("POSTGRES_HOST")
        self.port = int(os.getenv("POSTGRES_PORT"))
        self.import_file = os.getenv("DATABASE_IMPORT")
        self.connect = None
        self.cursor = None
        self.tries = 20
        self.connect_db()

    def connect_db(self):
        """Connect to database"""
        logging.info("connecting to")
        logging.info(
            {
                "user": self.user,
                "host": self.host,
                "port": self.port,
                "db": self.database,
            }
        )
        connect_str = "dbname='{}' user='{}' host='{}' password='{}'".format(
            self.database, self.user, self.host, self.password
        )

        for i in range(self.tries):
            try:
                self.connect = psycopg2.connect(connect_str)
                self.cursor = self.connect.cursor()

                return
            except Exception as e:
                logging.error(e)
                logging.info("Database might not be up yet, waiting and retrying ...")
                time.sleep(2)
        raise

    def create_tables(self):
        """Creates tables, if necessary"""

        query = """
            CREATE TABLE IF NOT EXISTS cache (
                id INT GENERATED ALWAYS AS IDENTITY,
                timestamp VARCHAR(64),
                data TEXT
            );
        """
        logging.info(query)
        self.cursor.execute(query)

        query = """
            CREATE TABLE IF NOT EXISTS cache_delete (
                deleteid INT
            );
        """
        logging.info(query)
        self.cursor.execute(query)

        query = """
            CREATE TABLE IF NOT EXISTS emissions (
                hash VARCHAR(64) UNIQUE PRIMARY KEY,
                co2 numeric(8,2),
                car_type VARCHAR(64),
                gas_type VARCHAR(64)
            );
            CREATE INDEX IF NOT EXISTS idx_hash
                ON emissions(hash);
        """
        logging.info(query)
        self.cursor.execute(query)

        self.connect.commit()

        logging.info("Database established")

    def import_data(self):
        """Import data if DATABASE_IMPORT file exists"""
        if not os.path.exists(self.import_file):
            logging.error("No import file present: {}".format(self.import_file))
            return

        logging.info("Deleting existing data")
        self.cursor.execute("DELETE FROM emissions;")
        logging.info("Importing data")
        lastmsg = time.time()
        started = time.time()
        with open(self.import_file, "rt") as fp:
            reader = csv.reader(fp, delimiter=";")
            values = []
            for i, row in enumerate(reader):
                if "-" not in row[0]:
                    continue
                plate = row[0].strip().replace("-", "")
                ct = row[1].strip()
                gt = row[2].strip()
                try:
                    co2 = int(row[3].strip())
                except ValueError:
                    co2 = None

                values.append(
                    self.cursor.mogrify(
                        "(%s,%s,%s,%s)", (create_hash(plate), co2, ct, gt)
                    ).decode("utf-8")
                )
                if i % 50000 == 0:
                    self.cursor.execute(
                        """INSERT INTO emissions(hash, co2, car_type, gas_type)
                       VALUES """
                        + ",".join(values)
                        + """ ON CONFLICT DO NOTHING;"""
                    )
                    self.connect.commit()
                    values = []
                    if time.time() - lastmsg > 10:
                        logging.info("Imported {} records ...".format(i))
                        lastmsg = time.time()

            if len(values) > 0:
                self.cursor.execute(
                    """INSERT INTO emissions(hash, co2, car_type, gas_type)
                       VALUES """
                    + ",".join(values)
                    + """ ON CONFLICT DO NOTHING;"""
                )
                values = []
                self.cursor.execute("SELECT count(*) FROM emissions;")
            if time.time() - lastmsg > 10:
                logging.info(
                    "Imported {} records in {}s".format(i, time.time() - started)
                )
            self.connect.commit()
        return

    def get_cache(self):
        """Get all entries from the database
        Args:
            None
        Returns:
            List: List of entries
        """
        query = """SELECT id,timestamp,data FROM cache ORDER BY timestamp"""

        entries = []
        try:
            self.cursor.execute(query)
            records = self.cursor.fetchall()

            for record in records:
                entry = {}
                entry["id"] = record[0]
                entry[
                    "timestamp"
                ] = datetime.strptime(  # TODO: change data type to date?
                    record[1], "%Y-%m-%d %H:%M:%S.%f"
                )
                entry["data"] = json.loads(record[2])
                entries.append(entry)

        except Exception as e:
            logging.error("DB ERROR:", e)

        return entries

    def delete_cache(self, ids):
        """Delete entries from the database
        Args:
            ids (List): List of database ID column values
        Returns:
            None
        """
        if len(ids) == 0:
            return
        try:
            self.cursor.execute(
                """INSERT INTO cache_delete(deleteid)
                VALUES ("""
                + "),(".join(map(str, ids))
                + """) ON CONFLICT DO NOTHING;"""
            )
            self.connect.commit()
            # TODO: can we query and delete from the same db?
            query = """
                DELETE FROM cache WHERE id IN (SELECT deleteid FROM cache_delete);
                DELETE FROM cache_delete;
            """
            self.cursor.execute(query)

            self.connect.commit()
        except Exception as e:
            logging.error("DB ERROR:", e)
