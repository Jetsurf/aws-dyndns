import boto3
import requests
import argparse
import os

os.environ['AWS_PROFILE'] = "ddns"

class AWSDynDns(object):
    def __init__(self, region, domain, subdomain, hosted_zone_id):
        self.ip_service = "http://httpbin.org/ip"
        self.client = boto3.client('route53')
        self.domain = domain
        self.subdomain = subdomain
        self.hosted_zone_id = hosted_zone_id
        if self.subdomain:
            self.fqdn = "{0}.{1}".format(self.subdomain, self.domain)
        else:
            self.fqdn = self.domain

    def get_external_ip(self):
        try:
            self.external_ip_request = requests.get(self.ip_service)
            self.external_ip = self.external_ip_request.json()['origin']
            print("Found external IP: {0}".format(self.external_ip))
        except Exception:
            raise Exception("error getting external IP")

    def check_existing_record(self):
        """ Get current external IP address """
        self.get_external_ip()

        """ Check for existing record and if it needs to be modified """
        response = self.client.list_resource_record_sets(
            HostedZoneId=self.hosted_zone_id,
            StartRecordName=self.fqdn,
            StartRecordType='A',
        )

        found_flag = False

        if len(response['ResourceRecordSets']) == 0:
            raise Exception("Could not find any records matching domain: {0}".format(self.fqdn))

        if self.fqdn in response['ResourceRecordSets'][0]['Name']:
            for ip in response['ResourceRecordSets'][0]['ResourceRecords']:
                if self.external_ip == ip['Value']:
                    found_flag = True
        else:
            raise Exception("Cannot find record set for domain: {0}".format(self.fqdn))

        return found_flag

    def update_record(self):
        if self.check_existing_record():
             print("IP is already up to date")
        else:
            response = self.client.change_resource_record_sets(
                HostedZoneId=self.hosted_zone_id,
                ChangeBatch={
                    'Comment': 'string',
                    'Changes': [
                        {
                            'Action': 'UPSERT',
                            'ResourceRecordSet': {
                                'Name': self.fqdn,
                                'Type': 'A',
                                'TTL': 123,
                                'ResourceRecords': [
                                    {
                                        'Value': self.external_ip
                                    },
                                ],
                            }
                        },
                    ]
                }
            )
            print(response)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage a dynamic home IP address with an AWS hosted route53 domain")

    parser.add_argument(
        "--region", "-r",
        default="us-east-1",
        help="AWS region to connect to",
        required=False
    )

    parser.add_argument(
        "--domain", "-d",
        default="robertellegate.com",
        help="Domain to modify",
        required=False
    )

    parser.add_argument(
        "--subdomain", "-s",
        default="surface",
        help="Subdomain to modify",
        required=False
    )

    parser.add_argument(
        "--zone", "-z",
        default="Z31IS2RBRR7PFA",
        help="AWS hosted zone id",
        required=False
    )

    args = parser.parse_args()

    run = AWSDynDns(args.region, args.domain, args.subdomain, args.zone)
    run.update_record()
