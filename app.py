from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from pandas import read_csv

app = FastAPI()

csv_model = read_csv("model.csv")

model = {}

for row in csv_model.iterrows():
    model[row[1]['Image']] = row[1]['Results']


@app.get('/')
async def get_root():
    return "Server is running!"


@app.post('/', response_class=PlainTextResponse)
async def upload_file(request: Request):
    form = await request.form()
    filename = form['inputFile'].filename
    image_name = filename.split('.')[0]
    return image_name + ':' + model[image_name]