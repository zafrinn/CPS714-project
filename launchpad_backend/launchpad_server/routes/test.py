from launchpad_server import app


@app.route("/test", methods=['GET'])
def test():
    return {
        "mssg": 'Connected to backend succesfully'
    }
