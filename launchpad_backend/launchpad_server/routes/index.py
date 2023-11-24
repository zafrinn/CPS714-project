from launchpad_server import app
from flask import render_template, request, flash, redirect, url_for,jsonify, send_file
from .forms import SignupForm, LoginForm  
from flask_login import login_user
from flask_bcrypt import Bcrypt, check_password_hash
from flask_pymongo import PyMongo
from flask_cors import CORS
from flask_cors import CORS
from flask import session  
import pymongo
import sys
import re
import gridfs
sys.path.append('./launchpad_server/routes')
from startup_data import startup_data
app.config['MONGO_URI'] = 'mongodb://localhost:27017/database'
from datetime import datetime
from flask import request
from bson import ObjectId

# Initialize the PyMongo extension
mongo = PyMongo(app)
bcrypt = Bcrypt(app)


CORS(app, origins='*')


def setup_db():
    for data in startup_data:
        collection = mongo.db[data["tableName"]] # similar to table in relational db
        collection.drop()
        insertList = []

        for record in data["records"]: # similar to row in relational db
            insertList.append(record)

        collection.insert_many(insertList)
        collection.create_index([(data["index"], pymongo.ASCENDING)], unique=True) # Enforces primary key like restrcitions

setup_db() # Resets db to startup_data everytime backend is saved or ran


@app.route("/notifications/<int:user_id>")
def get_notifications(user_id):
    user_collection = mongo.db.user
    user_query = {"userId": user_id}
    user_result = user_collection.find_one(user_query)

    if not user_result:
        return jsonify({"data": []})  # Return an empty list if user not found

    notifications_ids = user_result.get("notifications", [])

    # Select notifications where notificationId is in notifications_ids
    notification_collection = mongo.db.notification
    notification_query = {"notificationId": {"$in": notifications_ids}}
    notification_result = list(notification_collection.find(notification_query))

    for doc in notification_result:
        doc.pop("_id")

    return jsonify({"data": notification_result})

@app.route("/notifications/<int:notification_id>/mark-as-read", methods=["PUT"])
def mark_notification_as_read(notification_id):
    # Connect to the notifications collection
    collection = mongo.db.notification

    # Find the notification by notificationId
    query = {"notificationId": notification_id}
    notification = collection.find_one(query)

    if notification:
        # Update the read status to True
        collection.update_one({"_id": notification["_id"]}, {"$set": {"read": True}})

        return jsonify({"message": f"Notification {notification_id} marked as read."}), 200
    else:
        return jsonify({"error": "Notification not found."}), 404
    
@app.route("/notifications/<int:notification_id>/toggle-saved", methods=["PUT"])
def toggle_notification_saved(notification_id):
    # Connect to the notifications collection
    collection = mongo.db.notification

    # Find the notification by notificationId
    query = {"notificationId": notification_id}
    notification = collection.find_one(query)

    if notification:
        # Toggle the saved status (change True to False, and vice versa)
        new_saved_status = not notification.get("saved", False)

        # Update the saved status
        collection.update_one({"_id": notification["_id"]}, {"$set": {"saved": new_saved_status}})

        return jsonify({"message": f"Notification {notification_id} saved status toggled."}), 200
    else:
        return jsonify({"error": "Notification not found."}), 404

@app.route("/jobs")
def get_jobs():
    # Select * from posting where postingTitle LIKE user_id

    # get all of the query strings
    type_filter = request.args.get('type')
    duration_filter = request.args.get('duration')
    location_filter = request.args.get('location')
    # transform everything to queryable strings
    everything_regex = re.compile(".*")
    type_regex = everything_regex if type_filter == "null" else type_filter 
    duration_regex = everything_regex if duration_filter == "null" else duration_filter 
    location_regex = everything_regex if location_filter == "null" else location_filter
    # access database
    collection = mongo.db.posting
    query = {"type": type_regex, "duration": duration_regex, "workModel": location_regex}
    result = list(collection.find(query))

    for doc in result:
        doc.pop("_id")
    return (jsonify({"data": result}))

@app.route("/recommended-jobs/<int:user_id>")
def get_recommended_jobs(user_id):
    # Query to get postingIds of jobs user has applied to
    application_collection = mongo.db.application
    application_query = {"userId": user_id}
    application_result = list(application_collection.find(application_query, {"postingId": 1}))

    # Compile postingIds into a list
    posting_ids = [app_record["postingId"] for app_record in application_result]

    # Query the posting collection for records where postingId is not in the list
    # This means user has not applied to them
    posting_collection = mongo.db.posting
    posting_query = {"postingId": {"$nin": posting_ids}}
    available_postings = list(posting_collection.find(posting_query))

    for posting in available_postings:
        posting.pop("_id")

    return jsonify({"data": available_postings})

@app.route("/companies")
def get_companies():
    # Select * from company

    # access database
    collection = mongo.db.company
    query = {}
    result = list(collection.find(query))

    for doc in result:
        doc.pop("_id")
    return (jsonify({"data": result}))   

