import os
import subprocess

import boto3
# from botocore.exceptions import ClientError

sqs = boto3.resource('sqs', region_name='us-east-1')
s3 = boto3.resource('s3', region_name='us-east-1')

# s3_client = boto3.client('s3')

req_queue = sqs.get_queue_by_name(QueueName="1229503862-req-queue")
resp_queue = sqs.get_queue_by_name(QueueName="1229503862-resp-queue")

IN_BUCKET_NAME = '1229503862-in-bucket'
OUT_BUCKET_NAME = '1229503862-out-bucket'

in_bucket = s3.Bucket(IN_BUCKET_NAME)
out_bucket = s3.Bucket(OUT_BUCKET_NAME)

# def check_key_exists_in_output_bucket(key):
#     try:
#         s3_client.head_object(Bucket=OUT_BUCKET_NAME, Key=key)
#         return True
#     except ClientError as e:
#         return False

def main():

    while True:

        # Read message from request sqs.
        messages = req_queue.receive_messages(
            MaxNumberOfMessages=1,
            VisibilityTimeout=15,
            WaitTimeSeconds=0,
        )

        if not messages:
            continue

        message = messages[0]

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