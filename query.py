import sqlite3

db = sqlite3.connect('einvoice.db')

def check_most_buy():
    sql = 'select inv_goods.name, count(*) as c from inv_item left join inv_goods on inv_item.goods = inv_goods.idx group by inv_item.goods order by c desc'
    result = list(db.execute(sql))
    for r in result:
        print(r)

def check_most_spend():
    sql = 'select inv_goods.name, inv_goods.unitPrice, count(*) as c from inv_item left join inv_goods on inv_item.goods = inv_goods.idx group by inv_item.goods order by c desc'
    result = list(db.execute(sql))
    d = {}
    d.setdefault('拿鐵', [])
    for r in result:
        name = r[0]
        price = r[1]
        count = r[2]
        item = (price, count)
        if '拿鐵' in name or '大冰拿' in name:
            name = '拿鐵'
        if name in d.keys():
            d[name].append(item)
        else:
            d.setdefault(name, [item])
    l = []
    for k, v in d.items():
        total = 0
        count = 0
        for vv in v:
            total += vv[0] * vv[1]
            count += vv[1]
        l.append((k, total, count))
    l.sort(key=lambda x: -x[1])
    total = 0
    for ll in l:
        if ll[2] > 5 and ll[1] > 0:
            print(f'{ll[0]} ==> 總花費: ${ll[1]} 筆數: {ll[2]}')
        total += ll[1]
    print(f'{total=}')

def check_most_where():
    sql = 'select inv_seller.name, count(*) as c from inv_table left join inv_seller on inv_table.seller = inv_seller.ban group by inv_table.seller order by c desc'
    result = list(db.execute(sql))
    for r in result:
        print(r)

check_most_spend()
db.close()