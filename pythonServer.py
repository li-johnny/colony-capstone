from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['UPLOAD'] = 'static\Image'

@app.route("/", methods=['GET'])
def home():
    return render_template("index.html")

@app.route("/", methods=['POST'])
def getImage():
    
    file = request.files.get('img')
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD'], filename))
    img = os.path.join(app.config['UPLOAD'], filename)
    return render_template("index.html",image = img)

if __name__ == '__main__':
    app.run(debug=True)