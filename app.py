from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from functools import wraps
from werkzeug.utils import secure_filename
import os
app = Flask(__name__)
app.secret_key = "your_secret_key"
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="user_info"
)
cursor = db.cursor()
def get_available_courses(username):
    query = """
        SELECT c.courseid, c.coursename, c.description, c.duration, c.instructorname, c.instructorid
        FROM courses c
        LEFT JOIN enrollments e ON c.courseid = e.course_id
        WHERE e.student_id IS NULL
    """
    cursor.execute(query)
    available_courses = cursor.fetchall()
    return available_courses
def get_enrolled_students(course_id, instructor_id):
    query = """
        SELECT *
        FROM enrollments e
        JOIN users u ON e.student_id = u.user_id
        WHERE e.course_id = %s AND u.user_id != %s
    """
    cursor.execute(query, (course_id, instructor_id))
    enrolled_students = cursor.fetchall()
    return enrolled_students

def get_courses():
    query = """
        SELECT courseid, coursename
        FROM courses
    """
    cursor.execute(query)
    courses = cursor.fetchall()
    return courses

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        userid = request.form['userid']
        password = request.form['password']
        role = request.form['role']
        query = "SELECT * FROM users WHERE user_id = %s AND password = %s AND role=%s"
        cursor.execute(query, (userid, password,role))
        user = cursor.fetchone()
        if user:
            session['user'] = user[0]
            username=user[1]
            if role == 'student':
                return redirect(url_for('student_dashboard', username=username))
            elif role == 'instructor':
                return redirect(url_for('instructor_dashboard', username=username))
        else:
            return render_template('login.html', message="Invalid username, password, or role.")
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_id = request.form['user_id']
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        role = request.form['role']
        password = request.form['password']
        cursor.execute("INSERT INTO users (user_id,name,email,phoneno, role,password) VALUES (%s, %s, %s,%s, %s, %s)", (user_id, name, email, phoneno, role, password))
        db.commit()
        return render_template('login.html')
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('user_id', None)  
    return redirect(url_for('index'))
@app.route('/instructor/dashboard/<username>')
def instructor_dashboard(username):
    instructor_id = session['user']
    query = """
        SELECT *
        FROM courses
        WHERE instructorid = %s
    """
    cursor.execute(query, (instructor_id,))
    courses = cursor.fetchall()
    print(courses)
    return render_template('instructor_dashboard.html',username=username,courses=courses)
@app.route('/student/dashboard/<username>')
def student_dashboard(username):
   available_courses = get_available_courses(session['user'])  
   return render_template('student_dashboard.html', username=session['user'], available_courses=available_courses)   
@app.route('/postcourse')
def postcourse():
    return render_template('add_course.html',username=session['user'])
@app.route('/postcourse', methods=['GET', 'POST'])
def insertcourse():
    if request.method == 'POST':
        username = session['user']
        title = request.form['title']
        course_id = request.form['courseId']
        description = request.form['description']
        duration = request.form['duration']
        instructor_name = request.form['instructorName']
        instructor_id = request.form['instructorId']
        insert_query = "INSERT INTO courses (courseid, coursename, description, duration, instructorname, instructorid) VALUES (%s, %s, %s, %s, %s, %s)"
        cursor.execute(insert_query, (course_id, title, description, duration, instructor_name, instructor_id))
        db.commit()
        flash("Course added successfully", "success")
        return redirect(url_for('instructor_dashboard', username=username))
    return render_template('add_course.html')
@app.route('/postassignment')
def postassignment():
    return render_template('post_assignment.html',username=session['user'])
@app.route('/postassignment', methods=['GET', 'POST'])
def insertassignment():
    if request.method == 'POST':
        username = session['user']
        aid = request.form['assignmentid']
        title = request.form['title']
        description = request.form['description']
        sub = request.form['submission_date']
        marks = request.form['marks']
        course_id = request.form['course_id']
        insert_query = "INSERT INTO assignments (aid, title, description, sub, marks, course_id) VALUES (%s, %s, %s, %s, %s, %s)"
        cursor.execute(insert_query, (aid, title, description, sub, marks, course_id))
        db.commit()
        flash("Assignment added successfully", "success")
        return redirect(url_for('instructor_dashboard', username=username))
    return render_template('your_template.html')

