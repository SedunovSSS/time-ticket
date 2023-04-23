from flask import Flask, render_template, request, redirect, make_response
from flask_sqlalchemy import SQLAlchemy
import hashlib, datetime, os, shutil
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.db"
db = SQLAlchemy(app)
HOST = '0.0.0.0'
PORT = 5000
# PHP = кал
admins = open('admins.txt', 'r').read().split('\n')

sender_email = 'timeticket@mail.ru'
sender_password = 'LrLyf0825C9SafGc9Q1L'


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    dateR = db.Column(db.DateTime, default=datetime.datetime.utcnow())

    def __repr__(self):
        return '<Users %r>' % self.id
    

class Tickets(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(150), nullable=False)
    price_simple = db.Column(db.Float, nullable=False)
    price_dish = db.Column(db.Float, nullable=False)
    price_merch = db.Column(db.Float, nullable=False)
    tickets_count_simple =  db.Column(db.Integer, nullable=False)
    tickets_count_dish =  db.Column(db.Integer, nullable=False)
    tickets_count_merch =  db.Column(db.Integer, nullable=False)
    concert_name = db.Column(db.String(150), nullable=False)
    date = db.Column(db.String(150), nullable=False)
    image_path = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(500), nullable=False)

    def __repr__(self):
        return '<Tickets %r>' % self.id
    

class Tickets_in_Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tickets_id = db.Column(db.Integer, nullable=False)
    ticket_type = db.Column(db.String(150), nullable=False)
    author = db.Column(db.String(150), nullable=False)

    def __repr__(self):
        return '<Cart %r>' % self.id
    

class Promo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    sale = db.Column(db.Integer, nullable=False)
    count_promo = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<Promo %r>' % self.id


@app.route('/')
def main():
    name = request.cookies.get('user')
    search = request.args.get('search')
    if name is None:
        return redirect("/login")
    if search is None:
        tickets = list(Tickets.query.all())
        search = ''
    else:
        tickets = []
        for i in list(Tickets.query.all()):
            if search.lower() in i.concert_name.lower() or i.concert_name.lower() in search.lower():
                tickets.append(i)
    if len(tickets) >= 3:
        tickets.reverse()
    elif len(tickets) == 2:
        tickets[0], tickets[1] = tickets[1], tickets[0]
    a = len(list(Tickets_in_Cart.query.filter_by(author=name).all()))
    return render_template("index.html", name=name, tickets=tickets, a=a, search=search)


@app.route('/register', methods=['POST', 'GET'])
def register():
    name = request.cookies.get('user')
    try:
        a = len(list(Tickets_in_Cart.query.filter_by(author=name).all()))
    except:
        a = 0
    if request.method == "POST":
        login = request.form['login']
        email = request.form['email']
        passw1 = request.form['password']
        password = hashlib.md5(passw1.encode("utf-8")).hexdigest()
        exists = db.session.query(Users.id).filter_by(login=login).first() is not None or db.session.query(Users.id).filter_by(email=email).first() is not None
        if not exists:
            user = Users(login=login, password=password, email=email)
            try:
                db.session.add(user)
                db.session.commit()
                resp = make_response(redirect("/"))
                resp.set_cookie('user', user.login)
                return resp
            except Exception as ex:
                print(ex)
                return redirect("/register")
        else:
            return redirect("/register")
    else:
        return render_template("register.html", a=a)


@app.route('/login', methods=['POST', "GET"])
def login():
    name = request.cookies.get('user')
    try:
        a = len(list(Tickets_in_Cart.query.filter_by(author=name).all()))
    except:
        a = 0
    if request.method == "POST":
        login = request.form['login']
        passw1 = request.form['password']
        password = hashlib.md5(passw1.encode("utf-8")).hexdigest()
        exists = db.session.query(Users.id).filter_by(login=login, password=password).first() is not None
        user = db.session.query(Users.login).filter_by(login=login, password=password).first()
        if exists:
            resp = make_response(redirect("/"))
            resp.set_cookie('user', user[0])
            return resp
        else:
            return redirect("/login")
    else:
        return render_template("login.html", a=a)


@app.route('/logout')
def logout():
    resp = make_response(redirect("/login"))
    resp.set_cookie('user', '', expires=0)
    return resp