@app.route("/users/<int:user_id>")
def get_users(user_id):
    # Select * from users where userId=user_id
    collection = mongo.db.user
    query = {"userId": user_id}
    result = list(collection.find(query))

    for doc in result:
        doc.pop("_id")
    return (jsonify({"data": result}))   

@app.route("/applications/<int:user_id>")
def get_applications(user_id):
    # Select * from application where userId=user_id
    collection = mongo.db.application
    query = {"userId": user_id}
    result = list(collection.find(query))

    for doc in result:
        doc.pop("_id")
    return (jsonify({"data": result}))   

# ACCOUNT SETTINGS INFORMATION ---------------------
@app.route('/acc-settings/<int:user_id>')
def get_user_info(user_id):
    collection = mongo.db.user
    query = {"userId": user_id}
    user_data = collection.find_one(query)

    # Extracting required information
    full_name = f"{user_data['firstName']} {user_data['lastName']}"
    email = user_data['email']
    password = user_data['password']
    program = user_data['program']
    address = user_data['address']
    phone_number = user_data['phoneNumber']
    two_factor = user_data['twoFactor']
    data_collection = user_data['dataCollection']

    # Creating the response JSON
    response_data = {
        "profile": {
            "full_name": full_name,
            "email": email,
            "password": password,
            "program": program,
            "address": address,
            "phone_number": phone_number
        },
        "security": {
            "two_factor":  two_factor,
            "data_collection": data_collection,
        }

    }

    return jsonify(response_data), 200

@app.route("/edit_profile/<int:user_id>", methods=["PUT"])
def edit_profile(user_id):
    # Connect to the user collection
    collection = mongo.db.user

    # Find the user by userId
    filter_query = {"userId": user_id}
    
    if request.method == 'PUT':
        # get form data
        formData = request.get_json()
        title = formData["title"]

        # update user info
        if(title=="Full Name"):
            first_name =  formData.get('first_name')
            last_name =formData.get('last_name')
            update_query = {
            '$set': {
                'firstName': first_name,
                'lastName': last_name,
                }
            }
            result = collection.update_one(filter_query, update_query)
        elif(title=="Email"):
            email =  formData.get('email')
            update_query = { '$set': {'email': email }}
            result = collection.update_one(filter_query, update_query)
        elif(title=="Password"):
            password =   bcrypt.generate_password_hash (formData.get('password')).decode('utf-8')
            update_query = { '$set': {'password': password }}
            result = collection.update_one(filter_query, update_query)
        elif(title=="Program"):
            program =  formData.get('program')
            update_query = { '$set': {'program': program }}
            result = collection.update_one(filter_query, update_query)
        elif(title=="Address"):
            street =  formData.get('street')
            postal_code =formData.get('postal_code')
            province_state =  formData.get('province_state')
            update_query = {
            '$set': {
                'address.streetAddress': street,
                'address.postalCode': postal_code,
                'address.province': province_state,
                }
            }
            result = collection.update_one(filter_query, update_query)
        elif(title=="Phone Number"):
            number =  formData.get('number')
            update_query = { '$set': {'phoneNumber': number }}
            result = collection.update_one(filter_query, update_query)

    # check it file was updated
    if result.modified_count > 0:
        print("Update user profile successful")
        return jsonify({"success": "Update user profile succesfully."}), 200
    else:
        print("Error update failed")
        return jsonify({"error": "Could not update user profile data."}), 400
    
@app.route("/edit_security/<int:user_id>", methods=["PUT"])
def edit_security(user_id):
    # Connect to the user collection
    collection = mongo.db.user

    # Find the user by userId
    filter_query = {"userId": user_id}
    
    if request.method == 'PUT':
        # get form data
        formData = request.get_json()
        security_type = formData["security_type"]

        # update security info
        if(security_type=="twoFactor"):
            twoFactor =  formData.get('twoFactor')
            update_query = { '$set': {'twoFactor': twoFactor }}
            result = collection.update_one(filter_query, update_query)
        elif(security_type=="dataCollection"):
            dataCollection =  formData.get('dataCollection')
            update_query = { '$set': {'dataCollection': dataCollection }}
            result = collection.update_one(filter_query, update_query)
    # check it file was updated
    if result.modified_count > 0:
        print("Update security info succesfully")
        return jsonify({"success": "Update security info succesfully."}), 200
    else:
        print("Error update security info failed")
        return jsonify({"error": "Could not update security data."}), 400

@app.route("/check_db")
def check_db():
    # Check if the connection is successful
    if mongo.cx:
        return "Connected to MongoDB successfully!" 
    

@app.route("/", methods = ['POST', 'GET'])
def index():
    return "Hello from Flask Backend"


@app.route("/home", methods = ['POST', 'GET'])
def landing(form):
        return render_template('landing.html',title='Landing Page',form=form)

