# py-redis-pg
Simple case study using postgre python and redis

# Prerequisites
Following need to be installed before this sample can be tried
Postgre Server
Python 3.x preferrably > 3.5
Redis 4

# Importing Test Data
Get the SQL from the below location
https://gist.githubusercontent.com/kumaresan-plivo/928368f0cd97b0a35c79d91948491747/raw/954ef7f33226bba969720c537892e7464bc7d8ec/testdatadump.sql

From commandline connect to PostgreSQL
I assume postgres ans the user name and database name

$ sudo su - postgres

Your prompt would show postgres as the user

$ psql

The prompt would change to 

postgres=#

postgres=# use postgres

postgres=# \i testdatadump.sql

You are done with import. You will have two tables 'account' and 'phone_number' created. You can verify the same using

postgres=# \i select * from account;


# Setup Python environment

Run the following pip from your command prompt

pip install flask Flask-SQLAlchemy Flask-HTTPAuth requests redis psycopg2

Note: you would be better off creating a virtualenv and then using the above command if you dont want to disturb your existing python setup

We are good now.

# Executing tests

Open api.py and go to line 26 which would look like this

DB_URL = 'postgresql+psycopg2://{user}:{pw}@{host}/{db}'.format(user='----',pw='----',host='---',db='---')

Replace the ---- with values corresponding to your configuration.

In separate command prompts execute the following

$ python3 api.py --dev

Note: Skipping '--dev' switch would make tests take very long time ~ 1 day and a test case to fail

In another command prompt execute
$ python3 test.py

These tests should show pass.
