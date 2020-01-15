#!/bin/bash 

# This script loads the necessary python packages into pip's user space
# for use with the James Madison University computer science lab machines
# which do not allow students to install python packages with administrative
# access. 
#
# It also enables the widgetsnbextension which is necessary to get the
# jupyter widgets running properly on the lab machines.

pip3 install --user wheel
pip3 install --user ipycanvas ipywidgets ipyevents dataclasses

jupyter nbextension enable --py widgetsnbextension
