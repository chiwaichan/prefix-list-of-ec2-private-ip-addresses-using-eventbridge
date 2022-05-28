AWS VPC customer-managed prefix list is a great feature to have in a tool box as it provides the ability to track and maintain a list of CIDR block values, that can be referenced by other AWS Networking component’s in their rules and tables. Each Prefix List supports either IPv4 or IPv6 based addresses, and a number of expected Max Entries for the list must be defined; the number of entries in the list cannot exceed the Max Entries. Check out my blog on [AWS Prefix List](https://chiwaichan.co.nz/2022/05/28/leveraging-aws-prefix-lists) to learn how it could be referenced and leveraged by other AWS Networking components.

In this blog we will:
- Walk-through the proposed solution
- Deploy the solution from a SAM project hosted in my [GitHub repository](https://github.com/chiwaichan/prefix-list-of-ec2-private-ip-addresses-using-eventbridge)
- Stop the running EC2 instance provisioned by the SAM project's CloudFormation stack - this will de-register the Private IP address of the EC2 instance from the Prefix List (also provisioned by the CloudFormation stack)
- Start the same EC2 instance - this will register the Private IP address of the provisioned EC2 instance back into the Prefix List
- Manually create an EC2 instance with a Tag value of "prefix-list=eventbridge-managed-prefix-list"

# Solution
In this solution we propose an architecture to maintain a list of EC2 Private IPs in a Prefix List by leveraging EventBridge to listen for EC2 Instance State Change Events.

![1](https://github.com/chiwaichan/blog-assets/raw/main/images/maintain-a-prefix-list-of-ec2-private-ip-addresses-using-eventbridge/1-eventbridge-ec2-instance-state-events.png)

Depending on the EC2 Instance State Change value we will perform a different action against the Prefix List using a Lambda Function: if the Instance State is “running" then we register the Private IP address into the Prefix List; or, deregister the Private IP address from the Prefix list when the Instance State is “stopping”.

![2](https://github.com/chiwaichan/blog-assets/raw/main/images/maintain-a-prefix-list-of-ec2-private-ip-addresses-using-eventbridge/2-eventbridge-ec2-instance-state-events-sequence.png)


When the event is received by the Lambda function, it will perform a lookup on the Tags of the EC2 instance for a Tag (e.g. prefix-list=eventbridge-managed-prefix-list) that indicates which Prefix List (or Lists) the Lambda function will register/de-register the Private IP against. The Prefix List should be maintained economically - because it affects the quotas of resources that reference this Prefix List as described by the AWS documentation: [Prefix lists concepts and rules](https://docs.aws.amazon.com/vpc/latest/userguide/managed-prefix-lists.html), so the Lambda function should ideally set the Prefix List Max Entries to the number of entries expected in the list before an entry is registered, or, afterwards if an entry de-registered.


By maintaining a Prefix List and leveraging this pattern in your solutions, your solutions may potentially benefit in the following ways:
- Reusability of configurations which will reduce the operational burden and improve consistency. 
- Re-use of Prefix Lists by sharing it with other AWS accounts by leveraging Resource Access Manager
- Creates an automated mechanism to track and maintain a definitive list of Private IP addresses of similarly grouped of EC2 instances with non-deterministic IP addresses 
- High cohesion and low Coupling designs: reduce manual flow on changes when a change is implemented 
- Leverage programmatic mechanisms for automatically changes and maintenance – minimise deployments and/or manual tasks
- Improve Security posture: this may potentially reduce occurances of overly broad CIDR values used in rules or route tables where it is used to encompass a few number of IP address within a wide IP range


# Deploying the solution

Here we will walk-through the steps involved to deploy a SAM project of this solution hosted in my GitHub repository: [https://github.com/chiwaichan/prefix-list-of-ec2-private-ip-addresses-using-eventbridge](https://github.com/chiwaichan/prefix-list-of-ec2-private-ip-addresses-using-eventbridge)

Prerequisites:
- [Install AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
- [Configure your CLI credentials](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html)

Run the following command to checkout the code

```
git clone git@github.com:chiwaichan/prefix-list-of-ec2-private-ip-addresses-using-eventbridge.git

cd prefix-list-of-ec2-private-ip-addresses-using-eventbridge/
```

![3](https://github.com/chiwaichan/blog-assets/raw/main/images/maintain-a-prefix-list-of-ec2-private-ip-addresses-using-eventbridge/3-git-clone.png)

Run the following command to configure the SAM deploy 

```
sam deploy --guided
```

Enter the following arguments in the prompt:
- Stack Name: prefix-list-of-ec2-private-ip-addresses-using-eventbridge
- AWS Region: ap-southeast-2 or the value of your preferred Region
- Parameter ImageID: ami-0c6120f461d6b39e9 (the Amazon Linux AMI ID in ap-southeast-2), you can use any AMI ID for your Region
- Parameter SecurityGroupId: the Security Group ID to use for the EC2 instance provisioned, e.g. sg-0123456789
- Parameter SubnetId: the Subnet ID of the Subnet to deploy the EC2 instance in, e.g. subnet-0123456678


![4](https://github.com/chiwaichan/blog-assets/raw/main/images/maintain-a-prefix-list-of-ec2-private-ip-addresses-using-eventbridge/4-sam-deploy.png)

![5](https://github.com/chiwaichan/blog-assets/raw/main/images/maintain-a-prefix-list-of-ec2-private-ip-addresses-using-eventbridge/5-sam-deploy.png)

![6](https://github.com/chiwaichan/blog-assets/raw/main/images/maintain-a-prefix-list-of-ec2-private-ip-addresses-using-eventbridge/6-sam-deploy.png)

## Confirm the deployment
Let's check to see that everything has been deployed correctly in our AWS account.

Here we can see the list of AWS resources deployed in the CloudFormation Stack

![7](https://github.com/chiwaichan/blog-assets/raw/main/images/maintain-a-prefix-list-of-ec2-private-ip-addresses-using-eventbridge/7-cloudformation-resources.png)

Here we can see the details of the EC2 instance provisioned in a "Running" state. Take note of the Private IPv4 address.
![8](https://github.com/chiwaichan/blog-assets/raw/main/images/maintain-a-prefix-list-of-ec2-private-ip-addresses-using-eventbridge/8-ec2-instance.png)

This is the Prefix List provisioned; here we can see the Private IPv4 address of the EC2 instance in the Prefix list entries. Also, note that the Max Entries is currently set to 1.
![9](https://github.com/chiwaichan/blog-assets/raw/main/images/maintain-a-prefix-list-of-ec2-private-ip-addresses-using-eventbridge/9-prefix-list.png)

# Stopping the running EC2 Instance

Let's stop the EC2 instance

![10](https://github.com/chiwaichan/blog-assets/raw/main/images/maintain-a-prefix-list-of-ec2-private-ip-addresses-using-eventbridge/10-stopping-ec2-instance.png)

We should see the Private IP address of the EC2 instance removed from the Prefix List Entries, the Max Entries remains as 1 - this is because the minimum value must be 1 even when there are no Entries in the Prefix List

![11](https://github.com/chiwaichan/blog-assets/raw/main/images/maintain-a-prefix-list-of-ec2-private-ip-addresses-using-eventbridge/11-prefix-list-entry-removed.png)

This is the sniplet of Python code in the [Lambda function](https://github.com/chiwaichan/prefix-list-of-ec2-private-ip-addresses-using-eventbridge/blob/main/prefix_list_function/update_prefix_list/app.py) that removes the Private IP address from the Prefix List:

```
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
```

# Starting the stopped EC2 Instance

Let's start the EC2 instance

![12](https://github.com/chiwaichan/blog-assets/raw/main/images/maintain-a-prefix-list-of-ec2-private-ip-addresses-using-eventbridge/12-starting-ec2-instance.png)

We should see the Private IP address of the EC2 instance added back to the Prefix List Entries. Note the description is different to what it was when we first saw it earlier.

![13](https://github.com/chiwaichan/blog-assets/raw/main/images/maintain-a-prefix-list-of-ec2-private-ip-addresses-using-eventbridge/13-prefix-list-add.png)

This is the sniplet of Python code in the [Lambda function](https://github.com/chiwaichan/prefix-list-of-ec2-private-ip-addresses-using-eventbridge/blob/main/prefix_list_function/update_prefix_list/app.py) that adds the Private IP address to the Prefix List:

```
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
```


# Manually create an EC2 instance with a Prefix List Tag 

Let's launch a new EC2 instance (using any AMI and deploy it in any Subnet with any Security Group) with a value of "eventbridge-managed-prefix-list" for the "prefix-list" Tag, the EventBridge and Lambda will register the Private IP address of this newly created instance into the Prefix List "eventbridge-managed-prefix-list".


![14](https://github.com/chiwaichan/blog-assets/raw/main/images/maintain-a-prefix-list-of-ec2-private-ip-addresses-using-eventbridge/14-launch-ec2-instance.png)

![15](https://github.com/chiwaichan/blog-assets/raw/main/images/maintain-a-prefix-list-of-ec2-private-ip-addresses-using-eventbridge/15-new-ec2-instance.png)

![16](https://github.com/chiwaichan/blog-assets/raw/main/images/maintain-a-prefix-list-of-ec2-private-ip-addresses-using-eventbridge/16-new-ec2-instance-tags.png)

Here we see the Private IP address of the new manually created EC2 instance appear in the Prefix List Entries; also, the Max Entries has been updated to 2 by the Lambda function.

![17](https://github.com/chiwaichan/blog-assets/raw/main/images/maintain-a-prefix-list-of-ec2-private-ip-addresses-using-eventbridge/17-prefix-list-new-ec2-add.png)

FYI, You can adapted this pattern and Lambda function to add or remove Private IP addresses based on the EC2 instance state change value of your choosing.

# Clean up

- Delete the manually created EC2 instance; afterwards, you can see it removed from the Prefix List and the Prefix List's Max Entries decreased back down to 1 by the Lambda function
- Delete the CloudFormation stack with the name "prefix-list-of-ec2-private-ip-addresses-using-eventbridge"



This solution compliments the use of networking solutions in other blogs I have written:
- [Work-around for cross-account Transit Gateway Security Group Reference](https://chiwaichan.co.nz/2022/05/28/work-around-for-cross-account-transit-gateway-security-group-reference) 
- [AWS Prefix List](https://chiwaichan.co.nz/2022/05/28/leveraging-aws-prefix-lists)
- [Breaking Down Monolithic Subnets](https://chiwaichan.co.nz/2022/05/28/breaking-down-monolithic-subnets)
- [Swiss Cheese Network Security: Factorising Security Group Rules into NACLs and Security Group Rules](https://chiwaichan.co.nz/2022/05/06/factorising-security-group-rules-into-nacls-and-security-group-rules)
