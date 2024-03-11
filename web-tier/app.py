import time
from fastapi import FastAPI, Request, Depends
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


async def get_form_data(request: Request):
    return await request.form()


@app.post('/', response_class=PlainTextResponse)
def upload_file(form = Depends(get_form_data)):
    image_file = form['inputFile']

    image_filename = image_file.filename

    in_bucket.put_object(
        Key=image_filename,
        Body=image_file.file,
    )

    req_queue.send_message(MessageBody=image_filename)

    image_name = image_filename.split('.')[0]

    time.sleep(60)

    while True:
        time.sleep(0.5)
        messages = resp_queue.receive_messages(
            MaxNumberOfMessages=10,
            VisibilityTimeout=0,
            WaitTimeSeconds=5,
        )

        if not messages:
            continue

        for message in messages:
            res = message.body

            if res.startswith(image_name):
                message.delete()
                return res