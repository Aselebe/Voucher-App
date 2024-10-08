from flask import render_template, request, redirect, url_for, flash, session
from models import get_db_connection
import uuid
from flask_mail import Message
from flask_bcrypt import Bcrypt
from datetime import datetime
from email.mime.multipart import MIMEMultipart
import smtplib  # For sending emails
import qrcode  # For generating QR codes
from flask import Flask, render_template, request, redirect, url_for, flash, session
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from io import BytesIO
#from routes import create_routes


bcrypt = Bcrypt()

def create_routes(app):

    def send_voucher_email(subject, body, recipient, voucher_id):
        sender_email = 'sales@aurorainfinity.co.uk'
        email_password = 'Sales_Aurora_00'
        smtp_server = 'aurorainfinity.co.uk'
        smtp_port = 465

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient
        msg['Subject'] = subject

        # Attach email body
        msg.attach(MIMEText(body, 'plain'))

        # Attach QR code
        qr_code_img = generate_qr_code(voucher_id)
        qr_code_attachment = MIMEImage(qr_code_img.read(), name=f"{voucher_id}.png")
        qr_code_attachment.add_header('Content-Disposition', 'attachment', filename=f"{voucher_id}.png")
        msg.attach(qr_code_attachment)

        # Send email
        try:
            with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                server.login(sender_email, email_password)
                server.send_message(msg)
            print(f"Email sent to {recipient}")
        except Exception as e:
            print(f"Failed to send email: {e}")
    
    @app.route('/create_voucher', methods=['GET', 'POST'])
    def create_voucher():
        if request.method == 'POST':
            # Retrieve form data
            new_voucher_name = request.form['new_voucher_name']
            new_voucher_email = request.form['new_voucher_email']
            new_voucher_amount = float(request.form['new_voucher_amount'])

            # Generate a unique voucher ID
            new_voucher_id = str(uuid.uuid4())

            # Store the voucher in the database
            conn = get_db_connection()
            conn.execute('INSERT INTO vouchers (voucher_id, voucher_name, email, balance) VALUES (?, ?, ?, ?)',
                        (new_voucher_id, new_voucher_name, new_voucher_email, new_voucher_amount))
            conn.commit()
            conn.close()

            # Generate the QR code
            qr_code_img = generate_qr_code(new_voucher_id)

            # Prepare the email content
            subject = f"Voucher Created: {new_voucher_name}"
            body = f"Thank you for purchasing {new_voucher_name} with an initial balance of £{new_voucher_amount}. Please find your voucher QR code attached."

            # Send the voucher details via email
            send_voucher_email(subject, body, new_voucher_email, new_voucher_id)

            flash(f'Voucher {new_voucher_name} created successfully and an email sent to {new_voucher_email}.', 'success')
            return redirect(url_for('admin_dash'))

        return render_template('create_voucher.html')
            
    @app.route('/redeem/<voucher_id>', methods=['GET', 'POST'])
    def redeem_voucher(voucher_id):
        vendor_id = session.get('vendor_id')  # Ensure vendor is logged in

        if not vendor_id:
            flash('You must be logged in to redeem vouchers.', 'error')
            return redirect(url_for('vendor_login'))

        conn = get_db_connection()
        voucher = conn.execute('SELECT * FROM vouchers WHERE voucher_id = ?', (voucher_id,)).fetchone()

        if request.method == 'POST':
            deduction_amount = float(request.form.get('deduction_amount'))

            # Debugging print statements
            print(f"Processing redemption for Voucher ID: {voucher_id}")
            print(f"Vendor ID: {vendor_id}")
            print(f"Deduction Amount: {deduction_amount}")

            # Check if the voucher has sufficient balance
            if voucher and voucher['balance'] >= deduction_amount:
                new_balance = voucher['balance'] - deduction_amount
                conn.execute('UPDATE vouchers SET balance = ? WHERE voucher_id = ?', (new_balance, voucher_id))

                # Insert the sale into the sales table
                conn.execute('INSERT INTO sales (voucher_id, booth_id, sale_amount) VALUES (?, ?, ?)',
                            (voucher_id, vendor_id, deduction_amount))
                
                conn.commit()  # Commit the transaction

                # Debugging print to confirm sale insertion
                print(f"Sale inserted for Voucher ID: {voucher_id}, Vendor ID: {vendor_id}, Amount: {deduction_amount}")

                # Send email to the buyer
                subject = f'Purchase Notification for Voucher {voucher["voucher_name"]}'
                body = (f'Dear {voucher["voucher_name"]},\n\n'
                        f'You made a purchase of £{deduction_amount:.2f}.\n'
                        f'Your remaining balance is now £{new_balance:.2f}.\n\n'
                        'Thank you for your purchase!')
                
                # Assuming `send_voucher_email` sends emails
                send_voucher_email(subject, body, voucher['email'], voucher_id)

                flash(f'Deduction of £{deduction_amount} successful! New balance: £{new_balance}. Notification email sent to buyer.', 'success')
                return redirect(url_for('vendor_dashboard'))

            else:
                flash('Insufficient balance or voucher not found.', 'error')

        conn.close()
        return render_template('redeem_voucher.html', voucher_balance=voucher['balance'], voucher_id=voucher_id)

    
    @app.route('/manage_vouchers', methods=['GET', 'POST'])
    def manage_vouchers():
        conn = get_db_connection()
        vouchers = conn.execute('SELECT * FROM vouchers').fetchall()  # Fetch all vouchers for dropdown
        conn.close()

        if request.method == 'POST':
            action = request.form['action']
            voucher_id = request.form['voucher_id']

            # Handle voucher top-up
            if action == 'top_up':
                top_up_amount = float(request.form['top_up_amount'])
                conn = get_db_connection()
                voucher = conn.execute('SELECT * FROM vouchers WHERE voucher_id = ?', (voucher_id,)).fetchone()

                if voucher:
                    new_balance = voucher['balance'] + top_up_amount
                    conn.execute('UPDATE vouchers SET balance = ? WHERE voucher_id = ?', (new_balance, voucher_id))
                    conn.commit()

                    # Prepare the email content
                    subject = f'Voucher {voucher["voucher_name"]} Top-Up Confirmation'
                    body = f'Your voucher "{voucher["voucher_name"]}" has been topped up by £{top_up_amount}. Your new balance is £{new_balance}.'

                    # Send email to the buyer with updated balance and QR code
                    send_voucher_email(subject, body, voucher['email'], voucher_id)

                    flash(f'Voucher {voucher["voucher_name"]} topped up successfully. Email sent to buyer.', 'success')

                conn.close()
                return redirect(url_for('manage_vouchers'))

            # Handle voucher removal
            elif action == 'remove':
                conn = get_db_connection()
                voucher = conn.execute('SELECT * FROM vouchers WHERE voucher_id = ?', (voucher_id,)).fetchone()

                if voucher:
                    conn.execute('DELETE FROM vouchers WHERE voucher_id = ?', (voucher_id,))
                    conn.commit()

                    # Prepare the email content
                    subject = f'Voucher {voucher["voucher_name"]} Cancellation'
                    body = f'Your voucher "{voucher["voucher_name"]}" has been cancelled.'

                    # Send email to the buyer with cancellation notice
                    send_voucher_email(subject, body, voucher['email'], voucher_id)

                    flash(f'Voucher {voucher["voucher_name"]} removed. Email sent to buyer.', 'success')

                conn.close()
                return redirect(url_for('manage_vouchers'))

        # Render the voucher management page with the available vouchers
        return render_template('manage_vouchers.html', vouchers=vouchers)

        
    
    
    @app.route('/cancel_voucher/<voucher_id>', methods=['POST'])
    def cancel_voucher(voucher_id):
        conn = get_db_connection()
        voucher = conn.execute('SELECT * FROM vouchers WHERE voucher_id = ?', (voucher_id,)).fetchone()

        if voucher:
            conn.execute('UPDATE vouchers SET canceled = 1 WHERE voucher_id = ?', (voucher_id,))
            conn.commit()

            # Prepare the email content
            subject = f'Voucher {voucher["voucher_name"]} Cancellation Notice'
            body = f'Your voucher "{voucher["voucher_name"]}" has been canceled.'

            # Send email to the buyer
            send_voucher_email(subject, body, voucher['email'], voucher_id)

            flash('Voucher canceled and email sent to buyer.', 'success')
        else:
            flash('Voucher not found.', 'error')

        conn.close()
        return redirect(url_for('admin_dash'))    
    
    def generate_qr_code(voucher_id):
        redemption_url = f"http://127.0.0.1:9000/redeem/{voucher_id}"
    
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(redemption_url)
        qr.make(fit=True)

        img = qr.make_image(fill='black', back_color='white')

        img_io = BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)  # Move the cursor back to the start of the stream

        return img_io

        
    @app.route('/admin_login', methods=['GET', 'POST'])
    def admin_login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            if username == 'admin' and password == 'adminpassword':
                session['admin_logged_in'] = True
                flash('Login successful!', 'success')
                return redirect(url_for('admin_dash'))
            else:
                flash('Invalid username or password.', 'error')

        return render_template('admin_login.html')
    
    @app.route('/deduct_voucher', methods=['POST'])
    def deduct_voucher():
        voucher_id = request.form['voucher_id']
        deduction_amount = float(request.form['deduction_amount'])

        conn = get_db_connection()
        voucher = conn.execute('SELECT * FROM vouchers WHERE voucher_id = ?', (voucher_id,)).fetchone()

        if voucher:
            current_balance = voucher['balance']

            if current_balance >= deduction_amount:
                new_balance = current_balance - deduction_amount
                conn.execute('UPDATE vouchers SET balance = ? WHERE voucher_id = ?', (new_balance, voucher_id))
                conn.commit()

                # Prepare the email content
                subject = f'Voucher {voucher["voucher_name"]} Deduction Notice'
                body = f'A deduction of £{deduction_amount} has been made on your voucher "{voucher["voucher_name"]}". Your new balance is £{new_balance}.'

                # Send email to the buyer with updated balance and QR code
                send_voucher_email(subject, body, voucher['email'], voucher_id)  # Make sure to pass voucher['email'] as the recipient

                flash('Deduction successful and email sent to buyer.', 'success')
            else:
                flash('Insufficient balance on the voucher.', 'error')
        else:
            flash('Voucher not found.', 'error')

        conn.close()
        return redirect(url_for('admin_dash'))
            
    @app.route('/admin_logout')
    def admin_logout():
        session.pop('admin_logged_in', None)  # Remove the session to log out the admin
        flash('You have been logged out successfully.')
        return redirect(url_for('admin_login'))



    @app.route('/admin_dash')
    def admin_dash():
        conn = get_db_connection()
        events = conn.execute('SELECT * FROM events').fetchall()

        # Format the event date for each event
        formatted_events = []
        for event in events:
            event_date = datetime.strptime(event['event_date'], '%Y-%m-%d')
            formatted_date = event_date.strftime('%d %b %Y')  # Format as 01 Jan 2020
            event_with_formatted_date = {
                'event_id': event['event_id'],
                'event_name': event['event_name'],
                'event_date': formatted_date  # Use the formatted date
            }
            formatted_events.append(event_with_formatted_date)

        event_vendors = {}
        for event in formatted_events:
            vendors = conn.execute('SELECT * FROM vendors WHERE event_id = ?', (event['event_id'],)).fetchall()
            event_vendors[event['event_id']] = vendors

        conn.close()

        return render_template('admin_dashboard.html', events=formatted_events, event_vendors=event_vendors)

    @app.route('/create_event', methods=['GET', 'POST'])
    def create_event():
        if request.method == 'POST':
            event_name = request.form.get('event_name')
            event_date = request.form.get('event_date')

            if event_name and event_date:
                conn = get_db_connection()
                event_id = str(uuid.uuid4())
                conn.execute('INSERT INTO events (event_id, event_name, event_date) VALUES (?, ?, ?)',
                             (event_id, event_name, event_date))
                conn.commit()
                conn.close()
                flash('Event Created Successfully', 'success')
                return redirect(url_for('admin_dash'))
            else:
                flash('Please provide all required fields', 'error')

        return render_template('event_creation.html')

    @app.route('/remove_event/<event_id>', methods=['POST'])
    def remove_event(event_id):
        conn = get_db_connection()
        conn.execute('DELETE FROM events WHERE event_id = ?', (event_id,))
        conn.commit()
        conn.close()
        flash('Event removed successfully.', 'success')
        return redirect(url_for('admin_dash'))

    @app.route('/add_vendor/<event_id>', methods=['GET', 'POST'])
    def add_vendor(event_id):
        if request.method == 'POST':
            vendor_name = request.form['vendor_name']
            vendor_email = request.form['vendor_email']
            vendor_phone = request.form['vendor_phone']
            vendor_id = str(uuid.uuid4())

            try:
                conn = get_db_connection()
                conn.execute('INSERT INTO vendors (vendor_id, vendor_name, email, phone, event_id) VALUES (?, ?, ?, ?, ?)',
                             (vendor_id, vendor_name, vendor_email, vendor_phone, event_id))
                conn.commit()
                conn.close()

                flash('Vendor added successfully!', 'success')
            except Exception as e:
                flash('Error adding vendor. Please try again.', 'error')

            return redirect(url_for('admin_dash'))

        return render_template('add_vendor.html', event_id=event_id)
    
    @app.route('/remove_vendor/<vendor_id>', methods=['POST'])
    def remove_vendor(vendor_id):
        conn = get_db_connection()
        conn.execute('DELETE FROM vendors WHERE vendor_id = ?', (vendor_id,))
        conn.commit()
        conn.close()
        flash('Vendor removed successfully.', 'success')
        return redirect(url_for('admin_dash'))

    @app.route('/register', methods=['GET', 'POST'])
    def register_vendor():
        if request.method == 'POST':
            email = request.form['email'].strip().lower()
            password = request.form['password']
            confirm_password = request.form['confirm_password']

            # Check if passwords match
            if password != confirm_password:
                flash('Passwords do not match.', 'error')
                return redirect(url_for('register_vendor'))

            # Hash the password using bcrypt
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

            conn = get_db_connection()

            # Check if the vendor exists and has not yet registered
            vendor = conn.execute('SELECT * FROM vendors WHERE LOWER(email) = ?', (email,)).fetchone()

            if vendor:
                if vendor['password'] is None:  # Vendor is allowed to register
                    conn.execute('UPDATE vendors SET password = ? WHERE email = ?', (hashed_password, email))
                    conn.commit()
                    flash('Vendor registered successfully!', 'success')
                    return redirect(url_for('vendor_login'))
                else:
                    flash('This email has already been registered.', 'error')
            else:
                flash('You are not authorized to register.', 'error')
            
            conn.close()

        return render_template('register_vendor.html')

    @app.route('/vendor_login', methods=['GET', 'POST'])
    def vendor_login():
        if request.method == 'POST':
            email = request.form['vendor_email'].strip().lower()
            password = request.form['vendor_password']

            conn = get_db_connection()
            vendor = conn.execute('SELECT * FROM vendors WHERE LOWER(email) = ?', (email,)).fetchone()
            conn.close()

            print("Vendor query result:", vendor)  # Check if vendor is fetched
            
            if vendor is None:
                flash('No vendor found with that email.', 'error')
                return render_template('vendor_login.html')

            if bcrypt.check_password_hash(vendor['password'], password):
                # Use 'vendor_id' instead of 'id'
                session['vendor_id'] = vendor['vendor_id']
                print("Login successful, redirecting to dashboard.")  # Debug message
                return redirect(url_for('vendor_dashboard'))
            else:
                flash('Invalid email or password.', 'error')

        return render_template('vendor_login.html')

    @app.route('/vendor_logout')
    def vendor_logout():
        session.pop('vendor_logged_in', None)  # Remove the session to log out 
        flash('You have been logged out successfully.')
        return redirect(url_for('_login'))
    
    @app.route('/vendor_dashboard')
    def vendor_dashboard():
        if 'vendor_id' not in session:
            flash('You must log in first.', 'error')
            return redirect(url_for('vendor_login'))

        vendor_id = session['vendor_id']

        # Fetch vendor details
        conn = get_db_connection()
        vendor = conn.execute('SELECT * FROM vendors WHERE vendor_id = ?', (vendor_id,)).fetchone()
        
        # Fetch sales data for the vendor
        sales = conn.execute('SELECT * FROM sales WHERE booth_id = ?', (vendor_id,)).fetchall()
        conn.close()

        # Calculate total sales and total sales amount
        total_sales = len(sales)
        total_sales_amount = sum(sale['sale_amount'] for sale in sales)

        return render_template('vendor_dashboard.html', vendor=vendor, sales=sales, total_sales=total_sales, total_sales_amount=total_sales_amount)
    
    @app.route('/view_sales/<vendor_id>')
    def view_sales(vendor_id):
        # Ensure admin is logged in (adjust based on your session logic)
        if 'admin_logged_in' not in session:
            flash('You must log in as an admin to view vendor sales.', 'error')
            return redirect(url_for('admin_login'))

        # Fetch vendor details using the passed vendor_id
        conn = get_db_connection()
        vendor = conn.execute('SELECT * FROM vendors WHERE vendor_id = ?', (vendor_id,)).fetchone()

        # Fetch sales data for the vendor
        sales = conn.execute('SELECT * FROM sales WHERE booth_id = ?', (vendor_id,)).fetchall()
        conn.close()

        if not vendor:
            flash('Vendor not found.', 'error')
            return redirect(url_for('admin_dash'))

        # Calculate total sales and total sales amount
        total_sales = len(sales)
        total_sales_amount = sum(sale['sale_amount'] for sale in sales)

        return render_template('view_sales.html', vendor=vendor, sales=sales, total_sales=total_sales, total_sales_amount=total_sales_amount)

    
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/forgot_password', methods=['GET', 'POST'])
    def forgot_password():
        if request.method == 'POST':
            email = request.form['email']
            flash('If this email is registered, a password reset link will be sent.', 'info')
            return redirect(url_for('vendor_login'))

        return render_template('forgot_password.html')