from launchpad_server import app

@app.route("/", methods = ['POST', 'GET'])
def index():
    return "Hello from Flask Backend"


