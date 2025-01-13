from uploader.app import app

if __name__ == "__main__":
    app.run()  # Optional for local testing

# WSGI callable exposed for the server
# application = app