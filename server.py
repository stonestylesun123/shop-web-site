import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
import sys

reload( sys )
sys.setdefaultencoding('utf-8')

DEBUG = True
SECRET_KEY = '8\x01\xa7Ry\xf6H\x8f^\xea\xd11\x7f\xc9\xa3\x88%\xf4\xae@\xd8\xd2!'

app = Flask(__name__)
app.config.from_object(__name__)


def account_connect_db():
    connection = sqlite3.connect('database/account.db')
    connection.text_factory = str
    return connection

def shopdata_connect_db():
    connection = sqlite3.connect('database/shopdata.db')
    connection.text_factory = str
    return connection


@app.before_first_request
def before_first_request():
    g.shop_db = shopdata_connect_db()

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'account_db'):
        g.account_db.close()
    if hasattr(g, 'shop_db'):
        g.shop_db.close()


@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')
    
@app.route('/about')
def about():
    return render_template('about.html')
    
@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/shop')
def shop():
    g.shop_db = shopdata_connect_db()
    sort = str(request.args.get('sort',''))
    if sort is None or sort is "":
        cur = g.shop_db.execute('select shopname, shopprice, shopstar from shopdata order by id')
        entries = [dict(shopname=row[0], shopprice=row[1], shopstar=[1]*row[2]) for row in cur.fetchall()]
        return render_template('shop.html', entries=entries)
    elif sort == 'shopstar':
        cur = g.shop_db.execute('select shopname, shopprice, shopstar from shopdata order by shopstar desc')
        entries = [dict(shopname=row[0], shopprice=row[1], shopstar=[1]*row[2]) for row in cur.fetchall()]
        return render_template('shop.html', entries=entries)
    elif sort == 'shopname':
        cur = g.shop_db.execute('select shopname, shopprice, shopstar from shopdata order by shopname')
        entries = [dict(shopname=row[0], shopprice=row[1], shopstar=[1]*row[2]) for row in cur.fetchall()]
        return render_template('shop.html', entries=entries)
    elif sort == 'shopprice':
        cur = g.shop_db.execute('select shopname, shopprice, shopstar from shopdata order by shopprice')
        entries = [dict(shopname=row[0], shopprice=row[1], shopstar=[1]*row[2]) for row in cur.fetchall()]
        return render_template('shop.html', entries=entries)
    else:
        return "error sort!"


@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/addaccount', methods=['POST'])
def add_account():
    g.account_db = account_connect_db()
    g.account_db.execute('insert into account (username, password) values (?,?)', [request.form['username'], request.form['password']])
    g.account_db.commit()
    session['username'] = request.form['username']
    session['logged_in'] = True
    return render_template('shop.html')
    

@app.route('/search', methods=['GET'])
def search():
    g.shop_db = shopdata_connect_db()
    searchword = request.args.get('tag','')
    cur = g.shop_db.execute('select shopname, shopprice, shopstar from shopdata where tag = ?', [searchword])
    entries = [dict(shopname=row[0], shopprice=row[1], shopstar=[1]*row[2]) for row in cur.fetchall()]
    return render_template('shop.html', entries=entries, search=searchword)
    
@app.route('/shopmessage', methods=['GET'])
def shopmessage():
    g.shop_db = shopdata_connect_db()
    shopname = request.args.get('shopname','')
    cur = g.shop_db.execute('select shopname, shopprice, shopdes, shopstar, tag, id from shopdata where shopname = ?', [shopname])
    entries = [dict(shopname=row[0], shopprice=row[1], shopdes=row[2], shopstar=[1]*row[3], tag=row[4], id=row[5]) for row in cur.fetchall()]
    return render_template('shopmessage.html', entries=entries)
    

'''
a function to change sql data to shopcart data.
eg.
    "2:1##3:2"      -->     {"2":1, "3":2}
            ""      -->     {}
'''
def SQLtocart(sqldata=""):
    if sqldata == '':
        return {}
    else:
        tmp = sqldata.split("##")
        result = {}
        for i in tmp:
            i = i.split(':')
            result[i[0]] = int(i[1])
        return result
        
'''
a function to change shopcart data to sql data.
eg.
    {"2":1, "3":2}      -->     "2:1##3:2"
                {}      -->     ""   
'''
def CARTtoSQL(cart=""):
    if len(cart) == 0:
        return ""
    else:
        tmp = []
        for i in cart:
            string = i + ':' + str(cart[i])
            tmp.append(string)
        return '##'.join(tmp)

