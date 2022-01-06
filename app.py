from flask import Flask, redirect, url_for,render_template,request,session,flash
from flask.templating import render_template_string
import mysql.connector 
conn= mysql.connector.connect(host="localhost",user="root",password="",database="farmeasy")

mycursor=conn.cursor()
mycursor.execute("set global max_allowed_packet=67108864;")

app= Flask(__name__)
app.secret_key="Dhriti"

def date(x):
    new_date=x.split("/")
    new_date.reverse()
    new_date[1],new_date[2]= new_date[2],new_date[1]
    '-'.join(new_date)

def check():
    
    if session["fid"]== session["data"][0][0]:
        return True
    if session["cid"]==session["data"][0][0]:
        return True

    
@app.route("/",methods=["POST","GET"])
def login_page():
    if(request.method == "POST" and request.form["sub"]=="farmer"):
        username= request.form["f_user"]
        password=request.form["psw"]
        mycursor.execute("select * from farmer where user_id = '"+username+"' and password = '"+password+"';")
        data=mycursor.fetchall()
        
        if (len(data)>=1):
            session["fid"] = data[0][0] 
            session["data"]=data
            session["loggedin"] = True
            session["type"] = "farmer"
            return redirect(url_for("fmain"))
        else:
            return "Login failed , Click back to return to login page"
        
    elif(request.method == "POST" and request.form["sub"]=="customer"):
        username= request.form["c_user"]
        password=request.form["pws"]
        mycursor.execute("select * from customers where user_id = '"+username+"' and password = '"+password+"';")
        c_data=mycursor.fetchall()
        print(c_data)
        
        if (len(c_data)>=1):
            session["cid"] = c_data[0][0] 
            session["data"]=c_data
            session["loggedin"] = True
            session["type"] = "customer"
            return redirect(url_for("cmain"))
        else:
            return "login failed , Click back to return to login page"
        

    return render_template("login.html")
#Video:
@app.route('/quicktour',methods=["POST","GET"])
def video():
    return render_template("video.html")

#registration page
@app.route('/registration',methods=["POST","GET"])  
def signup():
    if (request.method=="POST"):
        role= request.form["role"]
        name=request.form["fn"]
        username=request.form["user"]
        password=request.form["pws"]
        print(role,name,username,password)
        address=request.form["add"]
        if role=="Farmer":
            mycursor.execute("select * from farmer")
            data=mycursor.fetchall()
            print(data)
            for val in data:
                if val[3]==username:
                    print("Username already exists")
                    break
                else:
                    sql="""insert into farmer(f_name,address,user_id,password)
                    Values(' """+name+"'"+','+"'"+address+"'"+','+"'"+username+"'"+','+"'"+password+"'"+')'
                    print(sql)
                    mycursor.execute(sql)
                    conn.commit()

                    return redirect(url_for("login_page"))
        else:
            mycursor.execute("select * from customers")
            data=mycursor.fetchall()
            print(data)
            for val in data:
                if val[3]==username:
                    print("Username already exists")
                    break
                else:
                    sql="""insert into customers(c_name,address,user_id,password)
                    Values(' """+name+"'"+','+"'"+address+"'"+','+"'"+username+"'"+','+"'"+password+"'"+')'
                    print(sql)
                    mycursor.execute(sql)
                    
                    conn.commit()
                    print("Successfully Registered")
                    return redirect(url_for("login_page"))
                    
    return render_template("registration.html")
      
#farmer home page-----x-------------x-------------
@app.route('/farmer',methods=["POST","GET"])
def fmain():
    #first check if the farmer is logged in using the session logged in variables
    #if not logged in or if the login is a customer instead redirect him to login page and display "farmer login required"
    if(session["loggedin"] != True or session["type"]!="farmer"):
        print("Farmer Login Required !!")
        return redirect(url_for("login_page"))

    #Viewing the previous Posts
    mycursor.execute("""select farmer.f_name,crop.name, h.quantity,h.price,h.posted_on,h.expiry,h.h_id
    from harvestpost h
    join farmer on farmer.f_id=h.f_id 
    join crop on crop.cr_id=h.cr_id  where h.expiry>=curdate() and h.f_id=""" +str(session["fid"]))
    data = mycursor.fetchall()
    print(data)
    return render_template("fmain.html",html_data = data,fdata=session["data"])

#customer home page-----x-------------x-------------
@app.route("/customer",methods = ["GET","POST"])
def cmain():
    if(session["loggedin"] != True or session["type"]!="customer"):
        return redirect(url_for("login_page"))

    if (request.method=="POST"):
        session['h_id']=request.form["h_id"]
        print(session['h_id'])
        return redirect(url_for("cpost"))
    #Viewing the Available Farmer Posts
    mycursor.execute("""Select crop.name, farmer.f_Name, h.price,h.quantity,h.expiry,h.h_id
    from harvestpost h
    join crop on crop.cr_id=h.cr_id
    join farmer  on farmer.f_id=h.f_id
    and h.expiry>= curdate()""")
    data = mycursor.fetchall()
    print(data)
    return render_template("cmain.html",html_data = data,cdata=session["data"])

