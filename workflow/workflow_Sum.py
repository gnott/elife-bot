import boto.swf
from boto.swf.layer1_decisions import Layer1Decisions
import json
import random
import datetime

import workflow

"""
Sum workflow
"""

class workflow_Sum(workflow.workflow):
	
	def __init__(self, settings, logger, conn = None, token = None, decision = None, maximum_page_size = 100, definition = None):
		self.settings = settings
		self.logger = logger
		self.conn = conn
		self.token = token
		self.decision = decision
		self.maximum_page_size = maximum_page_size
		
		# JSON format workflow definition, for now
		workflow_definition = {
			"name": "Sum",
			"version": "1",
			"task_list": self.settings.default_task_list,
			"input": {"data": [1,3,7,11]},
	
			"start":
			{
				"requirements": None
			},
			
			"steps":
			[
				{
					"step1": {
						"activity_type": "PingWorker",
						"activity_id": "PingWorker",
						"version": "1",
						"input": None,
						"control": None,
						"heartbeat_timeout": 300,
						"schedule_to_close_timeout": 300,
						"schedule_to_start_timeout": 300,
						"start_to_close_timeout": 300
					}
				},
				{
					"step2a": {
						"activity_type": "Sum",
						"activity_id": "Sum2a",
						"version": "1",
						"input": {"data": [1,3,7,11]},
						"control": None,
						"heartbeat_timeout": 300,
						"schedule_to_close_timeout": 300,
						"schedule_to_start_timeout": 300,
						"start_to_close_timeout": 300
					}
				}
			],
		
			"finish":
			{
				"requirements": None
			}
		}
		
		self.load_definition(workflow_definition)
		

	def do_workflow(self, data = None):
		"""
		Make decisions and process the workflow accordingly
		"""
		
		# Quick test for nextPageToken
		self.handle_nextPageToken()

		# Schedule an activity
		if(self.token != None):
			# 1. Check if the workflow is completed
			if(self.is_workflow_complete()):
				# Complete the workflow execution
				self.complete_workflow()
			else:
				# 2. Get the next activity
				next_activities = self.get_next_activities()
				d = None
				for activity in next_activities:
					# Schedule each activity
					d = self.schedule_activity(activity, d)
				self.complete_decision(d)
				
		return True