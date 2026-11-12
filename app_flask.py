from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    # Esto le dice a Flask que busque el archivo index.html
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
