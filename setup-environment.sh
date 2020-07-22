#!/bin/sh

# run this script from root directory of repo
# after setting up the Python virtual environment
# to generate additional necessary resources

# convert PyQt5 `.ui` files to Python code
pyuic5 src/main/python/ayab/about_gui.ui -o src/main/python/ayab/about_gui.py
pyuic5 src/main/python/ayab/firmware_flash_gui.ui -o src/main/python/ayab/firmware_flash_gui.py
pyuic5 src/main/python/ayab/main_gui.ui -o src/main/python/ayab/main_gui.py
pyuic5 src/main/python/ayab/menu_gui.ui -o src/main/python/ayab/menu_gui.py
pyuic5 src/main/python/ayab/mirrors_gui.ui -o src/main/python/ayab/mirrors_gui.py
pyuic5 src/main/python/ayab/prefs_gui.ui -o src/main/python/ayab/prefs_gui.py
pyuic5 src/main/python/ayab/engine/dock_gui.ui -o src/main/python/ayab/engine/dock_gui.py
pyuic5 src/main/python/ayab/engine/options_gui.ui -o src/main/python/ayab/engine/options_gui.py
pyuic5 src/main/python/ayab/engine/status_gui.ui -o src/main/python/ayab/engine/status_gui.py

# generate PyQt5 resource file
pyrcc5 src/main/python/ayab/ayab_logo_rc.qrc -o src/main/python/ayab/ayab_logo_rc.py

# generate translation files
cd src/main/resources/base/ayab/translations/
./ayab_trans.pl
