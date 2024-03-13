import time

import boto3

req_queue_url = "https://sqs.us-east-1.amazonaws.com/851725282796/1229503862-req-queue"

class Controller:

    def __init__(self, req_queue_url):
        self.sqs = boto3.client('sqs', region_name='us-east-1')
        self.ec2 = boto3.client('ec2', region_name='us-east-1')
        self.req_queue_url = req_queue_url
        self.desired_capacity = 0
        self.target_to_reach = 0
        self.target_not_reached_counter = 0
        self.recreate_instance_counter_val = 10
        self.max_target_not_reached_counter = 16
        self.instances = [None]*20
        self.instance_running = [False]*20


    def req_queue_length(self):
        response = self.sqs.get_queue_attributes(
            QueueUrl=self.req_queue_url,
            AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
        )
        visible_messages = int(response['Attributes']['ApproximateNumberOfMessages'])
        invisible_messages = int(response['Attributes']['ApproximateNumberOfMessagesNotVisible'])
        return visible_messages + invisible_messages


    def running_instance_count(self):
        instance_ids = [instance_id for instance_id in self.instances if instance_id is not None]
        resp = self.ec2.describe_instance_status(
            InstanceIds=instance_ids,
            IncludeAllInstances=True,
        )
        count = 0
        for i, instance_status in enumerate(resp['InstanceStatuses']):
            assert instance_status['InstanceState']['InstanceId'] == self.instances[i]
            self.instance_running[i] = instance_status['InstanceState']['Name'] == 'running'
            count = count + (1 if self.instance_running[i] else 0)


    def set_desired_capacity(self, capacity):
        self.desired_capacity = capacity


    def create_instance(self, name):
        resp = self.ec2.run_instances(
            LaunchTemplate={
                'LaunchTemplateName': 'app-tier-template'
            },
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': name,
                        },
                    ]
                },
            ],
            MaxCount=1,
            MinCount=1,
        )
        return resp['Instances'][0]['InstanceId']

    def update_instance_state(self):
        for i, instance in enumerate(self.instances):
            if i < self.desired_capacity and instance is not None and not self.instance_running[i] and self.target_not_reached_counter == self.recreate_instance_counter_val:
                print("Recreating instance: ", i + 1)
                self.ec2.terminate_instances(InstanceIds=[instance])
                self.instances[i] = self.instances[i] = self.create_instance('app-tier-instance-' + str(i + 1))
            elif i < self.desired_capacity and instance is None:
                self.instances[i] = self.create_instance('app-tier-instance-' + str(i + 1))
            elif i >= self.desired_capacity and instance is not None:
                 self.ec2.terminate_instances(InstanceIds=[instance])
                 self.instances[i] = None

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

        self.update_instance_state()


if __name__ == "__main__":
    controller = Controller(req_queue_url)

    while True:
        time.sleep(8)
        controller.autoscale()