@app.route('/admin')
def admin():
    name = request.cookies.get('user')
    a = len(list(Tickets_in_Cart.query.filter_by(author=name).all()))
    global admins
    name = request.cookies.get('user')
    admins = open('admins.txt', 'r').read().split('\n')
    if not name in admins:
        return redirect('/login')
    tickets = list(Tickets.query.all())
    if len(tickets) >= 3:
        tickets.reverse()
    elif len(tickets) == 2:
        tickets[0], tickets[1] = tickets[1], tickets[0]
    return render_template('admin.html', tickets=tickets, a=a)


@app.route('/view')
def view():
    name = request.cookies.get('user')
    _type = request.args.get('type')
    a = len(list(Tickets_in_Cart.query.filter_by(author=name).all()))
    concert_name = request.args.get('name')
    date = request.args.get('date')
    ticket = Tickets.query.filter_by(date=date, concert_name=concert_name).first()
    return render_template('view.html', ticket=ticket, a=a, type=_type)


@app.route('/admin/add_ticket', methods=['POST', 'GET'])
def add():
    global admins
    name = request.cookies.get('user')
    a = len(list(Tickets_in_Cart.query.filter_by(author=name).all()))
    admins = open('admins.txt', 'r').read().split('\n')
    if not name in admins:
        return redirect('/login')
    if request.method == 'POST':
        try:
            concert_name = request.form['name']
            description = request.form['description']
            price_simple = float(request.form['price_simple'])
            price_dish = float(request.form['price_dish'])
            price_merch = float(request.form['price_merch'])
            tickets_count_simple = int(request.form['count_simple'])
            tickets_count_dish = int(request.form['count_dish'])
            tickets_count_merch = int(request.form['count_merch'])
            date = request.form['date']
            image = request.files['file[]']
        except:
            return redirect('/admin/add_ticket')
        exists = db.session.query(Tickets.id).filter_by(concert_name=concert_name, date=date).first() is not None
        if exists:
            return redirect('/admin/add_ticket')
        try:
            os.makedirs(f'static/images-tickets/{concert_name}_{date}')
        except:
            pass
        image.save(f'static/images-tickets/{concert_name}_{date}/image.png')
        try:
            ticket = Tickets(concert_name=concert_name, price_simple=price_simple, price_dish=price_dish, price_merch=price_merch, tickets_count_simple=tickets_count_simple, tickets_count_dish=tickets_count_dish, tickets_count_merch=tickets_count_merch, date=date, image_path=f'static/images-tickets/{concert_name}_{date}/image.png', description=description, author=name)
            db.session.add(ticket)
            db.session.commit()
            return redirect('/admin')
        except Exception as _ex:
            print(_ex)
            return redirect('/admin/add_ticket')
    else:
        return render_template('add.html', a=a)


@app.route('/mytickets')
def tickets():
    name = request.cookies.get('user')
    a = len(list(Tickets_in_Cart.query.filter_by(author=name).all()))
    tickets_in_cart = list(Tickets_in_Cart.query.filter_by(author=name).all())
    tickets = []
    all_price=0
    for i in tickets_in_cart:
        obj = Tickets.query.filter_by(id=i.tickets_id).first()
        if not obj is None:
            tickets.append(obj)
            if i.ticket_type == 'simple':
                all_price += obj.price_simple
            elif i.ticket_type == 'dish':
                all_price += obj.price_dish
            else:
                all_price += obj.price_merch

    all_price = round(all_price, 2)
        
    return render_template('mytickets.html', tickets=tickets, a=a, tickets_in_cart=tickets_in_cart, all_price=all_price)


@app.route('/admin/all_users', methods=['POST', 'GET'])
def admin_users():
    global admins
    name = request.cookies.get('user')
    a = len(list(Tickets_in_Cart.query.filter_by(author=name).all()))
    admins = open('admins.txt', 'r').read().split('\n')
    if not name in admins:
        return redirect('/login')
    
    users = Users.query.all()
    return render_template('allusers.html', a=a, admins=admins, users=users)


@app.route('/admin/del_account')
def admin_del_account():
    global admins
    name = request.cookies.get('user')
    admins = open('admins.txt', 'r').read().split('\n')
    if not name in admins:
        return redirect('/login')
    
    try:
        _id = int(request.args.get('id'))
        user = Users.query.filter_by(id=_id).first()
        db.session.delete(user)
        db.session.commit()
    except:
        pass
    return redirect('/admin/all_users')


