from launchpad_server import app

@app.route("/api/login", methods = ['POST', 'GET'])
def login():
    return "Hello from login route"

