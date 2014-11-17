INSTALL
=======

Currently project setup is a checkout from github:

    git clone https://github.com/gavingc/TuckerSync.git

Then create a virtualenv that can be accessed from the project root directory (TuckerSync/env):

    # Either directly:

    cd TuckerSync
    curl https://pypi.python.org/packages/source/v/virtualenv/virtualenv-1.11.6.tar.gz | tar xz
    python virtualenv-1.11.6/virtualenv.py env
    rm -R virtualenv-1.11.6

    # OR symlinked (my preference):

    cd /usr/local/bin
    curl https://pypi.python.org/packages/source/v/virtualenv/virtualenv-1.11.6.tar.gz | tar xz
    python virtualenv-1.11.6/virtualenv.py python-virtualenv-tucker-sync
    cd TuckerSync
    ln -s /usr/local/bin/python-virtualenv-tucker-sync env
    # rm virtualenv-1.11.6 not required in this case.

Install dependencies in the virtualenv:

    cd TuckerSync
    env/bin/pip install -r requirements.txt

For more on virtualenv and also deploying see:  
http://www.kromhouts.net/blog/python/python-shared-hosting/

Run server and tests:

Shell 1:
    
    cd TuckerSync
    ./server.py  

Shell 2:
    
    cd TuckerSync
    ./tests.py

Project files for IntelliJ IDEA or PyCharm are included.  
Add the new virtualenv as an SDK and set it as the project SDK in project settings.
