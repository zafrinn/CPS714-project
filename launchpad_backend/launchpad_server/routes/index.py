from launchpad_server import app
from flask import render_template, request, flash, redirect, url_for,jsonify, send_file, Response
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
from flask_mail import Mail
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from flask import request
import os
from bson import ObjectId


# Initialize the PyMongo extension
mongo = PyMongo(app)
bcrypt = Bcrypt(app)


CORS(app, origins='*')

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'organizationlaunchpad@gmail.com'
app.config['MAIL_PASSWORD'] = 'zeid hsnp odqv jsol'
app.config['MAIL_DEFAULT_SENDER'] = 'organizationlaunchpad@gmail.com'
app.config['SECRET_KEY'] = '37e0f3d0ced66904aa5b89a39bb94649ec5ae68d06419f7ccadd7a3c5eebc93a'

mail = Mail(app)




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

    # Sort the result by 'dateTime' in descending order (-1 for descending)
    notification_result = list(notification_collection.find(notification_query).sort('dateTime', -1))

    for doc in notification_result:
        doc.pop("_id")

    return jsonify({"data": notification_result})


@app.route("/notifications/<int:user_id>/<subject>/<body>/<int:application_id>/add-notification", methods=["POST"])
def add_notifications(user_id, subject, body, application_id):

    # Raise an error if any of the parameters are missing
    if not all([user_id, subject, body, application_id]):
        return jsonify({"error": "Missing parameters for notification"}), 404

    # Create a new notificationId by find the highest existing notificationId and adding 1
    max_notification = mongo.db.notification.find_one(sort=[("notificationId", -1)])
    notification_id = (max_notification['notificationId'] + 1) if max_notification else 1 # If no notifications exist, set new notificationID to 1
    
    # Add the notifications to the user's notifications list
    result_user = mongo.db.user.update_one(
        {"userId": user_id},
        {"$addToSet": {"notifications": notification_id}}
    )

    # Replace quadruple spaces with line breaks in the body
    body = body.replace('<br>', '\n')

    # Create a notification object
    notification = {
        "notificationId": notification_id,
        "subject": subject,
        "body": body,
        "dateTime": datetime.utcnow(),
        "read": False,
        "saved": False,
        "applicationId": application_id
    }

    # Insert the notification object into the database
    result_notification = mongo.db.notification.insert_one(notification)

    # Log a success/error message if the notification was/wasn't inserted respectively
    if result_user.modified_count > 0 and result_notification.inserted_id: # Inserted ID is only generated if insertion was successful 
        return jsonify({"message": f"Notification {notification_id} added successfully"}), 200
    else:
        return jsonify({"error": f"Failed to add notification {notification_id}"}), 404


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

@app.route("/jobs/<int:user_id>/<int:posting_id>/toggle-saved", methods=["PUT"])
def toggle_posting_saved(user_id, posting_id):

    # Check if the user with userId = user_id has a saved posting with postingId = posting_id
    posting_exists = mongo.db.user.find_one(
        {"userId": user_id, "savedPostings.postingId": posting_id},
        {"_id": 0, "savedPostings.$": 1}
    )
    
    # If the user does not have the posting saved
    if not posting_exists:

        # Get current datetime and format it into ISO 8601
        date_time = datetime.utcnow()

        # Add the posting to savedPostings
        result = mongo.db.user.update_one(
            {"userId": user_id},
            {"$addToSet": {"savedPostings": {"dateTime": date_time, "postingId": posting_id}}}
        )

        # Log a success/error message if the posting was/wasn't saved respectively
        if result.modified_count > 0:
            return jsonify({"message": "Posting saved successfully!"}), 200
        else:
            return jsonify({"message": "Posting save failed :("}), 404

    # If the user has the posting saved
    else: 

        # Remove the posting from savedPostings
        result = mongo.db.user.update_one(
            {"userId": user_id},
            {"$pull": {"savedPostings": {"postingId": posting_id}}}
        )

        # Log a success/error message if the posting was/wasn't unsaved respectively
        if result.modified_count > 0:
            return jsonify({"message": "Posting unsaved successfully!"}), 200
        else:
            return jsonify({"message": "Posting unsave failed :("}), 404
          
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
    print("hello")
    print(user_id)
    query = {"userId": user_id}
    projection = {"_id": 1, "Status": 1, "postingId": 1, "userId": 1, "date": 1, "applicationId":1}
    applications = list(collection.find(query,  projection))

    # Remove the "_id" field from each document in the result
    for app in applications:
        app.pop("_id")

        # Additional query to retrieve information from anotherTable
        posting_id = app["postingId"]
        postings = mongo.db.posting
        other_table_query = {"postingId": posting_id}
        
        
        additional_info = postings.find_one(other_table_query, {"postingTitle": 1, "location": 1, "duration": 1, "type":1, "postingDescription":1, "workModel":1, "workterm":1,"deadline":1, "logo":1, "companyId":1 })
        additional_info.pop("_id")

        company_id = additional_info["companyId"]
        company = mongo.db.company
        company_query = {"companyId": company_id}
        company_info = company.find_one(company_query, {"companyName": 1})
        company_name = company_info['companyName']


        app["additionalInfo"] = {
            **additional_info,
            "companyName": company_name
        }
    
    return jsonify({"data": applications}), 200

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
            "userConfirmed": False,
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
            return jsonify({'message': 'User already exists'})
        
        mongo.db.get_collection("user").insert_one(data_to_insert)
        confirmation_token = generate_confirmation_token(username)
        send_confirmation_email(username, confirmation_token)

        return jsonify({'message': 'User registered successfully'})
    
    return jsonify({'message': 'Invalid request method'})

