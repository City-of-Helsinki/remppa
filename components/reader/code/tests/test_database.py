from DB import Database


def test_get_vehicles():
    DB = Database()

    assert DB.get_vehicles() is not None


def test_plate_hash():
    DB = Database()
    plate0 = DB.get_vehicles()[0]

    if plate0:
        assert DB.hash_exists(plate0[0])
