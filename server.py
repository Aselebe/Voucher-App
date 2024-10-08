    
from __init__ import app  # Ensure this imports your app correctly
from models import create_tables

if __name__ == '__main__':
    create_tables()  # Ensure tables are created if they don't exist
    #app.run(debug=True)
    app.run(host='0.0.0.0', port=9000, debug=True)  # Set debug=True for development