#Farmer's New Crop-Post--------x------x--------x----------
@app.route('/posts',methods=["POST","GET"])
def fpost():
    if(request.method == "POST"):
        items= request.form["crops"]
        quant=request.form["quant"]
        price=request.form["price"]
        expiry=request.form["expiry"]
        sql="select cr_id from crop where name='" +str(items)+"';"
        mycursor.execute(sql)
        crop= mycursor.fetchall()
        crop=int(crop[0][0])

        sql="""INSERT Into harvestpost(f_id,cr_id, quantity, price, posted_on, expiry)
        Values("""+str(session["fid"])+","+str(crop)+","+str(quant)+","+str(price)+",CURDATE(),'"+str(expiry)+"');"""
        mycursor.execute(sql)
        conn.commit()
        
        return redirect(url_for("fmain"))
    return render_template("fpost.html")

#customer Posts--------x------x--------x----------x-------
@app.route('/cposts',methods=["POST","GET"])
def cpost():
    hid=session["h_id"]
    if request.method=="POST":
        quant=request.form["quantity"]
        print(quant)
        #getting the price per kg using sql query to calculate the total price
        h="""select h.price from harvestpost h where h.h_id="""+str(hid)
        mycursor.execute(h)
        hp=mycursor.fetchall()[0][0]
        
        #Placing the Order 
        sql="""insert into transaction(h_id,c_id,quantity,price,status)
        select """+str(hid)+','+str(session["cid"])+',' +str(quant)+',' +str(float(quant)*float(hp))+','+"'Order Placed'"+ """ 
        from harvestpost h where h.h_id= """+str(hid)+" and h.quantity >="+str(quant)
        print(sql)
        mycursor.execute(sql)
        conn.commit()

        #Once the customer orders the value is updated in the available quantity
        sql=""" Update harvestpost
        Set quantity= quantity - """+str(quant)+"""
        where h_id="""+str(hid)+" and quantity>="+str(quant)

        mycursor.execute(sql)
        conn.commit()
        return redirect(url_for("orders"))
        
    return render_template("cpost.html")


#Customer Orders--------x----------x------------x------------
@app.route('/orders',methods=["POST","GET"])
def orders():
    #Viewing the previous and new orders
    sql="""Select f.f_Name,cr.name, t.quantity, t.price,t.status,t.t_id
    from farmer f , crop cr, transaction t, harvestpost h
    where h.h_id= t.h_id and f.f_id=h.f_id and cr.cr_id=h.cr_id
    and c_id= """+str(session["cid"])
    #print(sql)
    mycursor.execute(sql)
    val=mycursor.fetchall()

    return render_template("order.html",html_data=val)


#Farmer views orders-----x-------------x------------x------x--------x----------
@app.route("/myorders",methods=["POST","GET"])
def forders():
    sql="""Select  c.c_name, c.address, cr.name, t.quantity , t.price, t.status,t.t_id,t.t_id
    from transaction t  , harvestpost h , crop cr, customers c
    where c.c_id=t.c_id  
    and  h.h_id=t.h_id   and cr.cr_id=h.cr_id and f_id=""" + str(session["fid"])

    mycursor.execute(sql)
    val=mycursor.fetchall()
    return render_template("forders.html",html_data=val)
# Farmer's Order Approval
@app.route("/approved",methods=["GET","POST"])
def Accept(): 
    if request.method=="POST":
        session["tid"]=request.form["accept"]
        sql="update transaction set status= 'Out For Delivery' where t_id= "+session["tid"]
        print(sql)
        mycursor.execute(sql)
        conn.commit()
    else:
        return "Error"
    return redirect(url_for("forders"))  
@app.route("/rejected",methods=["GET","POST"]) 
def Reject():
    if request.method=="POST":
        session["tid"]=request.form["reject"]
        sql="update transaction set status= 'REJECTED ' where t_id= "+session["tid"]
        mycursor.execute(sql)
        print(sql)
        conn.commit()
    else:
        return "Error"
    return redirect(url_for("forders"))  

#Cancelling the order by customer-----x-------------x---------
@app.route("/cancel", methods=["POST","GET"])
def cancel():
    session["tid"]= request.form['Cancel']
    if request.method=="POST":
        sql="update transaction set status= '"+str("Cancelled")+"' where t_id= "+session["tid"]
        mycursor.execute(sql)
        val="select t.quantity,t.h_id from transaction t where t.t_id= "+session["tid"]
        mycursor.execute(val)
        q=mycursor.fetchall()[0]
        quant=q[0]
        h_id=q[1]
        conn.commit()

        #When the customer cancels the order the quantity gets updated:
        
        sql=""" Update harvestpost
        Set quantity= quantity +"""+str(quant)+"""
        where h_id="""+str(h_id)
        print(sql)
        mycursor.execute(sql)
        conn.commit()
    return redirect(url_for("orders"))
#If order is out for delivery:
@app.route("/delivered", methods=["POST","GET"])
def ofd():
    session["tid"]=request.form["OFD"]
    if request.method=="POST":
        sql= "Update transaction set status= 'DELIVERED' where t_id= "+session["tid"]
        mycursor.execute(sql)
        conn.commit()
    return redirect(url_for("orders"))

#Deleting the farmer post-----x-------------x------------x---------x-----
@app.route("/delete",methods=["POST","GET"])
def fdel():
    fid=session["fid"]
    session['h_id']=request.form["del"]
    

    if request.method=="POST":
        sql="delete from harvestpost where h_id="+session['h_id']+" and f_id= "+str(fid)
        print(sql)
        mycursor.execute(sql)
        conn.commit()
        
        return redirect(url_for("fmain"))
#logout-----x-------------x-------------x------------
@app.route("/logout")
def logout():
    
    session.pop("username",None)
    session["loggedin"] = False
    session["type"] = None
    
    flash("You have successfully logged out of your account!!")
    return redirect(url_for("login_page"))


if __name__=="__main__":
    app.run(debug=True)