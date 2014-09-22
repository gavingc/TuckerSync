INSTALL
=======

Currently project setup is a checkout from github.

Then create a virtualenv that can be accessed from the project root directory (<PROJECT_DIR>/env):

    # Either directly:

    cd <PROJECT_DIR>
    curl https://pypi.python.org/packages/source/v/virtualenv/virtualenv-1.11.6.tar.gz | tar xz
    python virtualenv-1.11.6/virtualenv.py env
    rm -R virtualenv-1.11.6
    
    # OR symlinked (my preference):
    
    cd /usr/local/bin
    curl https://pypi.python.org/packages/source/v/virtualenv/virtualenv-1.11.6.tar.gz | tar xz
    python virtualenv-1.11.6/virtualenv.py python-virtualenv-tucker-sync
    ln -s python-virtualenv-tucker-sync <PROJECT_DIR>/env
    # rm virtualenv-1.11.6 not required in this case.
    
Install dependencies in the virtualenv:

    cd <PROJECT_DIR>
    env/bin/pip install -r requirements.txt

For more on virtualenv and also deploying see:
http://www.kromhouts.net/blog/python/python-shared-hosting/

Project files for IntelliJ IDEA or PyCharm are included.
Add the new virtualenv as an SDK and set it as the project SDK in project settings.
