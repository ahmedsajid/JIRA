# JIRA

Repository for JIRA related stuff

'''webhook.py''' is python script runs as a webserver on a port and accepts json data and does the following
- If triggered by approving access request type in JSD, invite the user to project and resolve the ticket
- If triggered manually inviting customers, add the customers to appropriate groups & organizations. 

Webhook needs to be defined in JSD: https://developer.atlassian.com/jiradev/jira-apis/webhooks

This solves the following feature requests.

https://jira.atlassian.com/browse/JSDSERVER-4519

https://jira.atlassian.com/browse/JSDSERVER-2073
