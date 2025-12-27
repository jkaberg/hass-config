import sys
from homeassistant.util.package import install_package

if "/config/pyscript/modules" not in sys.path:
    sys.path.append("/config/pyscript/scripts")
    sys.path.append("/config/pyscript/modules")

@time_trigger
def install_pkgs():
    # Install a package on PyPi. Accepts pip compatible package strings.
    pkgs = [
        "icalendar",
        "aiofile",
        "pyyaml",
    ]

    for pkg in pkgs:
        # https://github.com/home-assistant/core/blob/dev/homeassistant/util/package.py#L64
        install_package(package=pkg)