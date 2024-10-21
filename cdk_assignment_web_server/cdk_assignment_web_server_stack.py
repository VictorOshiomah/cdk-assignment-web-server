import os.path

from aws_cdk.aws_s3_assets import Asset as S3asset

from aws_cdk import (
    # Duration,
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    # aws_s3 as s3,
    aws_rds as rds,
    # aws_sqs as sqs,
)
import aws_cdk as cdk
from constructs import Construct

dirname = os.path.dirname(__file__)

class CdkAssignmentWebServerStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, cdk_vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # Instance Role and SSM Managed Policy
        InstanceRole = iam.Role(self, "InstanceSSM", assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"))

        InstanceRole.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"))
        
        web_server_sg = ec2.SecurityGroup(self, "WebServerSG",
            vpc=cdk_vpc,
            allow_all_outbound=True
        )
        web_server_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "Allow HTTP access")

        # Script in S3 as Asset
        webinitscriptasset = S3asset(self, "Asset", path=os.path.join(dirname, "configure.sh"))

        # Launch web servers in each public subnet
        # Create the first EC2 instance in the first public subnet
        assignment_instance1 = ec2.Instance(self, "AssignmentInstance1",
            vpc=cdk_vpc,
            vpc_subnets=ec2.SubnetSelection(subnets=[cdk_vpc.public_subnets[0]]),
            security_group=web_server_sg,
            instance_type=ec2.InstanceType("t2.micro"),
            machine_image=ec2.AmazonLinuxImage(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2),
            role=InstanceRole
        )
        # Script in S3 as Asset-Path
        asset_path1 = assignment_instance1.user_data.add_s3_download_command(
            bucket=webinitscriptasset.bucket,
            bucket_key=webinitscriptasset.s3_object_key
        )
        # Userdata executes script from S3
        assignment_instance1.user_data.add_execute_file_command(file_path=asset_path1)
        webinitscriptasset.grant_read(assignment_instance1.role)

        # Create the second EC2 instance in the second public subnet
        assignment_instance2 = ec2.Instance(self, "AssignmentInstance2",
            vpc=cdk_vpc,
            vpc_subnets=ec2.SubnetSelection(subnets=[cdk_vpc.public_subnets[1]]),
            security_group=web_server_sg,
            instance_type=ec2.InstanceType("t2.micro"),
            machine_image=ec2.AmazonLinuxImage(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2),
            role=InstanceRole
        )

        # Script in S3 as Asset-Path
        asset_path2 = assignment_instance2.user_data.add_s3_download_command(
            bucket=webinitscriptasset.bucket,
            bucket_key=webinitscriptasset.s3_object_key
        )
        # Userdata executes script from S3
        assignment_instance2.user_data.add_execute_file_command(file_path=asset_path2)
        webinitscriptasset.grant_read(assignment_instance2.role)
        
        # Security group for RDS instance
        rds_sg = ec2.SecurityGroup(self, "RdsSG",
            vpc=cdk_vpc,
            allow_all_outbound=True
        )
        rds_sg.add_ingress_rule(web_server_sg, ec2.Port.tcp(3306), "Only web servers SG")

        # Create RDS MySQL instance
        rds.DatabaseInstance(self, "MyRdsInstance",
            engine=rds.DatabaseInstanceEngine.mysql(version=rds.MysqlEngineVersion.VER_8_0),
            vpc=cdk_vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_groups=[rds_sg],
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.T3,
                ec2.InstanceSize.MICRO
            ),
            allocated_storage=20,
            max_allocated_storage=100,
            database_name="MyDatabase"
        )