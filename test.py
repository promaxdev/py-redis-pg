import requests
import time
from requests.auth import HTTPBasicAuth

url = "http://localhost:4747/inbound/sms"
outurl = "http://localhost:4747/outbound/sms"
paramString = "?from={0}&to={1}&text={2}"
toErrString = "?from={0}&text={1}"
fromErrString = "?to={0}&text={1}"
textErrString = "?from={0}&to={1}"

user = "azr1"
passwd = "20S0KPNOIM"

def printCase(name, actual, expected):
    printCase.caseno += 1
    result = '*FAIL*'
    if expected == actual:
        result = 'PASSED'
        print(printCase.caseno, name, result)
    else:
        print(printCase.caseno, name, result, actual, expected)

printCase.caseno = 0

name = 'METHODS'
auth_values = HTTPBasicAuth(user, passwd)
response = requests.get(url, auth=auth_values)
printCase(name, response.status_code, 405)


auth_values = HTTPBasicAuth(user, passwd)
response = requests.delete(url, auth=auth_values)
printCase(name, response.status_code, 405)


name = 'AUTH'
auth_values = HTTPBasicAuth(user, 'funny')
response = requests.post(url, auth=auth_values)
printCase(name, response.status_code, 403)

name = 'INPARAM'
auth_values = HTTPBasicAuth(user, passwd)
response = requests.post(url+paramString.format('121324323','4924195509012', '23214234'), auth=auth_values)
actual = response.json()
printCase(name, response.status_code, 200)
printCase(name, actual, {'message': 'inbound sms ok', 'error': ''})

auth_values = HTTPBasicAuth(user, passwd)
response = requests.post(url+toErrString.format('121324323','2324321421', '23214234'), auth=auth_values)
actual = response.json()
printCase(name, response.status_code, 400)
printCase(name, actual, {'message': '', 'error': 'to is missing'})

auth_values = HTTPBasicAuth(user, passwd)
response = requests.post(url+fromErrString.format('121324323','2324321421', '23214234'), auth=auth_values)
actual = response.json()
printCase(name, response.status_code, 400)
printCase(name, actual, {'message': '', 'error': 'from is missing'})

auth_values = HTTPBasicAuth(user, passwd)
response = requests.post(url+textErrString.format('121324323','2324321421', '23214234'), auth=auth_values)
actual = response.json()
printCase(name, response.status_code, 400)
printCase(name, actual, {'message': '', 'error': 'text is missing'})



name = 'STOP'
auth_values = HTTPBasicAuth(user, passwd)
response = requests.post(url+paramString.format('12','2324321421', '23214234'), auth=auth_values)
actual = response.json()
printCase(name, response.status_code, 400)
printCase(name, actual, {'message': '', 'error': 'from is invalid'})

auth_values = HTTPBasicAuth(user, passwd)
response = requests.post(url+paramString.format('121324323','232432142145436546464', '23214234'), auth=auth_values)
actual = response.json()
printCase(name, response.status_code, 400)
printCase(name, actual, {'message': '', 'error': 'to is invalid'})

auth_values = HTTPBasicAuth(user, passwd)
response = requests.post(url+paramString.format('121324323','2324321421', ''), auth=auth_values)
actual = response.json()
printCase(name, response.status_code, 400)
printCase(name, actual, {'message': '', 'error': 'text is invalid'})

auth_values = HTTPBasicAuth(user, passwd)
stopCacheNo = ['4924195509198', '4924195509012']
response = requests.post(url+paramString.format(stopCacheNo[0],stopCacheNo[1], 'hello'), auth=auth_values)
actual = response.json()
printCase(name, response.status_code, 200)
printCase(name, actual, {'message': 'inbound sms ok', 'error': ''})
response = requests.post(url+paramString.format(stopCacheNo[0],stopCacheNo[1], 'STOP'), auth=auth_values)
actual = response.json()
printCase(name, response.status_code, 200)
printCase(name, actual, {'message': 'inbound sms ok', 'error': ''})
response = requests.post(outurl+paramString.format(stopCacheNo[1], stopCacheNo[0], 'world'), auth=auth_values)
actual = response.json()
printCase(name, response.status_code, 200)
printCase(name, actual, {'message': '', 'error': 'sms from {0} to {1} blocked by STOP request'.format(stopCacheNo[1], stopCacheNo[0])})
time.sleep(6)
response = requests.post(outurl+paramString.format(stopCacheNo[1], stopCacheNo[0], 'new world'), auth=auth_values)
actual = response.json()
printCase(name, response.status_code, 200)
printCase(name, actual, {'message': 'outbound sms ok', 'error': ''})

name = 'COUNT'
auth_values = HTTPBasicAuth(user, passwd)
fromNo = '31297728125'
countTo = ['3253280312', '3253280311', '3253280315']
response = requests.post(outurl+paramString.format(fromNo, countTo[0], 'world'), auth=auth_values)
actual = response.json()
printCase(name, response.status_code, 200)
printCase(name, actual, {'message': 'outbound sms ok', 'error': ''})
response = requests.post(outurl+paramString.format(fromNo, countTo[1], 'world'), auth=auth_values)
actual = response.json()
printCase(name, response.status_code, 200)
printCase(name, actual, {'message': 'outbound sms ok', 'error': ''})
response = requests.post(outurl+paramString.format(fromNo, countTo[2], 'world'), auth=auth_values)
actual = response.json()
printCase(name, response.status_code, 200)
printCase(name, actual, {'message': '', 'error': 'limit reached for from {0}'.format(fromNo)})
time.sleep(6)
response = requests.post(outurl+paramString.format(fromNo, countTo[2], 'world'), auth=auth_values)
actual = response.json()
printCase(name, response.status_code, 200)
printCase(name, actual, {'message': 'outbound sms ok', 'error': ''})

name = 'PHNO'
auth_values = HTTPBasicAuth(user, passwd)
response = requests.post(url+paramString.format('3253280311','9999999', '23214234'), auth=auth_values)
actual = response.json()
printCase(name, response.status_code, 200)
printCase(name, actual, {'message': '', 'error': 'to parameter not found'})

auth_values = HTTPBasicAuth(user, passwd)
response = requests.post(outurl+paramString.format('9999999','3253280311', '23214234'), auth=auth_values)
actual = response.json()
printCase(name, response.status_code, 200)
printCase(name, actual, {'message': '', 'error': 'from parameter not found'})
