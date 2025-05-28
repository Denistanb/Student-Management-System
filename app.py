from flask import Flask, render_template, request, redirect, jsonify
import sqlite3
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('college.db')
    cursor = conn.cursor()

    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            semester INTEGER NOT NULL,
            credits INTEGER NOT NULL,
            dob DATE NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            enrollment_year INTEGER NOT NULL,
            course_name TEXT NOT NULL
        )
    ''')

    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS courses (
            course_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name TEXT NOT NULL,
            department TEXT NOT NULL,
            semester INTEGER NOT NULL
        )
    ''')

    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            course_id INTEGER NOT NULL,
            date DATE NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(student_id),
            FOREIGN KEY (course_id) REFERENCES courses(course_id)
        )
    ''')

    # New table to associate students with courses
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS student_courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            course_id INTEGER NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(student_id),
            FOREIGN KEY (course_id) REFERENCES courses(course_id)
        )
    ''')

    conn.commit()
    conn.close()



@app.route('/')
def index():
    return render_template('index.html')

def generate_student_id(name, department, enrollment_year):
    if name and department and enrollment_year:
        # Simple logic to generate student ID
        year_suffix = str(enrollment_year)[-2:]  # Last two digits of the year
        department_code = department[:2].upper()  # First two letters of the department

        # Connect to the database to find existing students
        conn = sqlite3.connect('college.db')
        cursor = conn.cursor()

        # Fetch existing students in the same department, ordered by name
        cursor.execute('SELECT student_id, name FROM students WHERE department = ? ORDER BY name ASC', (department,))
        existing_students = cursor.fetchall()

        # Prepare to determine the next unique number
        existing_ids = [student[0] for student in existing_students]
        existing_names = [student[1] for student in existing_students]

        # Determine the unique number based on the position of the new name
        # Insert the new name into the list and sort it
        all_names = existing_names + [name]
        all_names_sorted = sorted(all_names)

        # Find the position of the new name
        position = all_names_sorted.index(name)

        # Calculate the unique number: 1-based index
        unique_number = position + 1  # Increment the position by 1 to start from 1

        # Create the new student ID
        student_id = f"{year_suffix}{department_code}{unique_number:03d}"

        conn.close()
        return student_id

    return ''

@app.route('/generate_student_id', methods=['GET'])
def generate_student_id_route():
    name = request.args.get('name')
    department = request.args.get('department')
    enrollment_year = request.args.get('enrollment_year')

    student_id = generate_student_id(name, department, enrollment_year)
    return jsonify({'student_id': student_id})


@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        name = request.form['name']
        department = request.form['department']
        semester = request.form['semester']
        credits = request.form['credits']
        dob = request.form['dob']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        enrollment_year = request.form['enrollment_year']
        course_name = request.form['course_name']
        student_id = request.form['student_id']

        # Connect to database and insert the student record
        conn = sqlite3.connect('college.db')
        cursor = conn.cursor()
        cursor.execute(''' 
            INSERT INTO students (student_id, name, department, semester, credits, dob, email, phone, address, enrollment_year, course_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (student_id, name, department, semester, credits, dob, email, phone, address, enrollment_year, course_name))
        conn.commit()
        conn.close()
        return redirect('/view_students')

    return render_template('add_student.html')


@app.route('/view_students', methods=['GET', 'POST'])
def view_students():
    conn = sqlite3.connect('college.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        search_query = request.form.get('search_query')
        cursor.execute('SELECT * FROM students WHERE student_id LIKE ? OR name LIKE ?', ('%' + search_query + '%', '%' + search_query + '%'))
    else:
        cursor.execute('SELECT * FROM students')

    students = cursor.fetchall()
    conn.close()
    return render_template('view_students.html', students=students)

@app.route('/update_student', methods=['GET', 'POST'])
def update_student():
    if request.method == 'POST':
        student_id = request.form['student_id']
        name = request.form['name']
        department = request.form['department']
        semester = request.form['semester']
        credits = request.form['credits']
        dob = request.form['dob']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        enrollment_year = int(request.form['enrollment_year'])
        course_name = request.form['course_name']

        conn = sqlite3.connect('college.db')
        cursor = conn.cursor()
        cursor.execute(''' 
            UPDATE students 
            SET name=?, department=?, semester=?, credits=?, dob=?, email=?, phone=?, address=?, enrollment_year=?, course_name=?
            WHERE student_id=?
        ''', (name, department, semester, credits, dob, email, phone, address, enrollment_year, course_name, student_id))
        conn.commit()
        conn.close()
        return redirect('/view_students')

    return render_template('update_student.html')

@app.route('/add_course', methods=['GET', 'POST'])
def add_course():
    if request.method == 'POST':
        course_name = request.form['course_name']
        department = request.form['department']
        semester = request.form['semester']
        student_id = request.form['student_id']

        conn = sqlite3.connect('college.db')
        cursor = conn.cursor()

        cursor.execute(''' 
            INSERT INTO courses (course_name, department, semester)
            VALUES (?, ?, ?)
        ''', (course_name, department, semester))

        course_id = cursor.lastrowid

        cursor.execute(''' 
            INSERT INTO student_courses (student_id, course_id)
            VALUES (?, ?)
        ''', (student_id, course_id))

        conn.commit()
        conn.close()
        return redirect('/view_courses')

    return render_template('add_course.html')

@app.route('/view_courses', methods=['GET'])
def view_courses():
    conn = sqlite3.connect('college.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM courses')
    courses = cursor.fetchall()
    conn.close()
    return render_template('view_courses.html', courses=courses)

@app.route('/mark_attendance', methods=['GET', 'POST'])
def mark_attendance():
    conn = sqlite3.connect('college.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        student_id = request.form['student_id']
        course_name = request.form['course_name']
        date = request.form['date']
        status = request.form['status']

        cursor.execute('SELECT course_id FROM courses WHERE course_name = ?', (course_name,))
        course_id = cursor.fetchone()[0]

        cursor.execute(''' 
            INSERT INTO attendance (student_id, course_id, date, status)
            VALUES (?, ?, ?, ?)
        ''', (student_id, course_id, date, status))
        conn.commit()
        conn.close()

        return redirect('/mark_attendance')

    cursor.execute('SELECT student_id, name FROM students')
    students = cursor.fetchall()

    cursor.execute('SELECT course_name FROM courses')
    courses = cursor.fetchall()

    conn.close()

    return render_template('mark_attendance.html', students=students, courses=courses)

@app.route('/attendance_data/<student_id>', methods=['GET'])
def attendance_data(student_id):
    conn = sqlite3.connect('college.db')
    cursor = conn.cursor()
    cursor.execute(''' 
        SELECT course_id, date, status FROM attendance WHERE student_id = ?
    ''', (student_id,))
    records = cursor.fetchall()
    conn.close()

    data = {
        "dates": [record[1] for record in records],
        "statuses": [1 if record[2] == 'Present' else 0 for record in records] 
    }

    plt.figure(figsize=(10, 5))
    plt.plot(data["dates"], data["statuses"], marker='o', linestyle='-', color='b')
    plt.title(f'Attendance Record for Student ID: {student_id}')
    plt.xlabel('Date')
    plt.ylabel('Status (1=Present, 0=Absent)')
    plt.xticks(rotation=45)
    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()

    plot_url = base64.b64encode(img.getvalue()).decode()
    return render_template('attendance_chart.html', plot_url=plot_url)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
