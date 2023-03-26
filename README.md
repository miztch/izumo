# izumo

"izumo" is a Lambda function optimizing your AWS infrastructure cost.

## What this Lambda function does
- stop all EC2 instances 
- stop all RDS instances
- terminate EC2 instances in all AutoScaling groups (by changing group size)

This function is triggered by EventBridge Event, and affects to the resources in the region deployed.

## Provisioning

You can use [AWS SAM](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html) to provision this function.

```bash
sam build
sam deploy --guided
```
