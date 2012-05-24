#! /usr/bin/env python
# coding: utf-8
# @author stone
# @version V1.0

import sqlite3

'''
a function to add shop records into the sqlite3 database --- database/shopdata.db.
'''
def connect():
    return sqlite3.connect('database/shopdata.db')

def main():
    connection = connect()
    connection.text_factory = str
    shopfile = open('shop.txt','r')
    contents = shopfile.readlines()
    count = 0
    for entry in contents:
        print
        print "%d----------------------------" % count
        tmp = entry.split('##')
        tmp[4] = tmp[4].rstrip()
        tmp[1] = int(tmp[1])
        tmp[3] = int(tmp[3])
        count += 1
        connection.execute('insert into shopdata (shopname, shopprice, shopdes, shopstar, tag) values (?,?,?,?,?)', tmp)
        connection.commit()
    connection.close()
    
def test():
    connection = connect()
    cur = connection.execute('select * from shopdata')
    tmp = cur.fetchall()
    print tmp
    connection.close()

if __name__ == '__main__':
    main()
    #test()
