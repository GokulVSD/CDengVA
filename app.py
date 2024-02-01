from flask import Flask, request
from pandas import read_csv

model = read_csv("model_res.csv")

app = Flask(__name__)


@app.route('/', methods=['GET'])
def get_root():
    return "Server is running!"


@app.route('/', methods=['POST'])
def upload_file():
    image_name = request.files['inputFile'].filename.split('.')[0]
    return image_name + ':' + model.loc[(model['Image'] == image_name)]['Results'].values[0]


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)