@app.route("/signup", methods = ['POST', "GET"])
def register():
    response = "none"
    if request.method == 'POST':
        data = request.get_json()
        #print(data)
        fname =  data.get('fname')
        lname =data.get('lname')
        year = data.get('year')
        program = data.get('program')
        username = data.get('username')
        password = data.get('password')
        """
        print(
            "First Name: ", fname,
            "\nLast Name: ", lname,
            "\nYear: ", year,
            "\nProgram ", program,
            "\nusername: ", username,
            "\npasssword: ", password)

        """
        
        
        user_count = mongo.db.user.count_documents({}) # count user -> for user ID
        hashed_password = bcrypt.generate_password_hash (password).decode('utf-8') #encrypt Password

        data_to_insert = {
            "userId": user_count+1,
            "email": username, 
            "password": hashed_password, 
            "firstName": fname, 
            "lastName": lname, 
            "year": year, 
            "program": program,
            "address": {        # If address is not specified for a record, do not include this key-value pair in the dictionary
                "streetAddress": "",
                "postalCode": "",
                "province": ""
            },
            "phoneNumber": "",  # If number is not specified for a record, do not include this key-value pair in the dictionary
            "twoFactor": False,
            "dataCollection": True,
            "savedPostings": [{
                "dateTime": "", 
                "postingId": ""
            }],
            "notifications": []  # Ids of all their notifications
        }

        user_exists = mongo.db.get_collection("user").find_one({"email": username}) #check if user exists
       
        if user_exists:
            response = {'message': 'User already exists'}
        else:
            mongo.db.get_collection("user").insert_one(data_to_insert)
            response = {'message': 'User registered successfully'}
        return jsonify(response)
        
    return jsonify(response)
@app.route("/api/login", methods=['POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        print(data)
        username = data.get('username')
        password = data.get('password')
        print(
            "Username: ", username,
            "\nPassword: ", password)

        user_data = mongo.db.get_collection("user").find_one({"email": username})

        if user_data:
            stored_password_hashed = user_data.get("password")

            if stored_password_hashed and check_password_hash(stored_password_hashed, password):
                user_id = user_data.get("userId") 
                session['user_id'] = str(user_id)

                user_info = {
                    "userId": user_data.get("userId"),
                    "email": user_data.get("email"),
                    "firstName": user_data.get("firstName"),
                }

                response = {
                    "message": "User Logged In successfully",
                    "user_info": user_info  
                }
                return jsonify(response)

        response = {"message": "User does not exist or Incorrect Password"}
        return jsonify(response)

@app.route("/api/delete-account/<int:user_id>", methods=["DELETE"])
def delete_account(user_id):
    try:
        user_collection = mongo.db.user
        user_query = {"userId": user_id}
        user_result = user_collection.find_one(user_query)

        if user_result:
            user_collection.delete_one({"_id": user_result["_id"]})
            print(f"Account for user ID {user_id} deleted successfully.")

            return jsonify({"message": f"Account for user ID {user_id} deleted successfully."}), 200
        else:
            print(f"User not found for user ID: {user_id}")
            return jsonify({"error": "User not found."}), 404
    except Exception as e:
        print(f"Error deleting account: {str(e)}")
        return jsonify({"error": "Error deleting account. Please try again."}), 500


@app.route('/get-resume/<resume_id>')
def get_resume(resume_id):
    try:
        resume_id = ObjectId(resume_id)
        fs = gridfs.GridFS(mongo.db, collection='pdfs')
        resume_file = fs.get(resume_id)

        # Set the appropriate content type for PDF files
        response = send_file(resume_file, mimetype='application/pdf')

        # Optionally, you can specify a filename for the downloaded file
        response.headers['Content-Disposition'] = 'attachment; filename=resume.pdf'
        
        return response
    except Exception as e:
        return str(e), 404  # Or handle the error as needed

@app.route ("/upload-pdf", methods=["POST"])
def upload_pdf():
    if 'resume' in request.files and 'coverLetter' in request.files:
        user_id = session.get('user_id')
        if user_id:
            resume = request.files['resume']
            cover_letter = request.files['coverLetter']
            postingId = request.form['postingId']
            dt = datetime.now()
            # Save files to MongoDB using GridFS

            fs = gridfs.GridFS(mongo.db, collection='application')
            resume = fs.put(resume, filename=resume.filename, custom_metadata={"type": "resume"})
            cover_letter = fs.put(cover_letter, filename=cover_letter.filename, custom_metadata={"type": "cover_letter"}) 

            # get number of existing applications, add 1 to generate applicationID
            existing_applications = mongo.db.application.count_documents({})
            new_application_id = existing_applications + 1

            application_data = {
                "applicationId": new_application_id,  
                "resume": resume,
                "coverLetter": cover_letter,
                "Status": "Applied",
                "postingId": postingId,  
                "userId": user_id,
                "date": dt,
            }

            mongo.db.application.insert_one(application_data)
            return jsonify({"message": "PDF files uploaded successfully"}), 200
        
        else:
            return jsonify({"error": "User not authenticated"}), 401   
    else:
        return jsonify({"error": "Missing files"}), 400