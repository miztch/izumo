import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


ec2 = boto3.client('ec2')
rds = boto3.client('rds')
autoscaling = boto3.client('autoscaling')
ecs = boto3.client('ecs')


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
    instances = rds.describe_db_instances()['DBInstances']

    if len(instances) > 0:
        logger.info("Active RDS instances: {}".format(str(instances)))
        for instance in instances['DBInstances']:
            if instance['DBInstanceStatus'] == 'available':
                logger.info('Stop an RDS instance:' +
                            instance['DBInstanceIdentifier'])
                response = rds.stop_db_instance(
                    DBInstanceIdentifier=instance["DBInstanceIdentifier"])
    else:
        logger.info("No active RDS instances found.")


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


def stop_ecs_task():
    # do not consider protected task
    # https://aws.amazon.com/jp/blogs/news/announcing-amazon-ecs-task-scale-in-protection/
    cluster_arns = ecs.list_clusters()['clusterArns']
    cluster_names = [arn.split("/")[1] for arn in cluster_arns]

    if len(cluster_names) > 0:
        for cluster in cluster_names:
            # find ECS Services and update to terminate Tasks
            services = ecs.list_services(cluster=cluster)['serviceArns']
            service_names = [arn.split("/")[2] for arn in services]

            if len(service_names) > 0:
                logger.info("Active ECS services: {}. cluster: {}".format(
                    str(service_names), cluster))
                # update ECS Services to stop tasks
                for service in service_names:
                    ecs.update_service(
                        cluster=cluster,
                        service=service,
                        desiredCount=0
                    )
            else:
                logger.info(
                    "No active ECS services found in cluster: {}".format(cluster))

            # directly stop Tasks which is running without Services
            tasks = ecs.list_tasks(cluster=cluster)['taskArns']
            task_ids = [arn.split("/")[2] for arn in tasks]
            print(task_ids)

            if len(task_ids) > 0:
                logger.info("Active ECS tasks: {}".format(str(task_ids)))
                for task in task_ids:
                    ecs.stop_task(
                        cluster=cluster,
                        task=task,
                        reason='automatically stopped by izumo'
                    )
            else:
                logger.info(
                    "No active ECS tasks found in cluster: {}".format(cluster))
    else:
        logger.info("No active ECS clusters found.")


def lambda_handler(event, context):
    try:
        stop_ec2()
        stop_rds()
        update_autoscaling_group()
        stop_ecs_task()

    except Exception as e:
        logger.error(e)
