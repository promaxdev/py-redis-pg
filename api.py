from flask import Flask, abort, request, Response, jsonify, g, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from functools import wraps
import re
import redis
from time import time
import sys

app = Flask(__name__)
redis_db = redis.StrictRedis(host="localhost", port=6379, db=0)
auth = HTTPBasicAuth()

HOURS_IN_SECS = 60 * 60
MINS_IN_SECS = 60

STOP_EXPIRY_IN_SECS = 4 * HOURS_IN_SECS
FROM_EXPIRY_IN_SECS = 24 * HOURS_IN_SECS
MAX_SMS_COUNT = 50

if len(sys.argv) > 1 and '--dev' in sys.argv:
    STOP_EXPIRY_IN_SECS = 5
    FROM_EXPIRY_IN_SECS = 5
    MAX_SMS_COUNT = 2

DB_URL = 'postgresql+psycopg2://{user}:{pw}@{url}/{db}'.format(user='postgres',pw='postgres',url='localhost',db='postgres')

app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL #'postgresql://localhost/postgres'
db = SQLAlchemy(app)

class Account(db.Model):
    __tablename__ = "account"
    id = db.Column(db.Integer, primary_key=True)
    auth_id = db.Column(db.String(40))
    username = db.Column(db.String(30))

    def __init__(self, auth_id, username):
        self.auth_id = auth_id
        self.username = username

    def __repr__(self):
        return '<Name %r>' % self.username

class PhoneNumber(db.Model):
    __tablename__ = "phone_number"
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.String(40))
    number = db.Column(db.Integer)

    def __init__(self, account_id, number):
        self.account_id = account_id
        self.number = number

    def __repr__(self):
        return '<number %r>' % self.number


users = Account.query.all()
ph_nos = PhoneNumber.query.all()
print(users)
#print(ph_nos)


def check_phone(number):
    for phone in ph_nos:
        #print(phone.number - number)
        if phone.number == number:
            return True
    return False


def check_auth(username, password):
    passwd = ''
    for user in users:
        if user.username == username:
            return password == user.auth_id
    return False

def loginErrorResponse():
    return Response('Could not verify user.', 403,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return loginErrorResponse()
        return f(*args, **kwargs)
    return decorated


def validateFrom(args):
    if 'from' in args:
        fromNo = args['from']
        regx = '[1-9](\d{5,15})$'
        result = re.match(regx, fromNo)
        if result is None or len(result.groups()) < 1 :
            return 'from is invalid'
        return True
    else:
        return 'from is missing'

def validateTo(args):
    if 'to' in args:
        toNo = args['to']
        regx = '[1-9](\d{5,15})$'
        result = re.match(regx, toNo)
        #print(result)
        if result is None or len(result.groups()) < 1 :
            return 'to is invalid'
        return True
    else:
        return 'to is missing'

def validateText(args):
    if 'text' in args:
        text = args['text']
        strLen = len(text)
        #print('text len', strLen)
        if strLen < 1 or strLen > 120 :
            return 'text is invalid'
        return True
    else:
        return 'text is missing'

def getStopKey(fromNo, toNo):
    return "-".join(['STOP', fromNo, toNo])

def getTimestampKey(fromNo):
    return "-".join(['TS', fromNo])

def getCountKey(fromNo):
    return "-".join(['COUNT', fromNo])

def isParamsValid(args):
    valid = validateFrom(args)

    if valid == True:
        valid = validateTo(args)
    else:
        return valid

    if valid == True:
        valid = validateText(args)
    else:
        return valid

    return valid


@app.route('/inbound/sms', methods=['POST'])
@requires_auth
def inbound_sms():
    valid = isParamsValid(request.args)
    responseMsg = {'message':'', 'error':''}
    if valid == True:
        responseMsg['message'] = 'inbound sms ok'
    else:
        responseMsg['error'] = valid
        return (jsonify(responseMsg), 400)

    text = request.args['text']
    fromNo = request.args['from']
    toNo = request.args['to']

    if check_phone(toNo) == False:
        #print('to param lookup', toNo, int(toNo))
        responseMsg['error'] = 'to parameter not found'
        responseMsg['message'] = ''
        return (jsonify(responseMsg), 200)

    if text.strip() == 'STOP':
        key = getStopKey(fromNo,toNo)
        if redis_db.get(key) is None:
            redis_db.setex(key, '1', STOP_EXPIRY_IN_SECS)

    return (jsonify(responseMsg), 200)

@app.route('/outbound/sms', methods=['POST'])
@requires_auth
def outbound_sms():
    #sentTime = time()
    valid = isParamsValid(request.args)
    responseMsg = {'message':'', 'error':''}
    if valid == True:
        responseMsg['message'] = 'outbound sms ok'
    else:
        responseMsg['error'] = valid
        return (jsonify(responseMsg), 400)

    text = request.args['text']
    fromNo = request.args['from']
    toNo = request.args['to']

    if check_phone(fromNo) == False:
        #print('to param lookup', toNo, int(toNo))
        responseMsg['error'] = 'from parameter not found'
        responseMsg['message'] = ''
        return (jsonify(responseMsg), 200)

    stopkey = getStopKey(toNo, fromNo)
    if redis_db.get(stopkey) is not None:
        responseMsg['error'] = 'sms from {0} to {1} blocked by STOP request'.format(fromNo,toNo)
        responseMsg['message'] = ''
        return (jsonify(responseMsg), 200)

    tskey = getTimestampKey(fromNo)
    storedTs = redis_db.get(tskey)
    countKey = getCountKey(fromNo)
    if storedTs is None:
        redis_db.setex(tskey, '1', FROM_EXPIRY_IN_SECS)
        redis_db.set(countKey, '1')
        #redis_db.incr(countKey)
        responseMsg['error'] = ''
        responseMsg['message'] = 'outbound sms ok'
        return (jsonify(responseMsg), 200)
    else:
        counts = int(redis_db.get(countKey))
        #print(counts)
        if counts < MAX_SMS_COUNT:
            responseMsg['error'] = ''
            responseMsg['message'] = 'outbound sms ok'
            redis_db.set(countKey, str(counts + 1))
        else:
            redis_db.delete(countKey)
            responseMsg['error'] = 'limit reached for from {0}'.format(fromNo)
            responseMsg['message'] = ''
        return (jsonify(responseMsg), 200)

    #return (jsonify(responseMsg), 200)



if __name__ == '__main__':
    app.run(debug=True, port=4747)
