from db_config import get_connection
from flask import Flask, render_template, request, redirect, session
import tensorflow as tf
from tensorflow.keras.preprocessing import image
import numpy as np
import os


from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image
)

from reportlab.lib.styles import getSampleStyleSheet

from reportlab.lib.pagesizes import letter

app = Flask(__name__)

app.secret_key = "ovarian_secret_key"

# Load trained model
model = tf.keras.models.load_model("ovarian_cyst_model.h5")

# Upload folder
UPLOAD_FOLDER = "static/uploads"

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Home Page
@app.route('/')
def home():

    if 'user_id' in session:
        return redirect('/dashboard')

    return render_template("index.html")



# Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        # conn = sqlite3.connect("database.db")

        # cursor = conn.cursor()
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        user = cursor.fetchone()

        conn.close()

        if user:

            stored_password = user[3]

            if check_password_hash(
                stored_password,
                password
            ):

                session['user_id'] = user[0]

                session['user_name'] = user[1]
                print("LOGIN SUCCESS")
                return redirect('/dashboard')

        return "Invalid Email or Password"

    return render_template("login.html")


# Signup Page
@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if request.method == 'POST':

        name = request.form['name']

        email = request.form['email']

        password = request.form['password']

        hashed_password = generate_password_hash(password)

        
        conn = get_connection()
        cursor = conn.cursor()

        try:

            cursor.execute("""
            INSERT INTO users(name, email, password)
            VALUES(%s,%s,%s)
            """, (
                name,
                email,
                hashed_password
            ))

            conn.commit()

            conn.close()

            return redirect('/login')

        except:

            conn.close()

            return "Email already exists!"

    return render_template("signup.html")


# Dashboard Page
@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:

        return redirect('/login')

    # conn = sqlite3.connect("database.db")

    # cursor = conn.cursor()
    conn = get_connection()
    cursor = conn.cursor()
    # Total scans
    cursor.execute("""
    SELECT COUNT(*) FROM predictions
    WHERE user_id=%s
    """, (
        session['user_id'],
    ))

    total_scans = cursor.fetchone()[0]

    # Healthy cases
    cursor.execute("""
    SELECT COUNT(*) FROM predictions
    WHERE user_id=%s AND result='Healthy Ovary'
    """, (
        session['user_id'],
    ))

    healthy_cases = cursor.fetchone()[0]

    # Cyst cases
    cursor.execute("""
    SELECT COUNT(*) FROM predictions
    WHERE user_id=%s AND result='Cyst Detected'
    """, (
        session['user_id'],
    ))

    cyst_cases = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        name=session['user_name'],
        total_scans=total_scans,
        healthy_cases=healthy_cases,
        cyst_cases=cyst_cases
    )
# Upload Page
@app.route('/upload')
def upload():

    if 'user_id' not in session:
        return redirect('/login')

    return render_template("index.html")

# Logout Page
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')


# History Page
@app.route('/history')
def history():

    if 'user_id' not in session:

        return redirect('/login')

    # conn = sqlite3.connect("database.db")

    # cursor = conn.cursor()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM predictions
    WHERE user_id=%s
    ORDER BY id DESC
    """, (
        session['user_id'],
    ))

    predictions = cursor.fetchall()

    conn.close()

    return render_template(
        "history.html",
        predictions=predictions
    )


# Prediction Route
@app.route('/predict', methods=['POST'])
def predict():

    if 'user_id' not in session:

        return redirect('/login')

    if 'file' not in request.files:

        return "No file uploaded"

    file = request.files['file']

    if file.filename == '':

        return "No selected file"

    filepath = os.path.join(
        app.config['UPLOAD_FOLDER'],
        file.filename
    )

    file.save(filepath)

    # Preprocess image
    img = image.load_img(
        filepath,
        target_size=(128, 128)
    )

    img_array = image.img_to_array(img)

    img_array = np.expand_dims(
        img_array,
        axis=0
    )

    img_array = img_array / 255.0

    # Predict
    prediction = model.predict(img_array)

    confidence = float(prediction[0][0])

    if confidence > 0.5:

        result = "Healthy Ovary"

        confidence_percentage = confidence * 100

    else:

        result = "Cyst Detected"

        confidence_percentage = (1 - confidence) * 100

    # Save prediction to database
    # conn = sqlite3.connect("database.db")
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO predictions(
        user_id,
        image_path,
        result,
        confidence
    )
    # VALUES(?,?,?,?)
    VALUES(%s,%s,%s,%s)
    """, (
        session['user_id'],
        filepath,
        result,
        confidence_percentage
    ))

    conn.commit()

    conn.close()

    return render_template(
        "result.html",
        prediction=result,
        confidence=round(
            confidence_percentage,
            2
        ),
        img_path=filepath
    )