@app.route('/enroll_course', methods=['POST'])
def enroll_course():
    username = session['user']
    course_id = (request.form['course_id'])
    course_to_enroll = None
    available_courses = get_available_courses(session['user'])
    for course in available_courses:
        if course[0] == course_id:
            course_to_enroll = course
            break
    if course_to_enroll:
        try:
            available_courses.remove(course_to_enroll)
            insert_query = "INSERT INTO enrollments (student_id, course_id) VALUES (%s, %s)"
            cursor.execute(insert_query, (username, course_id))
            db.commit()

            flash('You have successfully enrolled in the course!', 'success')
        except Exception as e:
            flash('Failed to enroll in the course. Please try again.', 'error')
    else:
        flash('Failed to enroll in the course. Course may not be available.', 'error')
    return redirect(url_for('student_dashboard', username=username))
@app.route('/mycourses')
def my_courses():
    user_id = session['user']
    query = """
        SELECT c.courseid, c.coursename, c.description, c.duration, c.instructorname, c.instructorid
        FROM courses c
        INNER JOIN enrollments e ON c.courseid = e.course_id
        WHERE e.student_id = %s
    """
    cursor.execute(query, (user_id,))
    enrolled_courses = cursor.fetchall()
    return render_template('mycourses.html',username=session['user'], enrolled_courses=enrolled_courses)
@app.route('/assignments')
def view_assignments():
    user_id = session['user']
    query_assignments = """
        SELECT a.*
        FROM assignments a
        INNER JOIN courses c ON a.course_id = c.courseid
        INNER JOIN enrollments e ON c.courseid = e.course_id
        WHERE e.student_id = %s
    """
    cursor.execute(query_assignments, (user_id,))
    assignments = cursor.fetchall()
    return render_template('assignment.html', username=session['user'], assignments=assignments)
@app.route('/unenroll_course', methods=['POST'])
def unenroll_course():
    course_id = request.form['course_id']
    user_id = session['user']
    query = "DELETE FROM enrollments WHERE student_id = %s AND course_id = %s"
    
    try:
        cursor.execute(query, (user_id, course_id))
        db.commit()
        flash('Successfully unenrolled from the course!', 'success')
    except Exception as e:
        flash('Failed to unenroll from the course. Please try again.', 'error')
    return redirect(url_for('student_dashboard', username=session['user']))
@app.route('/delete_course', methods=['POST'])
def delete_course():
    if request.method == 'POST':
        course_id = request.form['course_id']
        delete_query = "DELETE FROM courses WHERE courseid = %s"
        cursor.execute(delete_query, (course_id,))
        db.commit()
        return redirect(url_for('instructor_dashboard', username=session['user']))
@app.route('/view_enrolled_students', methods=['GET', 'POST'])
def view_enrolled_students():
    if request.method == 'POST':
        instructor_id = session['user']
        course_id = request.form['course_id']
        enrolled_students = get_enrolled_students(course_id,instructor_id)
        return render_template('enrolled.html',username=session['user'], courses=get_courses(), enrolled_students=enrolled_students)
    return render_template('enrolled.html',username=session['user'], courses=get_courses(), enrolled_students=None)
@app.route('/home')
def home():
    return redirect(url_for('student_dashboard',username=session['user']))
@app.route('/homeinstructor')
def homeinstructor():
    return redirect(url_for('instructor_dashboard',username=session['user']))
@app.route('/upload_assignment', methods=['POST'])
def upload_assignment():
    if request.method == 'POST':
        assignment_id = request.form['assignment_id']
        student_id = request.form['student_id']
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            cursor.execute('INSERT INTO submissions(assignment_id,student_id,filepath) VALUES (%s, %s, %s)',
                         (assignment_id,student_id,filename))
            db.commit()
            flash('Assignment uploaded successfully!', 'success')
            return redirect(url_for('student_dashboard', username=session['user']))
    else:
        return 'Method Not Allowed', 405        
if __name__ == '__main__':
    app.run(debug=True)
