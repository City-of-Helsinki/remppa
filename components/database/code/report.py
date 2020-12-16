from db import DB
import logging
import time
import random


class Reporter:
    """Example Reporter class that will periodically send emission data to an
    API.
     Args:
         db (DB): Database class instance
    """

    def __init__(self, db):
        logging.basicConfig(level=logging.INFO)
        self.interval = 600
        self.db = db

    def get_cache(self):
        """Gets current messages to send
        Args:
            db (DB): Database class instance
        Returns:
            List: list of entries
        """
        return self.db.get_cache()

    def process_cache(self, entries):
        """Process a list of cached entries
        Args:
            entries (List): cached entries
        Returns:
            None
        """
        counted = []
        logging.info("Processing {} entries in cache".format(len(entries)))
        emissions = {"car_count": 0, "co2": 0, "car_types": {}, "gas_types": {}}
        for entry in entries:
            data = entry["data"]
            counted.append(entry["id"])
            emissions["car_count"] += 1
            emissions["co2"] += data["co2"]
            if not data["car_type"] in emissions["car_types"]:
                emissions["car_types"][data["car_type"]] = 0
            if not data["gas_type"] in emissions["gas_types"]:
                emissions["gas_types"][data["gas_type"]] = 0
            emissions["car_types"][data["car_type"]] += 1
            emissions["gas_types"][data["gas_type"]] += 1

        if self.send_emissions(emissions):
            self.db.delete_cache(counted)
        # If sending didnt succeed, count old cache in the next round

    def send_emissions(self, emissions):
        """Send emissions to an API
           TODO:  This part was not implemented
        Args:
            emissions (List): emission data to send
        Returns:
            bool: True if sending was succesful
        """
        # Code that will send entry to a remote location.
        # or just print it..
        logging.info(emissions)

        # Returns False if sending failed:
        if random.random() > 0.8:
            return False
        return True

    def start(self):
        """Start a loop for processing cached emission data"""
        while True:
            entries = self.get_cache()
            self.process_cache(entries)
            time.sleep(self.interval)


if __name__ == "__main__":
    reporter = Reporter(DB())
    reporter.start()
