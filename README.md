# JIRA

Repository for JIRA related stuff

### webhook.py 
webhook.py is python script runs as a webserver on a port and accepts json data and does the following
- If triggered by approving access request type in JSD, invite the user to project and resolve the ticket
- If triggered manually inviting customers, add the customers to appropriate groups & organizations. 

_Requirement_
Python library for interacting with JIRA via REST APIs. https://pypi.python.org/pypi/jira/

Webhook needs to be defined in JSD: https://developer.atlassian.com/jiradev/jira-apis/webhooks
Also see defining webhook as a post function to workflow: https://developer.atlassian.com/jiradev/jira-apis/webhooks#Webhooks-Addingawebhookasapostfunctiontoaworkflow

This solves the following feature requests.
1. https://jira.atlassian.com/browse/JSDSERVER-4519
2. https://jira.atlassian.com/browse/JSDSERVER-2073

This by no means is perfect. Any changes and improvements are welcome.