@app.route('/admin/gimme_admin')
def gimme_admin():
    try:
        global admins
        name = request.cookies.get('user')
        admins = open('admins.txt', 'r').read().split('\n')
        _id = int(request.args.get('id'))
    except:
        return redirect('/admin/all_users')
    if not name in admins:
        return redirect('/login')
    try:
        user = Users.query.filter_by(id=_id).first()
        with open('admins.txt', 'a') as file_admins:
            file_admins.write(f'{user.login}')
    except:
        pass
    return redirect('/admin/all_users')


@app.route('/admin/steal_admin')
def steal_admin():
    try:
        global admins
        name = request.cookies.get('user')
        admins = open('admins.txt', 'r').read().split('\n')
        _id = int(request.args.get('id'))
    except:
        return redirect('/admin/all_users')
    if not name in admins:
        return redirect('/login')
    
    try:
        user = Users.query.filter_by(id=_id).first()
        with open("admins.txt", "r") as f:
            lines = f.readlines()
        with open("admins.txt", "w") as f:
            for line in lines:
                if line.strip("\n") != user.login:
                    f.write(line)
    except:
        pass
    return redirect('/admin/all_users')


@app.route('/admin/edit_ticket', methods=['POST', 'GET'])
def admin_edit_ticket():
    try:
        global admins
        name = request.cookies.get('user')
        a = len(list(Tickets_in_Cart.query.filter_by(author=name).all()))
        admins = open('admins.txt', 'r').read().split('\n')
        _id = int(request.args.get('id'))
        ticket = Tickets.query.filter_by(id=_id).first()
    except:
        return redirect('/admin')
    if not name in admins:
        return redirect('/login')
    if request.method == 'POST':
        try:
            concert_name = request.form['name']
            description = request.form['description']
            price_simple = float(request.form['price_simple'])
            price_dish = float(request.form['price_dish'])
            price_merch = float(request.form['price_merch'])
            tickets_count_simple = int(request.form['count_simple'])
            tickets_count_dish = int(request.form['count_dish'])
            tickets_count_merch = int(request.form['count_merch'])
            date = request.form['date']
            image = request.files['file[]']
        except:
            return redirect('/admin/edit_ticket?id={_id}')
        if ticket.concert_name == concert_name:
            if image:
                os.remove(f'static/images-tickets/{concert_name}_{ticket.date}/image.png')
                image.save(f'static/images-tickets/{concert_name}_{ticket.date}/image.png')
            else:
                os.makedirs(f'static/cache/{concert_name}_{ticket.date}')
                os.rename(ticket.image_path, f'static/cache/{concert_name}_{ticket.date}/image.png')
                os.rmdir(f'static/images-tickets/{concert_name}_{ticket.date}')
                os.makedirs(f'static/images-tickets/{concert_name}_{date}')
                os.rename(f'static/cache/{concert_name}_{ticket.date}/image.png', f'static/images-tickets/{concert_name}_{date}/image.png')
                os.rmdir(f'static/cache/{concert_name}_{ticket.date}')
        else:
            if image:
                os.remove(f'static/images-tickets/{ticket.concert_name}_{ticket.date}/image.png')
                os.rmdir(f'static/images-tickets/{ticket.concert_name}_{ticket.date}')
                os.makedirs(f'static/images-tickets/{concert_name}_{date}')
                image.save(f'static/images-tickets/{concert_name}_{date}/image.png')
            else:
                os.makedirs(f'static/cache/{ticket.concert_name}_{ticket.date}')
                os.rename(ticket.image_path, f'static/cache/{ticket.concert_name}_{ticket.date}/image.png')
                os.rmdir(f'static/images-tickets/{ticket.concert_name}_{ticket.date}')
                os.makedirs(f'static/images-tickets/{concert_name}_{date}')
                os.rename(f'static/cache/{ticket.concert_name}_{ticket.date}/image.png', f'static/images-tickets/{concert_name}_{date}/image.png')
                os.rmdir(f'static/cache/{ticket.concert_name}_{ticket.date}')
            ticket.image_path = f'static/images-tickets/{concert_name}_{date}/image.png'
        try:
            try:
                in_cart = list(Tickets_in_Cart.query.filter_by(tickets_id=_id).all())
                emails = []
                for i in in_cart:
                    emails.append(Users.query.filter_by(login=i.author).first().email)
                for i in emails:
                    msg = MIMEMultipart()
                    msg['From'] = sender_email
                    msg['To'] = i
                    msg['Subject'] = "Time Ticket"
                    body = f'На билете {ticket.concert_name} - {ticket.date} произошли изменения'
                    msg.attach(MIMEText(body, 'plain'))
                    server = smtplib.SMTP('smtp.mail.ru', 587)
                    server.starttls()
                    server.login(sender_email, sender_password)
                    text = msg.as_string()
                    server.sendmail(sender_email, i, text)
                    server.quit()
            except:
                pass
            ticket.concert_name = concert_name
            ticket.price_simple = price_simple
            ticket.price_dish = price_dish
            ticket.price_merch = price_merch
            ticket.tickets_count_simple = tickets_count_simple
            ticket.tickets_count_dish = tickets_count_dish
            ticket.tickets_count_merch = tickets_count_merch
            ticket.date = date
            ticket.description = description
            db.session.commit()
            return redirect('/admin')
        except:
            return redirect(f'/admin/edit_ticket?id={_id}')
    else:
        return render_template('edit.html', ticket=ticket, a=a)



