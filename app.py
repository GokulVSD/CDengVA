from flask import Flask, request
from pandas import read_csv

csv_model = read_csv("model_res.csv")

model = {}

for row in csv_model.iterrows():
    model[row[1]['Image']] = row[1]['Results']

app = Flask(__name__)


@app.route('/', methods=['GET'])
def get_root():
    return "Server is running!"


@app.route('/', methods=['POST'])
def upload_file():
    image_name = request.files['inputFile'].filename.split('.')[0]
    return image_name + ':' + model[image_name]


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)