import os
import subprocess

timeout = os.getenv("TIMEOUT", "600")
workers = os.getenv("WORKERS", "2")


TZ = os.getenv("TIMEZONE", "Etc/UTC")
assert os.path.exists(
    "/usr/share/zoneinfo/" + TZ
), "Invalid timezone '%s'. See /usr/share/zoneinfo/*" % (TZ,)
with open("/etc/timezone", "wt") as fp:
    fp.write(TZ)
    fp.close()
if os.path.exists("/etc/localtime"):
    os.remove("/etc/localtime")
os.symlink("/usr/share/zoneinfo/" + TZ, "/etc/localtime")

env = os.environ.copy()
env["TZ"] = TZ
env["UID"] = os.getenv("UID")
env["GID"] = os.getenv("GID")

subprocess.call(
    [
        "gunicorn",
        "-b",
        "0.0.0.0:80",
        "--timeout",
        str(timeout),
        "-w",
        str(workers),
        "app:app",
    ],
    env=env,
)