@app.route('/admin/del_ticket')
def admin_delede_ticket():
    try:
        _id = int(request.args.get('id'))
        ticket = Tickets.query.filter_by(id=_id).first()
        shutil.rmtree(ticket.image_path[:-10])
        db.session.delete(ticket)
        db.session.commit()
    except Exception as _ex:
        print(_ex)
    return redirect('/admin')


@app.route('/buy')
def buy():
    try:
        name = request.cookies.get('user')
        a = len(list(Tickets_in_Cart.query.filter_by(author=name).all()))
        _id = request.args.get('id')
        _type = request.args.get('type')
        if id is None:
            return redirect('/')
        _id = int(_id)
        ticket = Tickets.query.filter_by(id=_id).first()
        return render_template('buy.html', ticket=ticket, a=a, type=_type)
    
    except:
        return redirect('/')


@app.route('/buyallcart')
def buy_all_cart():
    try:
        name = request.cookies.get('user')
        tickets_in_cart = list(Tickets_in_Cart.query.filter_by(author=name).all())
        tickets = []
        all_price=0
        for i in tickets_in_cart:
            obj = Tickets.query.filter_by(id=i.tickets_id).first()
            if not obj is None:
                tickets.append(obj)
                if i.ticket_type == 'simple':
                    all_price += obj.price_simple
                elif i.ticket_type == 'dish':
                    all_price += obj.price_dish
                else:
                    all_price += obj.price_merch

        all_price = round(all_price, 2)
        a = len(list(Tickets_in_Cart.query.filter_by(author=name).all()))
        return render_template('buyallcart.html', all_price=all_price, a=a)
    except:
        return redirect('/')


@app.route('/add2cart')
def add2cart():
    name = request.cookies.get('user')
    if name is None:
        return redirect('/login')
    try:
        _id = int(request.args.get('id'))
        _type = request.args.get('type')
        exists = db.session.query(Tickets_in_Cart.id).filter_by(tickets_id=_id, author=name, ticket_type=_type).first() is not None
        if exists:
            print(1)
            return redirect('/')
        ticket = Tickets.query.filter_by(id=_id).first()
        email = Users.query.filter_by(login=name).first().email
        saller_email = Users.query.filter_by(login=Tickets.query.filter_by(id=_id).first().author).first().email
        if _type == 'simple':
            if ticket.tickets_count_simple > 0:
                ticket.tickets_count_simple -= 1
            else:
                return redirect('/')
            
        elif _type == 'dish':
            if ticket.tickets_count_dish > 0:
                ticket.tickets_count_dish -= 1
            else:
                return redirect('/')
            
        else:
            if ticket.tickets_count_merch > 0:
                ticket.tickets_count_merch -= 1
            else:
                return redirect('/')
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = "Time Ticket"
        if _type == 'simple':
            ticket_type = 'Обычный'
        elif _type == 'dish':
            ticket_type = 'С едой'
        else:
            ticket_type = 'С мерчем'
        body = f'Вы купили {ticket.concert_name} - {ticket.date} - {ticket_type}'
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP('smtp.mail.ru', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, email, text)
        server.quit()
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = Users.query.filter_by(login=ticket.author).first().email
        msg['Subject'] = "Time Ticket"
        body = f'У вас купили {ticket.concert_name} - {ticket.date} - {ticket_type}'
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP('smtp.mail.ru', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, saller_email, text)
        server.quit()

        cart = Tickets_in_Cart(tickets_id=_id, author=name, ticket_type=_type)
        db.session.add(cart)
        db.session.commit()
       
        return redirect('/mytickets')
    except Exception as _ex:
        print(_ex)
        return redirect('/')
    

