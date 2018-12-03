# CMake generated Testfile for 
# Source directory: /home/coen/git/charon
# Build directory: /home/coen/git/charon/_build_armhf
# 
# This file includes the relevant testing commands required for 
# testing this directory and lists subdirectories to be tested as well.
add_test(pytest-main "/usr/bin/python3" "-m" "pytest" "--junitxml=/home/coen/git/charon/_build_armhf/junit-pytest-main.xml" "/home/coen/git/charon/tests")
set_tests_properties(pytest-main PROPERTIES  ENVIRONMENT "PYTHONPATH=/home/coen/git/charon::/home/coen/git/charon")
