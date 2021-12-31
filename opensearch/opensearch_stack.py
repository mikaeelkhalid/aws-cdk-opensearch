from aws_cdk import (
    aws_iam as iam,
    aws_sns_subscriptions as subs,
    core,
    aws_iot as iot,
    aws_opensearchservice as opensearch,
    aws_lambda as _lambda,
    aws_s3 as s3,
)


class OpensearchStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # 0.1 create iam policy for lambda to opensearch
        lambda_to_opensearch_policy = iam.Policy(
            self,
            "lambda_to_opensearch_policy",
            policy_name="lambda_to_opensearch_policy",
            statements=[
                iam.PolicyStatement(
                    actions=[
                        "es:*",
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=[
                        "*"
                    ],
                )]    
        )

        # 0.2 create iam role for lambda basic execution and lambda to opensearch
        opensearch_api_role = iam.Role(
            self,
            "opensearch_api_role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
            ]

        )
        
        # 0.3 attach lambda to open search policy to opensearch role
        lambda_to_opensearch_policy.attach_to_role(opensearch_api_role)

        # 1 create a openserch domain
        prod_domain = opensearch.Domain(self, "CdkDomainOpenSearch",
            version=opensearch.EngineVersion.OPENSEARCH_1_0,
            enforce_https=True,
            node_to_node_encryption=True,
            use_unsigned_basic_auth=True,
            capacity=opensearch.CapacityConfig(
                data_nodes=2,
                data_node_instance_type="t3.small.search"
            ),
            ebs=opensearch.EbsOptions(
                volume_size=10
            ),
            zone_awareness=opensearch.ZoneAwarenessConfig(
                availability_zone_count=2,
                enabled=False,
            ),
            encryption_at_rest=opensearch.EncryptionAtRestOptions(
                enabled=True
            ),
            fine_grained_access_control=opensearch.AdvancedSecurityOptions(
                master_user_arn=opensearch_api_role.role_arn,
            )
        )

        # 2 create an IAM role to have permission to dump data into openserch
        cdk_role = iam.Role(self, "CdkRoleOpenSearch",
            assumed_by=iam.ServicePrincipal("iot.amazonaws.com"))
        cdk_role.add_to_policy(iam.PolicyStatement(
            actions=["es:ESHttpPut"],
            resources=[prod_domain.domain_arn + "/*"]
        ))

        # 3 get the bucket object from bucket arn
        bucket_layer = s3.Bucket.from_bucket_arn(self, 
            "open_search_lambda_layer", 
            "arn:aws:s3:::mikaeel-bucket"
            )

        # 4 create a lambda function layer
        lambda_layer = _lambda.LayerVersion(self, "CdkLambdaLayer",
            code=_lambda.Code.from_bucket(bucket_layer, "os_layer.zip"),  
            compatible_runtimes = [_lambda.Runtime.PYTHON_3_8, _lambda.Runtime.PYTHON_3_9],
        )

        # 5 create lambda function to munupulate opensearch api
        opensearch_api_lambda = _lambda.Function(self, "opensearch_api_lambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="opensearch_api.lambda_handler",
            code=_lambda.Code.from_asset("opensearch_api/lambda"),
            role=opensearch_api_role,
            timeout=core.Duration.seconds(900),
            environment={                
                "DOMAIN_ENDPOINT": prod_domain.domain_endpoint,
                "OPENSEARCH_API_ROLE": opensearch_api_role.role_arn,
                "CDK_ROLE_ARN": cdk_role.role_arn,
            },
            layers=[lambda_layer]
        )

        # 6 defines an IoT Rule to send data to opensearch
        iot_topic_rule = iot.CfnTopicRule(self, "CdkIoTTopicRuleOpenSearch",
         topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty(
                sql="SELECT * FROM 'KKIA/speed/#'",
                enabled=False,
                actions=[iot.CfnTopicRule.ActionProperty(
                open_search=iot.CfnTopicRule.OpenSearchActionProperty(
                endpoint="https://"+prod_domain.domain_endpoint,
                id="${newuuid()}",
                index="speed",
                role_arn=cdk_role.role_arn,
                type="_doc"
             ),
            )]
         ))
            

