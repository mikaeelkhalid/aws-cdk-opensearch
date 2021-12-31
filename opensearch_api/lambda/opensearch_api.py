import boto3
import json
import requests
from requests_aws4auth import AWS4Auth
import datetime
from dateutil.relativedelta import relativedelta
import os

region = 'us-east-1'
service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

domain_endpoint = os.environ['DOMAIN_ENDPOINT']
cdk_role_arn = os.environ['CDK_ROLE_ARN']
opensearch_api_role_arn = os.environ["OPENSEARCH_API_ROLE"]

backend_role_arns = [cdk_role_arn, opensearch_api_role_arn]

os_api_endpoint_all_access = "_plugins/_security/api/rolesmapping/all_access"

os_api_endpoint_security_manager = "_plugins/_security/api/rolesmapping/security_manager"

os_api_create_index = "speed"

host_url = "https://" + domain_endpoint + "/" 

headers = { "Content-Type": "application/json" }

def  create_role_mapping(endpoint):
        
    query = {
          "backend_roles" : backend_role_arns,
          "hosts" : [ ],
          "users" : ["master"],
        }
    
    r = requests.put(host_url + endpoint , auth=awsauth, headers=headers,  data=json.dumps(query))
    response = {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": '*'
        },
        "isBase64Encoded": False
    }

    response['body'] = r.text

    return response

def create_index():

    query = { 
    "aliases": {},
    "mappings": {
      "properties": {
        "@timestamp": { 
            "type": "alias",
            "path": "Timestamp"
        }, 
        "Device_Name": {
          "type": "text",
          "fields": {
            "keyword": {
              "type": "keyword",
              "ignore_above": 256
            }
          }
        },
        "Device_Status": {
          "type": "long"
        },
        "OUT1": {
          "type": "long"
        },
        "OUT2": {
          "type": "long"
        },
        "PDV1": {
          "type": "float"
        },
        "Sensor_ID": {
          "type": "text",
          "fields": {
            "keyword": {
              "type": "keyword",
              "ignore_above": 256
            }
          }
        },
        "Sensor_Loc_ID": {
          "type": "long"
        },
        "Sensor_Type": {
          "type": "text",
          "fields": {
            "keyword": {
              "type": "keyword",
              "ignore_above": 256
            }
          }
        },
        "Sensor_Type_Name": {
          "type": "text",
          "fields": {
            "keyword": {
              "type": "keyword",
              "ignore_above": 256
            }
          }
        },
        "Target": {
          "type": "long"
        },
        "Timestamp": {
          "type": "date",
           "format": "strict_date_optional_time||epoch_second"
        },
        "Unit": {
          "type": "text",
          "fields": {
            "keyword": {
              "type": "keyword",
              "ignore_above": 256
            }
          }
        }
      }
    },
    "settings": {
      "index": {
        "number_of_shards": "5",
        "number_of_replicas": "1",
      }
    }
    }

    r = requests.put(host_url + os_api_create_index , auth=awsauth, headers=headers,  data=json.dumps(query))
    response = {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": '*'
        },
        "isBase64Encoded": False
    }

    response['body'] = r.text

    return response
            

def lambda_handler(event, context):
    
    # role_mapping_access_res = create_role_mapping(os_api_endpoint_all_access)
    # role_mapping_security_res = create_role_mapping(os_api_endpoint_security_manager)
    
    # print ({
    #    "role_mapping_access_res": role_mapping_access_res,
    #    "role_mapping_security_res": role_mapping_security_res
    # })

    index_res = create_index()

    print ({
        "index_res": index_res
    })
