from app import create_app

# Create the Flask app
app = create_app()

# Print which database URI the app is actually using
print("Using database:", app.config['SQLALCHEMY_DATABASE_URI'])

