#!/usr/bin/env python
# Written by ahmedsajid
# Version 1.1
# 
# This script is triggered as webhook when an issue is approved
# It grabs email address, sends the user email invitiation, adds the user to the appropriate groups, Comments on the issue and closes the issue 

import logging
import os, json
import re
import sys
import requests
from jira import JIRA
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import pycurl, requests
from requests.auth import HTTPBasicAuth

port = 8888
jira_url='https://your.jira.com'
jira_user='adminuser'
jira_pass='password'

header = {
    'Content-Type': 'application/json'
}

groups = {'domain.com' : ['group1','group2']}

project_key = 'PROJECTNAME'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# create a file handler
handler = logging.FileHandler('/opt/webhook/webhook.log')
handler.setLevel(logging.INFO)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)

# Try connecting to JIRA, fail on unable to connect
try:
    jac = JIRA(jira_url,basic_auth=(jira_user, jira_pass))
    del jac
except Exception:
    pass


class WebhookHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        length = self.headers['content-length']
        data = self.rfile.read(int(length))

        # Replace any u' with "
        data = data.replace("u\'", '"')
        # Replace any ' with "
        data = data.replace("\'",'"')

        sys.stdout.write(data)
        # Coverting String into JSON
        json_data = json.loads(data)

        logger.info(json_data)
 
        # Authenticate with JIRA
        jac = JIRA(jira_url,basic_auth=(jira_user, jira_pass))

        if "webhookEvent" in json_data:
            logger.info("webhookEvent")
            if json_data["webhookEvent"] == "user_created":

                email = json_data['user']['emailAddress'].lower()
                email_json = json.dumps({ "emails" : [ "" + email + "" ]})
                # extract domain part from email address
                domain = email.split('@')[1].lower()

                # extract org part from email address
                org = email.split('@')[1].split('.')[0].lower()

                # If user's domain is in working group dictionary
                if domain in working_groups:
                    jira_org_invite_url = jira_url + '/rest/servicedesk/1/pages/people/customers/pagination/' + project_key + '/invite/organisation' 

                    payload = {'query':org}

                    # Search for Organization

                    jira_search_url = jira_url + "/rest/servicedesk/1/pages/people/customers/pagination/" + project_key + "/search"
                    r = requests.get(jira_search_url, auth=(jira_user, jira_pass), params=payload, headers=header)
                    logger.info("Searching for Organization %s", org)
 
                    # If the search returned 200
                    if r.status_code == 200:
                        response = json.loads(r.content)
                        num_of_results = response['total']
                        search_results = response['results']
                        # If search yielded results
                        if num_of_results > 0:
                            for row in search_results:
                                if row['type'] == "Organisation" and row['displayName'].lower() == org:
                                    org_id = row['id']
                                    payload = {'id': org_id}
                                    logger.info("Inviting %s", email)
                                    logger.info("Org_id %s",org_id)
                                    # Invite user and add user to Org
                                    r =  requests.put(jira_org_invite_url, auth=(jira_user, jira_pass), data=email_json, params=payload, headers=header)
                                    logger.info("Invite returned %s", r.status_code)
                                    logger.info("Invite returned %s", r.content)
                    # Add user to groups
                    for group in working_groups[domain]:
                        jac.add_user_to_group(email,group)
                        logger.info("Adding user to group  %s",group)

        elif "transition" in json_data:
            logger.info("transition")

            # Grab issue key
            issue_type = json_data['issue']['fields']['issuetype']['name']
            # Grab project key
            project_key = json_data['issue']['fields']['project']['key']

            # Get Issue Key
            issue_key = json_data['issue']['key']


            # If issue type is Access 
            if issue_type == "Access":

            # Sanity check: If the issue was approved
                if json_data['transition']['transitionName'] == "Approved":

                    # Grab Custom email field
                    email = json_data['issue']['fields']['customfield_10304'].strip().lower()
                    
                    match = re.match("(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)",email)

                    # If email address matches regex
                    if not match == None:

                        # Assign Issue to Admin user so we get email
                        jac.assign_issue(issue_key, jira_user)

                        # Email in json format
                        email_json = json.dumps({ "emails" : [ "" + email + "" ]})

                        # Check if user exists
                        if jac.search_users(email):

                            # Add comment to issue
                            jac.add_comment(issue_key,"User already exists.")

                        else:
                            # Get Organization part from email
                            org = email.split('@')[1].split('.')[0].lower()

                            # build payload with query searching for organization
                            payload = {'query': org}

                            # search under specific project
                            jira_search_url = jira_url + "/rest/servicedesk/1/pages/people/customers/pagination/" + project_key + "/search"
                           
                            # run search 
                            r = requests.get(jira_search_url, auth=(jira_user, jira_pass), params=payload, headers=header)
                            
                            # If the search returned 200, try getting organization id
                            if r.status_code == 200:
                                response = json.loads(r.content)
                                num_of_results = response['total']
                                search_results = response['results']
                                # If search yielded results
                                if num_of_results > 0:
                                    # Loop through list of results
                                    for row in search_results:
                                        # if result type if organization
                                        if row['type'] == "Organisation" and row['displayName'].lower() == org:
                                            org_id = row['id']
                                            payload = {'id': org_id}
                                            jira_org_invite_url = jira_url + '/rest/servicedesk/1/pages/people/customers/pagination/' + project_key + '/invite/organisation'
                                            # Invite user and add user to Org
                                            r =  requests.put(jira_org_invite_url, auth=(jira_user, jira_pass), data=email_json, params=payload, headers=header)
                            else:

                                jira_invite_url = jira_url + '/rest/servicedesk/1/pages/people/customers/pagination/' + project_key + '/invite'

                                # Send invite to user using API
                                r = requests.post(jira_invite_url, auth=(jira_user, jira_pass), data=email_json,headers=header)

                            # If invite was sent OK
                            if r.status_code == 200:

                                # extract domain part from email address
                                domain = email.split('@')[1].lower()

                                # If user's domain is in working group dictionary
                                if domain in working_groups:

                                    # Add user to groups
                                    for group in working_groups[domain]:
                                        jac.add_user_to_group(email,group)
                                        logger.info("Adding user to group %s",group)

                                # Close issue
                                jac.transition_issue(issue_key,"Resolve this issue",fields={"resolution":{"name":"Done"}},comment="Invitation sent to user. Resolving this issue.")

                    else:
                        # Add comment on issue
                        jac.add_comment(issue_key,"The email address is invalid")

                else:
                     # Add comment on issue visibility to Administrators
                     jac.add_comment(issue_key,'Nothing to do', visibility={'type': 'role', 'value': 'Administrators'})
            else:
                # Add comment on issue visibility to Administrators
                jac.add_comment(issue_key,'Issue type is not Access', visibility={'type': 'role', 'value': 'Administrators'})

        self.send_response(200)

server = HTTPServer(('', port), WebhookHandler)
logger.info("serving at port=%s", port)

server.serve_forever()
