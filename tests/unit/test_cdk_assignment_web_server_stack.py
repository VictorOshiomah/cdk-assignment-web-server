import aws_cdk as core
import aws_cdk.assertions as assertions

from cdk_assignment_web_server.cdk_assignment_web_server_stack import CdkAssignmentWebServerStack

# example tests. To run these tests, uncomment this file along with the example
# resource in cdk_assignment_web_server/cdk_assignment_web_server_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CdkAssignmentWebServerStack(app, "cdk-assignment-web-server")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
