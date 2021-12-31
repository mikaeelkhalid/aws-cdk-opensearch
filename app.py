#!/usr/bin/env python3

from aws_cdk import core

from opensearch.opensearch_stack import OpensearchStack


app = core.App()
OpensearchStack(app, "opensearch")

app.synth()
