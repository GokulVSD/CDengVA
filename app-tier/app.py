import time
import os
import subprocess

import boto3

sqs = boto3.resource('sqs', region_name='us-east-1')
s3 = boto3.resource('s3', region_name='us-east-1')

req_queue = sqs.get_queue_by_name(QueueName="1229503862-req-queue")
resp_queue = sqs.get_queue_by_name(QueueName="1229503862-resp-queue")

in_bucket = s3.Bucket('1229503862-in-bucket')
out_bucket = s3.Bucket('1229503862-out-bucket')


def main():

    while True:
        # Read message from request sqs.
        messages = req_queue.receive_messages(
            MaxNumberOfMessages=5,
            VisibilityTimeout=10,
            WaitTimeSeconds=5,
        )

        if not messages:
            time.sleep(5)
            continue

        for message in messages:

            # Download image, run inference, upload image to s3.
            s3_image_filename = message.body

            in_bucket.download_file(s3_image_filename, s3_image_filename)

            result = subprocess.run(
                ['python3', 'face_recognition.py', s3_image_filename],
                stdout=subprocess.PIPE
            ).stdout.decode('utf-8')

            image_name = s3_image_filename.split('.')[0]

            with open(image_name, "w") as f:
                f.write(result)

            out_bucket.upload_file(image_name, image_name)

            # Cleanup.
            if os.path.exists(image_name):
                os.remove(image_name)

            if os.path.exists(s3_image_filename):
                os.remove(s3_image_filename)

            # Send message to response sqs.
            resp_queue.send_message(MessageBody=image_name + ':' + result)

            # After successfully processing this request, delete the message.
            message.delete()


if __name__ == "__main__":
    main()