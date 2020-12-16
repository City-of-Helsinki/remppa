import os
from datetime import datetime
import logging
import stat
import json
from flask import current_app as app


def create_folders():
    """Creates data folders to allow uploads
    Returns:
        None
    """
    try:
        os.mkdir(app.config["UPLOAD_PATH"])
    except Exception as e:
        logging.warning(e)
        pass
    for f in ("view", "data", "state"):
        try:
            os.mkdir(os.path.join(app.config["UPLOAD_PATH"], f))
            set_rights(os.path.join(app.config["UPLOAD_PATH"], f))
        except Exception as e:
            logging.warning(e)
            pass


def set_rights(path):
    """Sets access rights for a file
    Args:
        path (str): file name
    Returns:
        None
    """
    os.chown(path, app.config["UID"], app.config["GID"])
    st = os.stat(path)
    if app.config["UID"] > 0:
        os.chmod(path, st.st_mode | stat.S_IRUSR | stat.S_IWUSR)
    if app.config["GID"] > 0:
        os.chmod(path, st.st_mode | stat.S_IRGRP | stat.S_IWGRP)


def save_data(data, filename):
    """Save JSON data, by reformatting content
    Args:
        data (str): data to save, in JSON string format
        filename (str): path to save to
    Returns:
        None
    """
    with open(filename, "w") as fp:
        json.dump(json.loads(data), fp, indent=4, sort_keys=True)


## State


def is_existing_id(id):
    """Check for id existence
    Args:
        id (str): id name of camera
    Returns:
        bool: True if state file exists
    """
    filename = os.path.join(
        os.path.join(app.config["UPLOAD_PATH"], "state", id + ".json")
    )
    return os.path.exists(filename)


def save_state(state, id):
    """Save state for a named camera
    Args:
        state (Dict): state data to save
        id (str): name of the camera
    Returns:
        None
    """
    filename = os.path.join(
        os.path.join(app.config["UPLOAD_PATH"], "state", id + ".json")
    )
    with open(filename, "w") as fp:
        json.dump(state, fp, indent=4, sort_keys=True)


def load_state(id):
    """Load state for a named camera
    Args:
        id (str): name of the camera
    Returns:
        Dict: state data, defaults to a skeleton state if file not exists
    """
    try:
        filename = os.path.join(
            os.path.join(app.config["UPLOAD_PATH"], "state", id + ".json")
        )
        with open(filename, "r") as fp:
            return json.load(fp)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return {"server": {"mode": "pause"}, "client": {}}


def refresh_state(id, data, endpoint):
    """Refresh state for a named camera
    Args:
        id (str): name of the camera
        state (Dict): new state data
        endpoints (str): Update coming from "server" or "client"
    Returns:
        bool: True if updating state succeeded
    """
    if endpoint not in ("client", "server"):
        return False
    try:
        state = load_state(id)
        state[endpoint].update(data)
        state[endpoint]["refresh"] = datetime.now().strftime("%y-%m-%d %H:%M:%S")
        save_state(state, id)
        return True
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return False
