# Mingyue Wei
from flask import Flask,jsonify,request,url_for
import json,datetime

app = Flask(__name__)
database = []
coffee={"latte":3,"Espresso":4,"Double Espresso":6,"Short Macchiato":7,"Long Macchiato":6,"Ristretto":5,"Long Black":6,"Cappuccino":4,"Mocha":5,"Affogato":5,"Flat White":7,"Piccolo Latte":5}
order_id = 1

class Order:
    def __init__(self, id, type_coffee, cost, additions, status, coffee_status,next):
        self.id = id
        self.type_coffee = type_coffee
        self.cost = cost
        self.additions = additions
        self.status = status
        self.coffee_status = coffee_status
        self.next = next

class Payment:
    def __init__(self, id, type_payment, amount, cardNo, expires, name, coffee_status):
        self.id = id
        self.type_payment = type_payment
        self.amount = amount
        self.cardNo = cardNo
        self.expires = expires
        self.name = name
        self.coffee_status = coffee_status

#create order
@app.route("/coffee/create/order", methods=['POST'])
def create_order():
    global order_id
    data=request.get_data().decode()
    try:
        data=json.loads(data)
        if (type(data['type_coffee']) == str):
            data['id'] = order_id
            data['status'] = "unpaid"
            data['coffee_status'] = "not_started"
            data['additions'] = ""
            if data['type_coffee'] in coffee:
                myCost = coffee[data['type_coffee']]
            else:
                return jsonify("Sorry, we do not have what you order. The following is our menu.",coffee,), 400
            data['cost'] = myCost
            data['next'] = url_for('update_order',id=order_id)
            order_id += 1
            database.append(
                Order(data['id'], data['type_coffee'], float(myCost), data['additions'], data['status'],
                      data['coffee_status'], data['next']))
            return jsonify(data), 201
        return jsonify("You do not successfully create the order."),400
    except Exception as e:
        return jsonify("Data is not valid."),400

#get all the list of orders
@app.route("/coffee/get/orders", methods=['GET'])
def get_all_orders():
    if database!=[]:
        return jsonify([st.__dict__ for st in database]),200
    else:
        return jsonify("We do not have any orders."),404

#get specific order
@app.route("/coffee/get/order/<int:id>", methods=['GET'])
def get_single_order(id):
    for st in database:
        if (st.id==id):
            return jsonify(st.__dict__),200
    return jsonify("The order is not exist."),404

#barista gets all open order
@app.route("/coffee/get/openorders", methods=['GET'])
def get_all_open_orders():
    result = list()
    for i in database:
        if i.coffee_status!="released":
            result.append(i.__dict__)
    if len(result) > 0:
        return jsonify(result), 200
    return jsonify("We do not have open orders."), 404

#barista gets specific open orders
@app.route("/coffee/get/openorder/<int:id>", methods=['GET'])
def get_single_open_order(id):
    for st in database:
        if (st.coffee_status!="released" and st.id==id):
            return jsonify(st.__dict__),200
    return jsonify("The order is not exist."),404

#update specfic order
@app.route("/coffee/update/order/<int:id>", methods=['put'])
def update_order(id):
    data = request.get_data().decode()
    try:
        data = json.loads(data)
        for st in database:
            if (st.id == id):
                if (st.status=="unpaid" and st.coffee_status=="not_started"):
                    if data['type_coffee'] in coffee:
                        myCost = coffee[data['type_coffee']]
                        st.type_coffee = data['type_coffee']
                        st.additions = data['additions']
                        st.cost = myCost
                        st.next = url_for('create_payment', id=st.id)
                        return jsonify(st.__dict__), 200
                    else:
                        return jsonify("sorry, we do not have what you order. The following is our menu.", coffee), 400
        return jsonify("You can not amend the order details."), 400
    except:
        return jsonify("Data is not valid."),400

#pick up specific order
@app.route("/coffee/pickup/order/<int:id>", methods=['patch'])
def pickup_order(id):
    for st in database:
        if (st.id == id):
            if (st.status=="paid" or st.status=="unpaid"):
                if (st.coffee_status!="released"):
                    st.coffee_status="picked_up"
                    return jsonify(st.__dict__), 200
                return jsonify("The order has been released."), 400
    return jsonify("The order dose not exist."), 400

#check if the order is paid and release otherwise will not release the order
@app.route("/coffee/release/order/<int:id>", methods=['patch'])
def release_order(id):
    for st in database:
        if (st.id == id):
            if (st.status=="paid" and st.coffee_status=="picked_up"):
                st.coffee_status="released"
                return jsonify(st.__dict__), 200
            if st.coffee_status=="released":
                return jsonify("The order has been released."), 400
            if st.coffee_status=="unpaid":
                return jsonify("The order has not been paid."), 400
    return jsonify("The order dose not exist or the coffee has not been picked up."), 400

#delete specific order
@app.route("/coffee/delete/order/<int:id>", methods=['DELETE'])
def delete_order(id):
    for st in database:
        if (st.id == id and st.status == "unpaid"):
            database.remove(st)
            return jsonify("You have successfully deleted the order."), 200
    return jsonify("The order has been paid or the order dose not exist."), 404

#create payment for specific order
@app.route("/coffee/payment/order/<int:id>", methods=['put'])
def create_payment(id):
    data = request.get_data().decode()
    try:
        data = json.loads(data)
        if (data['type_payment']):
            for st in database:
                if (st.id == id and st.status=="unpaid" and data['type_payment']=="card"):
                    if (data['cardNo'] and data['name'] and data['expires'] and  type(data['cardNo'])==int and type(data['name']==str) and datetime.datetime.strptime(data['expires'], '%Y-%m-%d')):
                        currentdate = datetime.datetime.now().date()
                        inputdate = datetime.datetime.strptime(data['expires'], '%Y-%m-%d')
                        if (inputdate.date() > currentdate):
                            st.status="paid"
                            st.type_payment = data['type_payment']
                            st.cardNo = data['cardNo']
                            st.name = data['name']
                            st.expires = data['expires']
                            st.amount = st.cost
                            st.next=""
                            return jsonify(id=st.id, type_payment=st.type_payment, cardNo=st.cardNo, name=st.name,
                                           expires=st.expires, amount=st.amount), 200
                        return jsonify("Your card has expired."), 400
                    return jsonify("Please fill out the card info and using correct type."),400
                if (st.id == id and st.status == "unpaid" and data['type_payment'] == "cash"):
                    st.status = "paid"
                    st.amount = st.cost
                    st.type_payment=data['type_payment']
                    st.next = ""
                    return jsonify(id=st.id, type_payment=st.type_payment,amount=st.amount), 200
            return jsonify("You can only pay the payment by cash or card or You have paid for the order."),400
        return jsonify("Please select a payment type."),400
    except:
        return jsonify("Data is not valid."),400

#get the payment details of the a specific order
@app.route("/coffee/get/payment/<int:id>", methods=['GET'])
def get_payment(id):
    for st in database:
        if (st.id == id  and st.status=="paid" and st.type_payment=="card"):
            return jsonify(id=st.id,type_payment=st.type_payment,cardNo=st.cardNo,name=st.name,expires=st.expires,amount=st.amount),200
        if (st.id == id  and st.status=="paid" and st.type_payment=="cash"):
            return jsonify(id=st.id, type_payment=st.type_payment, amount=st.amount), 200
        return jsonify("The order has not been paid."), 404
    return jsonify("The order is not exist."), 404

if __name__ == "__main__":
   app.run()
