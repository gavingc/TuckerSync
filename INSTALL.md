INSTALL
=======

Currently project setup is a checkout from github:

    git clone https://github.com/gavingc/TuckerSync.git


**Virtualenv**

Then create a virtualenv that can be accessed from the project root directory (TuckerSync/env):

Either directly in the project directory:

    cd TuckerSync
    curl https://pypi.python.org/packages/source/v/virtualenv/virtualenv-1.11.6.tar.gz | tar xz
    python virtualenv-1.11.6/virtualenv.py env
    rm -R virtualenv-1.11.6

OR symlinked (my preference):

    mkdir -p ~/bin/
    cd ~/bin/
    curl https://pypi.python.org/packages/source/v/virtualenv/virtualenv-1.11.6.tar.gz | tar xz
    python virtualenv-1.11.6/virtualenv.py python-virtualenv-tucker-sync
    cd TuckerSync
    ln -s ~/bin/python-virtualenv-tucker-sync env
    # rm virtualenv-1.11.6 not required in this case.

**Requirements**

Install dependencies in the virtualenv:

    cd TuckerSync
    env/bin/pip install -r requirements.txt --allow-external mysql-connector-python

For more on virtualenv and also deploying see:  
http://www.kromhouts.net/blog/python/python-shared-hosting/
    
**Database**

Create a MySQL database and user:

    $ mysql -p -u root
    CREATE DATABASE tucker_sync_dev;
    USE tucker_sync_dev;
    GRANT ALL ON tucker_sync_dev.* TO tuckersyncadmin@localhost IDENTIFIED BY 'tuckersyncadmin';
    flush privileges;
    quit;
    
Check:

    $ mysql -p -u tuckersyncadmin tucker_sync_dev

**Setup**

Run application setup:

    cd TuckerSync
    ./app_setup.py
    
This will copy the template config file and create the database tables.

***Run Server and Tests***

The Python server and client implementations can now be run from the command line.

Shell #1:
    
    cd TuckerSync
    ./server.py  

Shell #2:
    
    cd TuckerSync
    ./tests.py

**IDE**

Project files for IntelliJ IDEA or PyCharm are included.  
Add the new virtualenv as an SDK and set it as the project SDK in project settings.

**Customise**

See app_model.py to define logical data objects for your application.
