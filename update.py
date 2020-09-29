import datetime
import json
import requests
import time
import sqlite3

APPID = ''
APPKEY = ''
CODE = ''
PASSWORD = ''
UUID = ''

URL = r'https://www.einvoice.nat.gov.tw/PB2CAPIVAN/invServ/InvServ'

def timestamp():
    return str((int)(datetime.datetime.now().timestamp()) * 1000)

def expTimestamp():
    return str((int)(datetime.datetime.now().timestamp() + 180) * 1000)

def get_json_by_params(params):
    while True:
        response = requests.post(URL, data=params)
        if response.status_code == 200:
            result = json.loads(response.text)
            code = int(result['code'])
            if code == 200:
                return result
            else:
                raise Exception('code ' + str(code))
        else:
            raise Exception('response.status_code= ' + str(response.status_code))

def get_list_by_data(start:str, end:str):
    params = {
        'version' : '0.5',
        'cardType' : '3J0002', # 手機條碼
        'cardNo' : CODE,
        'expTimeStamp' : expTimestamp(),
        'action' : 'carrierInvChk',
        'timeStamp' : timestamp(),
        'startDate' : start,
        'endDate' : end,
        'onlyWinningInv' : 'N',
        'uuid' : UUID,
        'appID' : APPID,
        'cardEncrypt' : PASSWORD,
    }
    return get_json_by_params(params)

def get_detail(invNum:str, invDate:str):
    params = {
        'version' : '0.5',
        'cardType' : '3J0002', # 手機條碼
        'cardNo' : CODE,
        'expTimeStamp' : expTimestamp(),
        'action' : 'carrierInvDetail',
        'timeStamp' : timestamp(),
        'invNum' : invNum,
        'invDate' : invDate,
        'uuid' : UUID,
        'appID' : APPID,
        'cardEncrypt' : PASSWORD,
    }
    return get_json_by_params(params)

def to_timestamp(item) -> int:
        (h, m, s) = item["invoiceTime"].split(':')
        t = time.localtime(item['invDate']['time'] / 1000)
        return int(time.mktime((t.tm_year, t.tm_mon, t.tm_mday, int(h), int(m), int(s), t.tm_wday, t.tm_yday, t.tm_isdst)))

def db_check_str_exist(db, table, colwant, colname, data):
    sql = f'select {colwant} from {table} where {colname} = "{data}"'
    result = list(db.execute(sql))
    if len(result) == 0:
        return None
    else:
        return result[0]

def check_seller_and_add(db, ban, name, address):
    if not db_check_str_exist(db, 'inv_seller', 'ban', 'ban', ban):
        db.execute('insert into inv_seller values (?,?,?)', (ban, name, address))
        db.commit()

def handle(result:dict, db:sqlite3.Connection):
    for item in result['details']:
        invNum = item['invNum']
        amount = item['amount']
        seller = item['sellerBan']
        invDate = to_timestamp(item)
        check_seller_and_add(db, seller, item['sellerName'], item['sellerAddress'])
        if not db_check_str_exist(db, 'inv_table', 'invNum', 'invNum', invNum):
            print(f'add inv num = {invNum}')
            db.execute('insert into inv_table values (?,?,?,?)', (invNum, invDate, amount, seller))
            db.commit()
        if not db_check_str_exist(db, 'inv_item', 'invNum', 'invNum', invNum):
            print(f'add inv detail num = {invNum}')
            detail = get_detail(invNum, time.strftime('%Y/%m/%d', time.localtime(invDate)))
            for g in detail['details']:
                name = g['description']
                price = g['amount']
                goods_index = 0
                while not goods_index:
                    sql = f'select idx from inv_goods where name = "{name}" and unitPrice = {price}'
                    goods_index = list(db.execute(sql))
                    if len(goods_index) == 0:
                        db.execute(f'insert into inv_goods (name,unitPrice) values (?,?)', (name, price))
                        db.commit()
                goods_index = goods_index[0][0]
                db.execute(f'insert into inv_item (invNum, goods, quantity) values (?,?,?)', (invNum, goods_index, g['quantity']))

db = sqlite3.connect('einvoice.db')
result = get_list_by_data('2020/9/01', '2020/10/31')
handle(result, db)
db.commit()
db.close()