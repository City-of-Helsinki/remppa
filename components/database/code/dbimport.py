from db import DB

if __name__ == "__main__":
    db = DB()
    db.create_tables()
    db.import_data()
