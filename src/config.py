#!/usr/bin/env python

####################
# Required Modules #
####################

# Generic/Built-in
import os
import subprocess

#############
# Functions #
#############

def get_real_executable_path(exec_name):
    try:
        # Capture the output of the 'which' command.
        symlink_path = subprocess.check_output(["which", exec_name], universal_newlines=True).strip()

        # Get the real path by resolving the symlink.
        real_path = subprocess.check_output(["realpath", symlink_path], universal_newlines=True).strip()

        return real_path
    except subprocess.CalledProcessError:
        return f"{exec_name} not found."

##########
# Script #
##########

tesseract_path = get_real_executable_path("tesseract")
poppler_path = os.path.dirname(get_real_executable_path("pdftotext"))
