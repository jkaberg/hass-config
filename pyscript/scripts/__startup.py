import os

# install necessary packages :-)
@time_trigger("startup")
def install_pkgs():
    os.system("pip3 install icalendar aiofile")