'''
get the total price of the shopcart of the current user through session attr.
'''
def getprice():
    if islogged():
        g.account_db = account_connect_db()
        g.shop_db = shopdata_connect_db()
        shopprice = 0
        username = session['username']
        cur = g.account_db.execute('select shopcart from account where username = ?', [username])
        result = cur.fetchone()
        shopcart = result[0]
        shopcart = SQLtocart(shopcart)
        if len(shopcart) == 0: return 0
        for i in shopcart:
            cur = g.shop_db.execute('select shopprice from shopdata where id = ?', [i])
            shopprice += cur.fetchone()[0] * shopcart[i]
        return shopprice


def updatecart(cart):
    if islogged():
        g.account_db = account_connect_db()
        g.shop_db = shopdata_connect_db()
        username = session['username']
        cur = g.account_db.execute('select shopcart from account where username = ?', [username])
        result = cur.fetchone()
        shopcart = result[0]
        shopcart = SQLtocart(shopcart)
        cart = SQLtocart(cart)
        if len(shopcart) == 0: shopcart = CARTtoSQL(cart)
        else:
            for i in cart:
                if i in shopcart:
                    shopcart[i] += int(cart[i])
                else:
                    shopcart[i] = int(cart[i])
            shopcart = CARTtoSQL(shopcart)
        g.account_db.execute('update account set shopcart = ? where username = ?', [shopcart, session['username']])
        g.account_db.commit()
        session['total'] = getprice()
        
        
@app.route('/addshop', methods=['POST'])
def addshop():
    id = request.form['id']
    num = request.form['quantity']
    tmp = str(id) + ':' + str(num)
    updatecart(tmp)
    return redirect(url_for('shopmanager'))
    
@app.route('/deleteshop', methods=['GET'])
def deleteshop():
    if islogged():
        g.account_db = account_connect_db()
        g.shop_db = shopdata_connect_db()
        shopid = request.args.get('shopid','')
        
        username = session['username']
        cur = g.account_db.execute('select shopcart from account where username = ?', [username])
        result = cur.fetchone()
        shopcart = result[0]
        shopcart = SQLtocart(shopcart)
        print "shopid:",shopid,type(shopid)
        print "shopcart:",shopcart,type(shopcart)
        del shopcart[str(shopid)]
        shopcart = CARTtoSQL(shopcart)
        g.account_db.execute('update account set shopcart = ? where username = ?', [shopcart, session['username']])
        g.account_db.commit()
        session['total'] = getprice()
        return redirect(url_for('shopmanager'))
        
    else:
        return redirect(url_for('signin'))
    
    
@app.route('/shopmanager')
def shopmanager():
    if islogged():
        g.account_db = account_connect_db()
        g.shop_db = shopdata_connect_db()
        entries = []
        username = session['username']
        cur = g.account_db.execute('select shopcart from account where username = ?', [username])
        result = cur.fetchone()
        shopcart = result[0]
        shopcart = SQLtocart(shopcart)
        length = len(shopcart)
        if length == 0: entries = []
        else:
            count = 1
            for i in shopcart:
                cur = g.shop_db.execute('select shopname, shopprice from shopdata where id = ?', [i])
                result = cur.fetchall()
                for row in result:
                    entries.append(dict(orderid=count, shopname=row[0], shopprice=row[1], shopquantity=shopcart[i], entryprice=shopcart[i] * row[1], shopid=i))
                count += 1
        return render_template('shopmanager.html', entries=entries, number=length)
    else:
        return redirect(url_for('signin'))
        

def islogged():
    if 'logged_in' in session and session['logged_in']:
        return True
    else:
        return False

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        g.account_db = account_connect_db()
        username = request.form['username']
        password = request.form['password']
        cur = g.account_db.execute('select password from account where username = ?', [username])
        result = cur.fetchone()
        if result == None:
            return render_template('signin.html', error="No such user!")
        if str(password) == result[0]:
            session['logged_in'] = True
            session['username'] = username
            session['total'] = getprice()
            return redirect(url_for('home'))
        else:
            return render_template('signin.html', error="Wrong password!")
    else:
        return render_template('signin.html')

@app.route('/signout')
def signout():
    if 'logged_in' in session:
        session.pop('logged_in', None)
    if 'username' in session:
        session.pop('username', None)
    if 'total' in session:
        session.pop('total', None)
    
    return redirect(url_for('home'))
    
if __name__ == '__main__':
    app.run(host='0.0.0.0')