def send_confirmation_email(username, user_token):
    confirmation_link = f'http://localhost:3000/confirm_email?token={user_token}'
    subject = 'Account Confirmation'
    body = f'Click the following link to confirm your account: {confirmation_link}'
    msg = Message(subject, recipients=[username], body=body)
    mail.send(msg)

@app.route('/confirm_email', methods=['GET', 'POST'])
def confirm_email():
    data = request.get_json()
    token = data.get('token')

    if not token:
        return jsonify({"status": "error", "message": "Token not provided."})

    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='email-confirm', max_age=3600)  # Token expiration in seconds
        user_collection = mongo.db.get_collection("user")

        # Update the user status in the database
        filter_query = {"email": email}
        update_query = {"$set": {"userConfirmed": True}}
        user_collection.update_one(filter_query, update_query)

        # Redirect the user to the main application page or return a JSON response indicating success
        return jsonify({"status": "success", "message": "Email confirmed successfully!"})
    except Exception as e:
        # Return a JSON response indicating failure
        return jsonify({"status": "error", "message": "Invalid or expired token. Please try again."})

def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-confirm')

@app.route('/api/login', methods=['POST'])
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


@app.route('/display-resume/<applicationId>')
def get_resume(applicationId):
    try:
        print(f"Attempting to retrieve application with ID: {applicationId}")
        application = mongo.db.application.find_one({'applicationId': int(applicationId.strip())})
        print(f"Query result: {application}")
        if application:
            print(f"Application found for ID: {applicationId}")

            resume_id = application.get('resume')
            fs = gridfs.GridFS(mongo.db, collection='application')

            resume_file = fs.get(ObjectId(resume_id))
            file_content = resume_file.read()
            return Response(file_content, mimetype='application/pdf')
        return "Application not found", 404
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return str(e), 500  

@ app.route('/display-cover-letter/<applicationId>')
def get_cover_letter(applicationId):
    try:
        print(f"Attempting to retrieve application with ID: {applicationId}")
        application = mongo.db.application.find_one({'applicationId': int(applicationId.strip())})
        print(f"Query result: {application}")

        if application:
            print(f"Application found for ID: {applicationId}")
            cover_letter_id = application.get('coverLetter')
            fs = gridfs.GridFS(mongo.db, collection='application')
            cover_letter_file = fs.get(ObjectId(cover_letter_id))
            file_content = cover_letter_file.read()
            return Response(file_content, mimetype='application/pdf')

        return "Application not found", 404
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return str(e), 500  

@app.route ("/upload-pdf", methods=["POST"])
def upload_pdf():
    if 'resume' in request.files and 'coverLetter' in request.files:
        user_id = int(session.get('user_id'))
        if user_id:
            resume = request.files['resume']
            cover_letter = request.files['coverLetter']
            postingId = int(request.form['postingId'])
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
            response_data = {
                "message": "PDF files uploaded successfully",
                "applicationId": str(new_application_id)
            }

            return jsonify(response_data), 200
        
        else:
            return jsonify({"error": "User not authenticated"}), 401   
    else:
        return jsonify({"error": "Missing files"}), 400