@app.route('/delfromcart')
def del_from_cart():
    try:
        name = request.cookies.get('user')
        _id = int(request.args.get('id'))
        _type = request.args.get('type')
        ticket = Tickets.query.filter_by(id=_id).first()
        if _type == 'simple':
            ticket.tickets_count_simple += 1
        elif _type == 'dish':
            ticket.tickets_count_dish += 1
        else:
            ticket.tickets_count_merch += 1
        
        ticket = Tickets.query.filter_by(id=_id).first()
        if _type == 'simple':
            ticket_type = 'Обычный'
        elif _type == 'dish':
            ticket_type = 'С едой'
        else:
            ticket_type = 'С мерчем'
        email = Users.query.filter_by(login=name).first().email
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = Users.query.filter_by(login=ticket.author).first().email
        msg['Subject'] = "Time Ticket"
        body = f'Вы отказались от покупки {ticket.concert_name} - {ticket.date} - {ticket_type}'
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP('smtp.mail.ru', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, email, text)
        server.quit()
        cart = Tickets_in_Cart.query.filter_by(tickets_id=_id, ticket_type=_type).first()
        db.session.delete(cart)
        db.session.commit()
        return redirect('/mytickets')
    except Exception as _ex:
        print(_ex)
        return redirect('/')


@app.route('/participants')
def participants():
    name = request.cookies.get('user')
    a = len(list(Tickets_in_Cart.query.filter_by(author=name).all()))
    concert_name = request.args.get('name')
    date = request.args.get('date')
    try:
        ticket = Tickets.query.filter_by(concert_name=concert_name, date=date).first()
        nicknames_ = list(Tickets_in_Cart.query.filter_by(tickets_id=ticket.id))
        temp = []
        
        for i in nicknames_:
            if [Users.query.filter_by(login=i.author).first().login, Users.query.filter_by(login=i.author).first().email] not in temp:
                temp.append([Users.query.filter_by(login=i.author).first().login, Users.query.filter_by(login=i.author).first().email])

        nicknames = temp
        return render_template('patricipants.html', nicknames=nicknames, concert_name=concert_name, date=date, a=a)
    except Exception as _ex:
        print(_ex)
        return redirect('/')
    

@app.route('/admin/add_promo',  methods=['POST', 'GET'])
def add_promo():
    global admins
    name = request.cookies.get('user')
    a = len(list(Tickets_in_Cart.query.filter_by(author=name).all()))
    admins = open('admins.txt', 'r').read().split('\n')
    if not name in admins:
        return redirect('/login')
    if request.method == 'POST':
        try:
            concert_name = request.form['name']
            sale = request.form['sale']
            count_promo = float(request.form['count_promo'])
        except:
            return redirect('/admin/add_promo')
        exists = db.session.query(Promo.id).filter_by(name=concert_name).first() is not None
        if exists:
            return redirect('/admin/add_promo')
        
        try:
            promo = Promo(name=concert_name, sale=sale, count_promo=count_promo)
            db.session.add(promo)
            db.session.commit()
            return redirect('/admin/all_promo')
        except Exception as _ex:
            print(_ex)
            return redirect('/admin/add_promo')
    else:
        return render_template('add_promo.html', a=a)


@app.route('/admin/all_promo')
def all_promo():
    global admins
    name = request.cookies.get('user')
    admins = open('admins.txt', 'r').read().split('\n')
    if not name in admins:
        return redirect('/login')
    a = len(list(Tickets_in_Cart.query.filter_by(author=name).all()))
    promo = Promo.query.all()
    return render_template('allpromo.html', admins=admins, promo = promo, a=a)    


@app.route('/admin/del_promo')
def del_promo():
    global admins
    name = request.cookies.get('user')
    admins = open('admins.txt', 'r').read().split('\n')
    if not name in admins:
        return redirect('/login')
    
    try:
        _id = int(request.args.get('id'))
        promo = Promo.query.filter_by(id=_id).first()
        db.session.delete(promo)
        db.session.commit()
    except:
        pass
    return redirect('/admin/all_promo')


if __name__ == '__main__':
    app.run(debug=True, host=HOST, port=PORT)
