from flask import Flask, render_template, url_for, request, make_response, send_file
from wtforms import StringField, DecimalField, validators, SubmitField, ValidationError, DateField
from wtforms.validators import InputRequired
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from io import BytesIO
import pdfkit
import db_pass

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:' + db_pass.mysql_pass + '@localhost/generator'
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

#submiting form with download pdf file module not in CELERY YET
@app.route('/submit', methods=['GET', 'POST'])
def submit():
    form = MyForm()
    if form.validate_on_submit():
        new_pdf = (request.form['first_name'], request.form['last_name'], request.form['email'],
                   request.form['number'], request.form['pesel'], request.form['date'])

        rendered = render_template('pdf_template.html', form=form, new_pdf=new_pdf)

        pdf =pdfkit.from_string(rendered, False)

        response = make_response(pdf)
        response.headers['Content-Type'] = 'aplication/pdf'
        response.headers['Content-Disposition'] = "attachment; filename=" + request.form['name_of_the_file'] + ".pdf"

        return response

    return render_template('submit.html', form=form)

@app.route('/', methods=['GET'])
def homepage():
    return render_template('homepage.html')

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

