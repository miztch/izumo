import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


ec2 = boto3.client('ec2')
rds = boto3.client('rds')
autoscaling = boto3.client('autoscaling')


def stop_ec2():
    instances = []

    running_instances = ec2.describe_instances(
        Filters=[
            {
                'Name': 'instance-state-name',
                'Values': ['running']
            }
        ]
    )

    for reservation in running_instances['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance.get('InstanceId')
            instances.append(instance_id)

    if len(instances) > 0:
        logger.info('Stop EC2 instances: ' + str(instances))
        ec2.stop_instances(InstanceIds=instances)
    else:
        logger.info('No running EC2 instances found.')


def stop_rds():
    all_instances = rds.describe_db_instances()

    if len(all_instances) > 0:
        logger.info("Active RDS instances: {}".format(str(all_instances)))
        for instance in all_instances['DBInstances']:
            if instance['DBInstanceStatus'] == 'available':
                logger.info('Stop an RDS instance:' +
                            instance['DBInstanceIdentifier'])
                response = rds.stop_db_instance(
                    DBInstanceIdentifier=instance["DBInstanceIdentifier"])
    else:
        logger.info("No available RDS instances found.")


def update_autoscaling_group():
    autoscaling_groups = []

    active_groups = autoscaling.describe_auto_scaling_groups()

    for autoscaling_group in active_groups['AutoScalingGroups']:
        group_name = autoscaling_group['AutoScalingGroupName']
        autoscaling_groups.append(group_name)

    if len(autoscaling_groups) > 0:
        logger.info("Active AutoScaling groups: {}".format(
            str(autoscaling_groups)))
        stop_param = dict(MinSize=0, DesiredCapacity=0)
        for autoscaling_group in autoscaling_groups:
            autoscaling.update_auto_scaling_group(
                AutoScalingGroupName=autoscaling_group, **stop_param)
    else:
        logger.info("No active Autoscaling groups found.")


def lambda_handler(event, context):
    try:
        stop_ec2()
        stop_rds()
        update_autoscaling_group()

    except Exception as e:
        logger.error(e)
