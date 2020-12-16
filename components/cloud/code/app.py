# -*- coding: utf-8 -*-

import os
import time
from flask import (
    Flask,
    render_template,
    url_for,
    request,
    send_from_directory,
)
import json
from revprox import ReverseProxied
from utils import (
    get_float,
    set_rights,
    is_existing_id,
    safe_name,
    save_data,
    create_folders,
    load_state,
    refresh_state,
)
import logging


app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = os.getenv("APP_KEY", "")
app.config["UID"] = int(os.getenv("UID", 0))
app.config["GID"] = int(os.getenv("GID", 0))
app.config["UPLOAD_PATH"] = "/code/data"
app.config["UPLOAD_TOKEN"] = os.getenv("UPLOAD_TOKEN", "")
app.config["FIRST_RUN"] = True

app.wsgi_app = ReverseProxied(app.wsgi_app)
logging.basicConfig(level=logging.DEBUG)


@app.before_request
def before_request():
    """Create data folders at first request time
        Args:
            None
        Returns:
            None
    """
    if app.config["FIRST_RUN"]:
        create_folders()
        app.config["FIRST_RUN"] = False



@app.route("/hello", methods=["GET"])
def hello():
    """Show hello page. Use to test the server is on.

        Returns:
            str: Hello page.
    """
    return "Hello", 200


@app.route("/upload/", methods=["POST"])
def upload():
    """Accept data to be uploaded. Either JSON format generic data,
       or thumbnails as jpegs from camera
        request.form:
            id (str): Identifier name of camera
            token (str): Secret token to allow uploads
            type (str): "data" for json upload, "small" or "crop" for JPGs
        Returns:
            None
    """
    if request.method == "POST":
        id = request.form["id"]
        token = request.form["token"]
        upload_type = request.form["type"]
        if token != app.config["UPLOAD_TOKEN"]:
            return "", 401
        if upload_type == "data":
            s_filename = safe_name(
                "{}-{}-{}.json".format(id, upload_type, int(time.time()))
            )
            filename = os.path.join(app.config["UPLOAD_PATH"], "data", s_filename)
            logging.info("Saving file {}".format(s_filename))
            save_data(request.form["data"], filename)
            set_rights(filename)

        if upload_type in ("small", "crop"):
            file = request.files["file"]
            if file:
                s_filename = safe_name("{}-{}.jpg".format(id, upload_type))
                filename = os.path.join(app.config["UPLOAD_PATH"], "view", s_filename)
                logging.info("Saving file {}".format(s_filename))
                file.save(filename)
                set_rights(filename)
                return "", 200

    return "", 200


@app.route("/view/<id>/<image>.jpg", methods=["GET"])
def image_view(id, image):
    """Get JPG image from data folder
        Args:
            id (str): Identifier name of camera
            image (str): "small" or "crop" for type of image
        Returns:
            A JPG binary
    """
    try:
        return send_from_directory(
            os.path.join(app.config["UPLOAD_PATH"], "view"),
            filename=safe_name("{}-{}.jpg".format(id, image)),
            as_attachment=True,
        )
    except FileNotFoundError:
        return "", 404


@app.route("/view/<id>", methods=["POST", "GET"])
def view_calibration(id):
    """View control page for a camera
        Args:
            id (str): Identifier name of camera
        Returns:
            HTML page
    """
    # TODO:  if no  session['UPLOAD_TOKEN'], redirect to page that asks one.
    if not is_existing_id(id):
        return "", 404
    small_url = url_for("image_view", id=id, image="small")
    crop_url = url_for("image_view", id=id, image="crop")
    state = load_state(id)
    if request.method == "POST":
        mode = request.form["mode"]
        state["server"]["mode"] = mode
        state["server"]["exposure_modifier"] = round(
            get_float(request.form["exposure_modifier"], 1.0), 2
        )
        refresh_state(id, state["server"], "server")

    state_view = json.dumps(state, indent=4, sort_keys=True)
    return render_template(
        "view.html",
        id=id,
        small_url=small_url,
        crop_url=crop_url,
        state=state,
        state_view=state_view,
    )


@app.route("/state/", methods=["POST"])
def get_set_state():
    """Get the current reported state from a camera
        request.form:
            id (str): Identifier name of camera
            token (str): Secret token to allow viewing of state
        Returns:
            JSON attachment
    """
    if request.method == "POST":
        id = request.form["id"]
        token = request.form["token"]

        if token != app.config["UPLOAD_TOKEN"]:
            return "", 401
        try:
            client_state = json.loads(request.form["state"])
            if refresh_state(id, client_state, "client"):
                return send_from_directory(
                    os.path.join(app.config["UPLOAD_PATH"], "state"),
                    filename=safe_name("{}.json".format(id)),
                    as_attachment=True,
                )
        except FileNotFoundError:
            return "", 404

    return "", 200


@app.route("/ajax/state/<id>", methods=["GET"])
def ajax_get_state(id):
    """Get the current reported state from a camera as a formatted string
        Args:
            id (str): Identifier name of camera
        Returns:
            string
    """
    if not is_existing_id(id):
        return "", 404
    state_view = json.dumps(load_state(id), indent=4, sort_keys=True)
    return state_view, 200


if __name__ == "__main__":
    app.run(debug=True)
