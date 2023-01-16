import os
import sys

# we need our modules!
if "/config/pyscript/modules" not in sys.path:
    sys.path.append("/config/pyscript/modules")

# install necessary packages :-)
@time_trigger("startup")
def install_pkgs():
    os.system("pip3 --quiet install icalendar aiofile > /dev/null 2>&1")