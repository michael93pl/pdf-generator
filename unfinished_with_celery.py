from flask import Flask, render_template, url_for, request, make_response, send_file, app
from wtforms import StringField, DecimalField, validators, SubmitField, ValidationError, DateField
from wtforms.validators import InputRequired
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_celery import make_celery
from io import BytesIO
import pdfkit
import db_pass

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:' + db_pass.mysql_pass + '@localhost/generator'
app.config.update(
    CELERY_BROKER_URL='amqp://localhost//',
    PRESERVE_CONTEXT_ON_EXCEPTION=False)

celery = make_celery(app)
db = SQLAlchemy(app)

class FileContent(db.Model):
    __tablename__ = 'files'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300))
    data = db.Column(db.LargeBinary)

db.create_all()
db.session.commit()

app.config.update(dict(
    SECRET_KEY="awesome key"
))

class MyForm(FlaskForm):
    name_of_the_file = StringField('Name of the file', validators=[InputRequired()])
    first_name = StringField('First Name', validators=[InputRequired()])
    last_name = StringField('Last Name', validators=[InputRequired()])
    email = StringField('Email Address', validators=[InputRequired()])
    number = DecimalField('Phone number', validators=[InputRequired()])
    pesel = DecimalField('PESEL', validators=[InputRequired()])
    date = DateField('Date yyyy-mm-dd', validators=[InputRequired()], format='%Y-%m-%d')

@app.route('/', methods=['GET'])
def homepage():
    return render_template('homepage.html')

@celery.task(name='main.create_pdf.generate')
def generate(form):
    with app.app_context().push():
        form = MyForm()
        new_pdf = (request.form['first_name'], request.form['last_name'], request.form['email'],
               request.form['number'], request.form['pesel'], request.form['date'])

        rendered = render_template('pdf_template.html', form=MyForm, new_pdf=new_pdf)
        pdf = pdfkit.from_string(rendered, False)

        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = "attachment; filename=" + request.form['name_of_the_file'] + ".pdf"

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        form = MyForm(request.form)

        if form.validate_on_submit():
            generate.delay(request.form)
            return "it worked ! "
    else:
        form = MyForm()
    return render_template('submit.html', form=form)


#upload file module
@app.route('/choose-file', methods=['GET', 'POST'])
def choose_file():
    return render_template('choose_file.html')

#saves the file inside the db
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    file = request.files['inputFile']
    newFile = FileContent(name=file.filename, data=file.read())
    db.session.add(newFile)
    db.session.commit()

    return render_template('uploaded.html')

# display pdf module with download option
@app.route('/list', methods=['GET', 'POST'])
def list():
    list = db.session.query(FileContent)
    return render_template('list.html', list=list)

@app.route('/download', methods=['GET', 'POST'])
def download():
    file_data = db.session.query(FileContent).filter(FileContent.name == request.form['item']).first()
    return send_file(BytesIO(file_data.data), attachment_filename=request.form['item'], as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)

