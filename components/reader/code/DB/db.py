import json
import logging
import os
import psycopg2


class Database:
    """Database handling class

    Args read from environment variables
        POSTGRES_DB: Database name
        POSTGRES_PASSWORD: Database password
        POSTGRES_USER: Database user name
        POSTGRES_HOST: Database server host name
        POSTGRES_PORT: Database server port number
        INSTALLATION_ADDRESS: Unique identifier for this device instance
    """
    def __init__(self):
        self.database = os.getenv("POSTGRES_DB")
        self.password = os.getenv("POSTGRES_PASSWORD")
        self.user = os.getenv("POSTGRES_USER")
        self.host = os.getenv("POSTGRES_HOST")
        self.port = int(os.getenv("POSTGRES_PORT"))
        self.connect = None
        self.cursor = None
        self.retries = 3
        self.address = os.getenv("INSTALLATION_ADDRESS", "")
        self.connect_db()

    def connect_db(self):
        """Connect to database

        """
        connect_str = "dbname='{}' user='{}' host='{}' password='{}'".format(
            self.database, self.user, self.host, self.password
        )

        self.connect = psycopg2.connect(connect_str)
        self.cursor = self.connect.cursor()

    def get_vehicle(self, hash):
        """Get data related to a vehicle hashed plate

        Args:
            hash (str): Hashed license plate
        Returns:
            List: List of emission values
        """
        query = """SELECT hash,co2,car_type,gas_type FROM emissions WHERE hash = %s;"""

        try:
            vehicle = {}

            self.cursor.execute(query, (hash,))
            record = self.cursor.fetchone()

            if record:
                try:
                    vehicle["co2"] = float(record[1])
                except Exception as e:
                    vehicle["co2"] = 100  # TODO: Handle missing values
                    logging.error(str(e))

                vehicle["car_type"] = record[2]
                vehicle["gas_type"] = record[3]

                return vehicle
        except Exception as e:
            logging.error("DB ERROR:", e)

        return None

    def get_vehicles(self):
        """Get all vehicle hashed plates

        Returns:
            List: List of hashes values
        """

        query = """SELECT hash FROM emissions"""

        try:
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Exception as e:
            logging.error("DB ERROR:", e)

    def hash_exists(self, hash):
        """Check if vehicle hashed plate exists

        Args:
            hash (str): Hashed license plate
        Returns:
            bool: Is found in the database
        """

        query = """SELECT count(hash) FROM emissions WHERE hash = %s;"""

        try:
            self.cursor.execute(query, (hash,))
            return self.cursor.fetchone()[0] > 0
        except Exception as e:
            logging.error("DB ERROR:", e)

    def write_cache(self, timestamp, data):
        """Writes objects to the cache database

        Args:
            timestamp (float): Timestamp of the emission detection
            data (Dict): Emission values for the vehicle
        Returns:
            None

        """

        query = """INSERT INTO cache (timestamp, data)
            VALUES (%s,%s);"""

        try:
            self.cursor.execute(
                query,
                (
                    timestamp,
                    json.dumps(data, ensure_ascii=False),
                ),
            )
            self.connect.commit()
            return
        except Exception as e:
            logging.error("DB ERROR:", e)
