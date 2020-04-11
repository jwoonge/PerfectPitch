from flask import Flask

app = Flask(__name__)

@app.route('/')

def hello() :
  return 'HELLO! MJJ!'


if __name__ == '__main__':
  app.run()
