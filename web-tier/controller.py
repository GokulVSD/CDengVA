import time

import boto3

req_queue_url = "https://sqs.us-east-1.amazonaws.com/851725282796/1229503862-req-queue"

asg_name = "app-tier-scaling-group"

class Controller:

    def __init__(self, asg_name, req_queue_url, max_instances=20):
        self.autoscaling = boto3.client('autoscaling', region_name='us-east-1')
        self.asg_name = asg_name
        self.sqs = boto3.client('sqs', region_name='us-east-1')
        self.req_queue_url = req_queue_url
        self.max_instances = max_instances
        self.target_to_reach = 0
        self.target_not_reached_counter = 0
        self.max_target_not_reached_counter = 8


    def req_queue_length(self):
        response = self.sqs.get_queue_attributes(
            QueueUrl=self.req_queue_url,
            AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
        )
        visible_messages = int(response['Attributes']['ApproximateNumberOfMessages'])
        invisible_messages = int(response['Attributes']['ApproximateNumberOfMessagesNotVisible'])
        return visible_messages + invisible_messages


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

    def can_scale_down(self, current_instance_count):
        if current_instance_count < self.target_to_reach:
            self.target_not_reached_counter += 1
            if self.target_not_reached_counter == self.max_target_not_reached_counter:
                print("Target could not be reached, scaling down anyway")
                self.target_not_reached_counter = 0
                self.target_to_reach = 0
                return True
            else:
                print("Target: ", self.target_to_reach, " not yet reached, not scaling down")
                return False
        print("Target: ", self.target_to_reach, " reached, scaling down")
        self.target_not_reached_counter = 0
        self.target_to_reach = 0
        return True

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
            self.target_to_reach = max(self.target_to_reach, new_instance_count)
            print("Setting capacity to: ", self.target_to_reach)
            self.set_desired_capacity(self.target_to_reach)

        elif instance_count > que_length:
            # Do not scale down until target_to_reach has been reached.
            if not self.can_scale_down(instance_count):
                return
            new_instance_count = instance_count - (instance_count - que_length)
            new_instance_count = max(0, new_instance_count)
            print("Setting capacity to: ", new_instance_count)
            self.set_desired_capacity(new_instance_count)


if __name__ == "__main__":
    controller = Controller(asg_name, req_queue_url)

    while True:
        time.sleep(8)
        controller.autoscale()