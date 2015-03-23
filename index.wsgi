
# Dynamic Config Section #
# Set Python path in lieu of static settings of
# WSGIPythonPath in web server config.
# In embedded mode this file will be loaded and executed on each request.
# Dynamic config will marginally add to application startup time.
# Note: that to flush application code changes in embedded mode
#   all of the web server processes must be restarted:
#     e.g. service apache2 restart
# In daemon mode changes to this file are loaded and executed once
# into each daemon process. Since code is cached until modified.
import os
import sys
import site

# Absolute dir of this file.
INDEX_DIR = os.path.dirname(os.path.abspath(__file__))

# Virtual environment site packages dir.
VIR_ENV_SITE_PACKAGES = os.path.join(
    INDEX_DIR, 'env', 'lib', 'python2.6', 'site-packages')

assert os.path.isdir(VIR_ENV_SITE_PACKAGES)

ALL_DIRS = [INDEX_DIR, VIR_ENV_SITE_PACKAGES]

prev_sys_path = list(sys.path)

for directory in ALL_DIRS:
    site.addsitedir(directory)

# Reorder sys.path so new directories at the front.
for path in list(sys.path):
    if path not in prev_sys_path:
        sys.path.remove(path)
        sys.path.insert(0, path)

# Ensure index dir is first.
sys.path.remove(INDEX_DIR)
sys.path.insert(0, INDEX_DIR)

# if enabled this will appear in web server error.log
print '-----------------------------------'
print 'Dynamic Config Path:'
for path in sys.path:
    print path
print '-----------------------------------'

# End Dynamic Config Section #

from server import application
