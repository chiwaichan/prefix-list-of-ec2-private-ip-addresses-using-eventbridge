from schema.aws.ec2.ec2instancestatechangenotification import Marshaller
from schema.aws.ec2.ec2instancestatechangenotification import AWSEvent
from schema.aws.ec2.ec2instancestatechangenotification import EC2InstanceStateChangeNotification
import boto3
from time import sleep


def lambda_handler(event, context):
    #Deserialize event into strongly typed object
    awsEvent:AWSEvent = Marshaller.unmarshall(event, AWSEvent)
    detail:EC2InstanceStateChangeNotification = awsEvent.detail

    client = boto3.client('ec2')

    ec2_detail = awsEvent.detail

    ec2_id = ec2_detail.instance_id
    ec2_state = ec2_detail.state

    response = client.describe_instances(InstanceIds=[ec2_id])

    # the private IP address we for the EC2 instance
    private_id_address = response["Reservations"][0]["Instances"][0]["PrivateIpAddress"]

    response = client.describe_tags(
        DryRun=False,
        Filters=[
            {
                'Name': 'resource-id',
                'Values': [ec2_id]
            },
        ]
    )

    prefix_list_name = None

    # identify the Prefix List to register / deregister the Private IP for
    for tag in response["Tags"]:
        if tag["Key"] == "prefix-list":
            prefix_list_name = tag["Value"]
            break
        

    # Is there a value for the 'prefix-list' Tag on the EC2 instance?
    if prefix_list_name is not None:
        response = client.describe_managed_prefix_lists(
            Filters=[
                {
                    'Name': 'prefix-list-name',
                    'Values': [
                        prefix_list_name,
                    ]
                },
            ],
            MaxResults=1
        )

        # we register / deregister if the private IP if we found a value for Tag 'prefix-list'
        if len(response["PrefixLists"]) > 0: 
            prefix_list = response["PrefixLists"][0]

            current_prefix_list_version = prefix_list["Version"]
            prefix_list_id = prefix_list["PrefixListId"]

            response = client.get_managed_prefix_list_entries(
                PrefixListId=prefix_list_id,
                MaxResults= prefix_list["MaxEntries"]
            )

            # Is the EC2 instance private IP in the Entries of the Prefix List
            current_entries = response["Entries"]
            is_in_list = False

            for ent in current_entries:
                if ent["Cidr"] == private_id_address + "/32":
                    is_in_list = True
                    break

            # if the instance state change is 'running' so we add the private IP CIDR to the Prefix List
            if ec2_state == "running":
                if is_in_list:
                    print("already in list so no action")
                else:
                    print("add")

                    if len(current_entries) + 1 != prefix_list["MaxEntries"]:
                        response = client.modify_managed_prefix_list(
                            PrefixListId=prefix_list_id,
                            MaxEntries=len(current_entries) + 1
                        )

                        sleep(3)

                    response = client.modify_managed_prefix_list(
                        PrefixListId=prefix_list_id,
                        CurrentVersion=current_prefix_list_version,
                        AddEntries=[
                            {
                                'Cidr': private_id_address + "/32",
                                'Description': 'added by EventBridge Lambda'
                            },
                        ]
                    )
            # if the instance state change is 'stopping' so we remove the private IP CIDR to the Prefix List
            elif ec2_state == "stopping":
                if is_in_list:
                    print("remove")

                    response = client.modify_managed_prefix_list(
                        PrefixListId=prefix_list_id,
                        CurrentVersion=current_prefix_list_version,
                        RemoveEntries=[
                            {
                                'Cidr': private_id_address + "/32"
                            },
                        ]
                    )

                    if len(current_entries) != 1: 
                        sleep(3)

                        response = client.modify_managed_prefix_list(
                            PrefixListId=prefix_list_id,
                            MaxEntries=len(current_entries) - 1
                        )
                else:
                    print("not in list so no action")

    return Marshaller.marshall(awsEvent)
