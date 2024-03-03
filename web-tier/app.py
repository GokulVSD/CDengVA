from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import boto3

sqs = boto3.resource('sqs', region_name='us-east-1')
s3 = boto3.resource('s3', region_name='us-east-1')

req_queue = sqs.get_queue_by_name(QueueName="1229503862-req-queue")
resp_queue = sqs.get_queue_by_name(QueueName="1229503862-resp-queue")

in_bucket = s3.Bucket('1229503862-in-bucket')

app = FastAPI()


@app.get('/')
async def get_root():
    return "Web-tier is running!"


@app.post('/', response_class=PlainTextResponse)
async def upload_file(request: Request):
    form = await request.form()

    image_file = form['inputFile']

    image_filename = image_file.filename

    in_bucket.put_object(
        Key=image_filename,
        Body=image_file,
    )

    req_queue.send_message(MessageBody=image_filename)

    image_name = image_filename.split('.')[0]

    while True:
        messages = req_queue.receive_messages()

        if not messages:
            continue

        for message in messages:
            res = message.body

            if res.startswith(image_name):
                message.delete()
                return res