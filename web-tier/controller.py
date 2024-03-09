import time
from collections import Counter

import boto3

req_queue_url = "https://sqs.us-east-1.amazonaws.com/851725282796/1229503862-req-queue"

asg_name = "app-tier-scaling-group"

class Controller:

    def __init__(self, asg_name, req_queue_url, max_instances=20):
        self.autoscaling = boto3.client('autoscaling')
        self.asg_name = asg_name
        self.sqs = boto3.client('sqs')
        self.req_queue_url = req_queue_url
        self.max_instances = max_instances
        self.target_to_reach = 0


    def req_queue_length(self):
        """
        Check the queue 5 times in 2.5 seconds. Return the length with most frequency
        if greater than 2, else the average of all.
        """
        count = []
        for _ in range(5):
            response = self.sqs.get_queue_attributes(
                QueueUrl=self.req_queue_url,
                AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
            )
            visible_messages = int(response['Attributes']['ApproximateNumberOfMessages'])
            invisible_messages = int(response['Attributes']['ApproximateNumberOfMessagesNotVisible'])
            count.append(visible_messages + invisible_messages)
            time.sleep(0.5)

        counts = Counter(count)

        if counts.most_common(1)[0][1] > 2:
            return counts.most_common(1)[0][0]

        return sum(count) // len(count)


    def running_instance_count(self):
        response = self.autoscaling.describe_auto_scaling_groups(
            AutoScalingGroupNames=[self.asg_name],
            MaxRecords=1
        )
        instances = response['AutoScalingGroups'][0]['Instances']
        running_instances = [instance for instance in instances if instance['LifecycleState'] == 'InService']
        return len(running_instances)


    def set_desired_capacity(self, capacity):
        self.autoscaling.set_desired_capacity(
            AutoScalingGroupName=self.asg_name,
            DesiredCapacity=capacity,
        )


    def autoscale(self):
        """
        Policy:
        1. If req_queue has more messages than current instances, scale out upto number of
        messages up to 20.
        2. If req_queue has less messages than current instances, scale in till number of messages in
        queue down to 0.
        """
        instance_count = self.running_instance_count()
        que_length = self.req_queue_length()

        print("Instances: ", instance_count)
        print("Queue length: ", que_length)

        if instance_count < que_length:
            new_instance_count = instance_count + (que_length - instance_count)
            new_instance_count = min(20, new_instance_count)
            print("Setting capacity to: ", new_instance_count)
            target_to_reach = max(target_to_reach, new_instance_count)
            self.set_desired_capacity(new_instance_count)

        elif instance_count > que_length:
            # Do not scale down until target_to_reach has been reached.
            if instance_count < target_to_reach:
                return
            target_to_reach = 0
            new_instance_count = instance_count - (instance_count - que_length)
            new_instance_count = max(0, new_instance_count)
            print("Setting capacity to: ", new_instance_count)
            self.set_desired_capacity(new_instance_count)


if __name__ == "__main__":
    controller = Controller(asg_name, req_queue_url)

    while True:
        time.sleep(3)
        controller.autoscale()