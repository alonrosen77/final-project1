import os,sqlite3,random,json,logging
from flask import Flask
from flask import redirect, url_for, render_template, request


app = Flask(__name__)
logging.basicConfig(filename="data.log",level=logging.DEBUG,format='%(asctime)s::%(levelname)s::%(message)s')

#this function show the user the sign-in/up page
@app.route('/')
def home_page():
    logging.info("the user is in the home page")
    return render_template('hello.html')

#this function check the user inputs from the sign-in/up page and show him the main page of the website
#in the main page he can see his flights and chose if he want to buy/delete anothe flights
@app.route('/main',methods=['POST'])
def main_page():
    global user_name,user_password,user_id
    conn = sqlite3.connect(r"C:\Users\Alon\Desktop\project-sql.db")
    try:
       user_name = request.form['name']
       logging.info("user enter name successfully")
    except:
        logging.error("something went wrong wtih the user name")
        return render_template(('error.html'))
    try:
       user_password = request.form['password']
       logging.info("user enter password successfully")
    except:
        logging.error("something went wrong with the user password")
        return render_template('error.html')
    try:
        user_id = request.form['id']
        logging.info("this is a new user")
    except :
        user_real_password = conn.execute('SELECT password FROM users WHERE "fullname" = ?',(user_name,))
        logging.info("the user already exists, now we want to see if the password that entered and the on in the db are equal")
        user_real_password = user_real_password.fetchall()
        # check if the password matches the one that is in the database
        if user_real_password[0][0] != user_password:
            logging.info("user entered the wrong password")
            return render_template('error.html')
        else:
            logging.info("user entered the right password now he will go inside the website")
            user_id = conn.execute('SELECT real_id FROM users WHERE "password" = ?',(user_real_password[0][0],)).fetchall()
            id_AI = conn.execute(f'SELECT id_AI FROM users WHERE real_id = "{user_id[0][0]}"').fetchall()
            user_data = conn.execute(f'SELECT timestamp,name FROM users JOIN tickets on tickets.user_id = {int(id_AI[0][0])}'
                                     ' JOIN flights on flights.flight_id = tickets.flight_id'
                                     ' JOIN countries on countries.code_AI = flights.dest_country_id').fetchall()
            new_dict ={}
            num_of_flights =[]
            for i in range(len(user_data)//2):
                new_dict.update({f"{user_data[i][0]}":f"{user_data[i][1]}"})
                num_of_flights.append(user_data[i][1])
            return render_template('main-page.html',name=user_name,flights=len(num_of_flights) ,d=new_dict)
    else:
        # put the new user details inside the database and let him inside the website
        conn.execute(f'INSERT INTO users (fullname,password,real_id) VALUES("{user_name}","{user_password}","{user_id}")')
        conn.commit()
        logging.info("insert into the database the new user inputs")
        return render_template('main-page.html',name=user_name,flights=0,d=None)
    conn.close()



#this function is handling the user choice. wether he wants to buy/delete ticket
@app.route('/buy-delete.html',methods=['POST'])
def tickets_data():
    conn = sqlite3.connect(r"C:\Users\Alon\Desktop\project-sql.db")
    user_choice = request.form['choice']
    if user_choice == "buy":
        list_of_countries =  conn.execute("SELECT name FROM countries").fetchall()
        logging.info("the user decided to buy ticket, and we show him where he can fly")
        conn.close()
        return render_template('buy.html',countries = list_of_countries)
    elif user_choice == "delete":
        conn.close()
        logging.info("the user wants to delete a ticket")
        return render_template('delete.html')
    else:
        conn.close()
        logging.error("the user put a wrong input")
        return render_template('error.html')


#handling deleting ticket
@app.route('/deleting.html',methods=['POST'])
def delete_ticket():
    ticket_id = int(request.form['ticket-id'])
    conn = sqlite3.connect(r"C:\Users\Alon\Desktop\project-sql.db")
    conn.execute('DELETE FROM tickets WHERE "ticket_id" = ?',(ticket_id,))
    conn.commit()
    conn.close()
    logging.info("the ticket was deleted!")
    return render_template('deleted.html')

#handling buying ticket
@app.route('/chose.html',methods=['POST'])
def choose_ticket():
    conn = sqlite3.connect(r"C:\Users\Alon\Desktop\project-sql.db")
    country_flight = request.form['country']
    list_of_flights = conn.execute(f'SELECT * FROM flights JOIN countries on dest_country_id = countries.code_AI WHERE "name" = "{country_flight}"').fetchall()
    conn.close()
    logging.info("after the user chose where to go, now he can chose a specific flight which is most comftarble to him")
    return render_template('chose-flight.html',flights = list_of_flights)

@app.route('/finish.html',methods=['POST'])
def bought_ticket():
    conn = sqlite3.connect(r"C:\Users\Alon\Desktop\project-sql.db")
    flight_id = int(request.form['chosen-flight'])
    user_id = int(request.form['id'])
    user_id_AI = conn.execute('SELECT id_AI FROM users WHERE "real_id" = ?',(user_id,)).fetchall()
    user_id_AI = int(user_id_AI[0][0])
    remianing_seats = conn.execute('SELECT remaing_seats FROM flights WHERE "flight_id" = ?',(flight_id,)).fetchall()
    remianing_seats = int(remianing_seats[0][0])
    print(remianing_seats)
    if remianing_seats > 0:
        remianing_seats -= 1
        print(remianing_seats)
        conn.execute(f'INSERT INTO tickets (user_id,flight_id) VALUES("{user_id_AI}","{flight_id}")')
        conn.commit()
        conn.execute(f'UPDATE flights set remaing_seats = {remianing_seats} WHERE flight_id = {flight_id}')
        conn.commit()
        conn.close()
        logging.info("there was enough seats on the flight so the ticket bought successfully")
        return render_template('success.html')
    else:
        conn.close()
        logging.info("there was no seats left")
        return render_template('fail.html')



#all the other http requests for every table

#users
@app.route('/data/users', methods = ['POST','GET'])
def get_post_data():
    conn = sqlite3.connect(r"C:\Users\Alon\Desktop\project-sql.db")
    list_of_data = conn.execute('SELECT * FROM users').fetchall()
    updated_list = []
    for i in range(len(list_of_data)):
        new_dict = {'id_AI': list_of_data[i][0], 'name': list_of_data[i][1], 'password': list_of_data[i][2],
                    'real_id': list_of_data[i][3]}
        updated_list.append(new_dict)
    if request.method == 'GET':
        conn.close()
        logging.info("get all the users")
        return json.dumps(updated_list)
    if request.method == 'POST':
        new_user = request.get_json(force=True)
        updated_list.append(new_user)
        conn.execute(f'INSERT INTO users (fullname,password,real_id) VALUES("{new_user["name"]}","{new_user["password"]}","{new_user["real_id"]}")')
        conn.commit()
        conn.close()
        logging.info("post all the user with new one we got")
        return json.dumps(updated_list)

@app.route('/data/users/<int:id>', methods=['PUT', 'DELETE','GET'])
def get_put_delete_data(id):
    conn = sqlite3.connect(r"C:\Users\Alon\Desktop\project-sql.db")
    list_of_data = conn.execute('SELECT * FROM users').fetchall()
    updated_list = []
    for i in range(len(list_of_data)):
        new_dict = {'id_AI': list_of_data[i][0], 'name': list_of_data[i][1], 'password': list_of_data[i][2],
                    'real_id': list_of_data[i][3]}
        updated_list.append(new_dict)
    if request.method == 'DELETE':
        for k in range(len(updated_list)):
            if updated_list[k]['id_AI'] == id:
                updated_list.pop(k)
                conn.execute(f'DELETE FROM users WHERE "id_AI" = {id}')
                conn.commit()
                conn.close()
                logging.info("delete one of the users")
                return json.dumps(updated_list)
    elif request.method == 'GET':
        for k in range(len(updated_list)):
            if updated_list[k]['id_AI'] == id:
                conn.close()
                logging.info("get a specific user")
                return json.dumps(updated_list[k])
    elif request.method == 'PUT':
        for k in range(len(updated_list)):
            if updated_list[k]['id_AI'] == id:
                updated_user = request.get_json(force=True)
                updated_list[k]['name'] = updated_user['name']
                updated_list[k]['password'] = updated_user['password']
                updated_list[k]['real_id'] = updated_user['real_id']
                conn.execute(f'UPDATE users SET fullname = "{updated_user["name"]}",password ="{updated_user["password"]}",real_id = "{updated_user["real_id"]}" WHERE id_AI ={id}')
                conn.commit()
                logging.info("change a specific user")
        conn.close()
        return json.dumps(updated_list)


#tickets
@app.route('/data/tickets', methods = ['POST','GET'])
def get_post_data2():
    conn = sqlite3.connect(r"C:\Users\Alon\Desktop\project-sql.db")
    list_of_data = conn.execute('SELECT * FROM tickets').fetchall()
    updated_list = []
    for i in range(len(list_of_data)):
        new_dict = {'ticket_id':list_of_data[i][0],'user_id':list_of_data[i][1],'flight_id':list_of_data[i][2]}
        updated_list.append(new_dict)
    if request.method == 'GET':
        conn.close()
        logging.info("get all tickets")
        return json.dumps(updated_list)
    if request.method == 'POST':
        new_user = request.get_json(force=True)
        print(new_user["user_id"],new_user["flight_id"])
        updated_list.append(new_user)
        conn.execute(f'INSERT INTO tickets (user_id,flight_id) VALUES({new_user["user_id"]},{new_user["flight_id"]})')
        conn.commit()
        conn.close()
        logging.info("post all tickets with new one")
        return json.dumps(updated_list)
    conn.close()

@app.route('/data/tickets/<int:id>', methods=[ 'DELETE','GET'])
def get_put_delete_data2(id):
    conn = sqlite3.connect(r"C:\Users\Alon\Desktop\project-sql.db")
    list_of_data = conn.execute('SELECT * FROM tickets').fetchall()
    updated_list = []
    for i in range(len(list_of_data)):
        new_dict = {'ticket_id':list_of_data[i][0],'user_id':list_of_data[i][1],'flight_id':list_of_data[i][2]}
        updated_list.append(new_dict)
    if request.method == 'DELETE':
        for k in range(len(updated_list)):
            if updated_list[k]['ticket_id'] == id:
                updated_list.pop(k)
                conn.execute(f'DELETE FROM tickets WHERE "ticket_id" ={id}')
                conn.commit()
                conn.close()
                logging.info("delete a specific ticket")
                return json.dumps(updated_list)
    elif request.method == 'GET':
        for k in range(len(updated_list)):
            if updated_list[k]['ticket_id'] == id:
                conn.close()
                logging.info("get a specific ticket")
                return json.dumps(updated_list[k])

#flights
@app.route('/data/flights', methods = ['POST','GET'])
def get_post_data3():
    conn = sqlite3.connect(r"C:\Users\Alon\Desktop\project-sql.db")
    list_of_data = conn.execute('SELECT * FROM flights').fetchall()
    updated_list = []
    for i in range(len(list_of_data)):
        new_dict = {'flight_id':list_of_data[i][0],'timestamp':list_of_data[i][1],'remaining_seats':list_of_data[i][2],
                    'origin_counry_id':list_of_data[i][3],'dest_country_id':list_of_data[i][4]}
        updated_list.append(new_dict)
    if request.method == 'GET':
        conn.close()
        logging.info("get all flights")
        return json.dumps(updated_list)
    if request.method == 'POST':
        new_user = request.get_json(force=True)
        updated_list.append(new_user)
        conn.execute(f'INSERT INTO flights (timestamp,remaing_seats,origin_country_id,dest_country_id) VALUES("{new_user["timestamp"]}","{new_user["remaining_seats"]}",{new_user["origin_country_id"]},{new_user["dest_country_id"]})')
        conn.commit()
        conn.close()
        logging.info("post all flights with the new one")
        return json.dumps(updated_list)

@app.route('/data/flights/<int:id>', methods=['PUT', 'DELETE','GET'])
def get_put_delete_data3(id):
    conn = sqlite3.connect(r"C:\Users\Alon\Desktop\project-sql.db")
    list_of_data = conn.execute('SELECT * FROM flights').fetchall()
    updated_list = []
    for i in range(len(list_of_data)):
        new_dict = {'flight_id':list_of_data[i][0],'timestamp':list_of_data[i][1],'remaining_seats':list_of_data[i][2],
                    'origin_counry_id':list_of_data[i][3],'dest_country_id':list_of_data[i][4]}
        updated_list.append(new_dict)
    if request.method == 'DELETE':
        for k in range(len(updated_list)):
            if updated_list[k]['flight_id'] == id:
                updated_list.pop(k)
                conn.execute(f'DELETE FROM flights WHERE "flight_id" = {id}')
                conn.commit()
                conn.close()
                logging.info("delete a specific flight")
                return json.dumps(updated_list)
    elif request.method == 'GET':
        for k in range(len(updated_list)):
            if updated_list[k]['flight_id'] == id:
                conn.close()
                logging.info("get a specific flight")
                return json.dumps(updated_list[k])
    elif request.method == 'PUT':
        for k in range(len(updated_list)):
            if updated_list[k]['flight_id'] == id:
                updated_user = request.get_json(force=True)
                updated_list[k]['timestamp'] = updated_user['timestamp']
                updated_list[k]['remaining_seats'] = updated_user['remaining_seats']
                updated_list[k]['origin_country_id'] = updated_user['origin_country_id']
                updated_list[k]['dest_country_id'] = updated_user['dest_country_id']
                conn.execute(f'UPDATE flights SET timestamp = "{updated_user["timestamp"]}",remaing_seats = "{updated_user["remaining_seats"]}",origin_country_id = "{updated_user["origin_country_id"]}",dest_country_id = "{updated_user["dest_country_id"]}" WHERE flight_id ={id}')
                conn.commit()
                conn.close()
                logging.info("change a specific flight")
        return json.dumps(updated_list)

#countries
@app.route('/data/countries', methods = ['POST','GET'])
def get_post_data4():
    conn = sqlite3.connect(r"C:\Users\Alon\Desktop\project-sql.db")
    list_of_data = conn.execute('SELECT * FROM countries').fetchall()
    updated_list = []
    for i in range(len(list_of_data)):
        new_dict = {'code_AI':list_of_data[i][0],'name':list_of_data[i][1]}
        updated_list.append(new_dict)
    if request.method == 'GET':
        conn.close()
        logging.info("get all countries")
        return json.dumps(updated_list)
    if request.method == 'POST':
        new_user = request.get_json(force=True)
        print(new_user)
        updated_list.append(new_user)
        conn.execute(f'INSERT INTO countries (name) VALUES ("{new_user["name"]}")')
        conn.commit()
        conn.close()
        logging.info("post all countries with the new one")
        return json.dumps(updated_list)

@app.route('/data/countries/<int:id>', methods=['PUT', 'DELETE','GET'])
def get_put_delete_data4(id):
    conn = sqlite3.connect(r"C:\Users\Alon\Desktop\project-sql.db")
    list_of_data = conn.execute('SELECT * FROM countries').fetchall()
    updated_list = []
    for i in range(len(list_of_data)):
        new_dict = {'code_AI':list_of_data[i][0],'name':list_of_data[i][1]}
        updated_list.append(new_dict)
    if request.method == 'DELETE':
        for k in range(len(updated_list)):
            if updated_list[k]['code_AI'] == id:
                updated_list.pop(k)
                conn.execute(f'DELETE FROM countries WHERE "code_AI" = {id}')
                conn.commit()
                conn.close()
                logging.info("delete a specific flight")
                return json.dumps(updated_list)
    elif request.method == 'GET':
        for k in range(len(updated_list)):
            if updated_list[k]['code_AI'] == id:
                conn.close()
                logging.info("get a specific flight")
                return json.dumps(updated_list[k])
    elif request.method == 'PUT':
        for k in range(len(updated_list)):
            if updated_list[k]['code_AI'] == id:
                updated_user = request.get_json(force=True)
                updated_list[k]['name'] = updated_user['name']
                conn.execute(f'UPDATE countries SET name = "{updated_user["name"]}" WHERE code_AI = {id}')
                conn.commit()
                conn.close()
                logging.info("change a specific flight")
        return json.dumps(updated_list)


app.run()