@app.route('/generate_report')
def generate_report():

    if 'user_id' not in session:
        return redirect('/login')

    # conn = sqlite3.connect("database.db")

    # cursor = conn.cursor()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM predictions
    WHERE user_id=%s
    ORDER BY id DESC
    LIMIT 1
    """, (session['user_id'],))

    prediction = cursor.fetchone()

    conn.close()

    if not prediction:
        return "No prediction found!"

    report_path = "static/reports/medical_report.pdf"

    doc = SimpleDocTemplate(
        report_path,
        pagesize=letter
    )

    styles = getSampleStyleSheet()

    elements = []

    # Title
    title = Paragraph(
        "Ovarian Cyst Detection Medical Report",
        styles['Title']
    )

    elements.append(title)

    elements.append(Spacer(1,20))

    # Prediction Details
    result = Paragraph(
        f"<b>Prediction Result:</b> {prediction[3]}",
        styles['BodyText']
    )

    confidence = Paragraph(
        f"<b>Confidence:</b> {round(prediction[4],2)}%",
        styles['BodyText']
    )

    
    date = Paragraph(
    "<b>Date:</b> Generated Report",
    styles['BodyText']
    )

    elements.append(result)

    elements.append(Spacer(1,10))

    elements.append(confidence)

    elements.append(Spacer(1,10))

    elements.append(date)

    elements.append(Spacer(1,20))

    # Add Image
    img = Image(
        prediction[2],
        width=300,
        height=300
    )

    elements.append(img)

    elements.append(Spacer(1,20))

    # Footer Note
    note = Paragraph(
        "This AI-generated report is for educational purposes only.",
        styles['Italic']
    )

    elements.append(note)

    # Build PDF
    doc.build(elements)

    return redirect('/static/reports/medical_report.pdf')

# Admin Login
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():

    if request.method == 'POST':

        email = request.form['email']

        password = request.form['password']

        
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT * FROM admin
        WHERE email=%s
        """, (email,))

        admin = cursor.fetchone()

        conn.close()

        if admin:

            stored_password = admin[2]

            if check_password_hash(
                stored_password,
                password
            ):

                session['admin'] = True

                return redirect('/admin_dashboard')

        return "Invalid Admin Credentials"

    return render_template("admin_login.html")


# Admin Dashboard
@app.route('/admin_dashboard')
def admin_dashboard():

    if 'admin' not in session:

        return redirect('/admin_login')

    # conn = sqlite3.connect("database.db")

    # cursor = conn.cursor()
    conn = get_connection()
    cursor = conn.cursor()

    # Total users
    cursor.execute("SELECT COUNT(*) FROM users")

    total_users = cursor.fetchone()[0]

    # Total predictions
    cursor.execute("SELECT COUNT(*) FROM predictions")

    total_predictions = cursor.fetchone()[0]

    # Get all predictions
    cursor.execute("""
    SELECT * FROM predictions
    ORDER BY id DESC
    """)

    predictions = cursor.fetchall()

    conn.close()

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_predictions=total_predictions,
        predictions=predictions
    )


# Delete Prediction
@app.route('/delete_prediction/<int:id>')
def delete_prediction(id):

    if 'admin' not in session:

        return redirect('/admin_login')

    # conn = sqlite3.connect("database.db")
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    DELETE FROM predictions
    WHERE id=%s
    """, (id,))

    conn.commit()

    conn.close()

    return redirect('/admin_dashboard')


# Admin Logout
@app.route('/admin_logout')
def admin_logout():

    session.pop('admin', None)

    return redirect('/admin_login')

if __name__ == '__main__':

    app.run(debug=True)