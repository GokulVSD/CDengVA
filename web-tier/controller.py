import time

import boto3

sqs = boto3.resource('sqs', region_name='us-east-1')

req_queue = sqs.get_queue_by_name(QueueName="1229503862-req-queue")

autoscale = boto3.client('autoscaling')

class Controller:

    def __init__(self, autoscale, req_queue, max_instances=20, max_instances_per_cycle=3):
        self.req_queue = req_queue
        self.max_instances = max_instances
        self.max_instances_per_cycle = max_instances_per_cycle

    def autoscale():
        """
        Policy:
        1. If req_queue has more messages than current instances, scale out upto number of
        messages in queue with a maximum of max_instances_per_cycle for every call to the method.
        2. If req_queue has less messages than current instances, scale in till number of messages in
        queue with a maximum of max_instances_per_cycle for every call to the method.
        """
        pass


if __name__ == "__main__":
    controller = Controller(autoscale, req_queue)

    while True:
        time.sleep(2)
        controller.autoscale()