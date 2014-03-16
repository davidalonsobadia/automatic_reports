__author__ = 'David Alonso'
import json
import sys
from pprint import pprint
from rowCostRM import RowCostRM
import csv
import datetime
import random
import urllib
import xmltodict
from get_excel import get_excel


def log(s):
    output = "%s\t%s" %(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), s)
    print output


#Get Python Files
def getCostFile(iFiles, campaignDict, supplierDict, date_start, date_end):
	log("Getting the costs files")
	costsFile = open(iFiles, 'rU')
 
	#Columsn order:
	#date_action, os, device_family, campaign_id, supplier_id, impression, click, install, cost, campaign_group

	# Put in a list of lists
	costsList = [line.rstrip().split('\t') for line in costsFile]

	dictObjects = {}
	
	# R = [ [x, y, str(sum(int(z[2]) for z in g))] for (x, y), g in groupby(sorted(L, key=pair), key=pair) ]
	
	for cost in costsList:

		if cost[0] == 'date_action':
			continue

		
		if cost[1] in ('android', 'ios'):
	
			# COULD BE POSSIBLE THAT THE CAMPAIGN AND/OR SUPPLIER IS NOT IN THE JSON FILE
			# IN THIS CASE, SEND AN EXCEPTION AND CONTINUE
			#### CHANGES IN THIS POINT

			##DONT NEED PREVIOUS IF

			campaignList = campaignDict[cost[3]] # campaign_id

			campaign_name = campaignList[0]
			campaign_device = campaignList[1]

			cost [4] = supplierDict[cost[4]] # supplier_id

			# date_action	os	device_family	campaign_id	supplier_id	impression	click	install	cost	campaign_group
			# 2013-10-14	ios	ipad			11558		58			267			0		0		0.0		Autoscout
			# Object = RowCostRM(cost[0], cost[1], cost[2], cost[3], cost[4], cost[5], cost[6], cost[9] )
			Object = RowCostRM(cost[0], cost[1], campaign_device, cost[3], campaign_name, cost[4], cost[5], cost[6], cost[9])

			if Object.key in dictObjects.keys():
				dictObjects[Object.key].__sumValues__(cost[5], cost[6])				
			else:
				dictObjects[Object.key] = Object

	# Add to the campaigns 0 values (i.e. a day that the campaign was stopped)
	#Get a certain campaign
	campaign_groups = list(set([objectR.campaign_identifier for objectR in dictObjects.values()]))
	campaign_groups.sort()
	
	for campaign_group in campaign_groups:

		d_start = datetime.datetime.strptime(date_start, '%Y-%m-%d').date()
		d_end   = datetime.datetime.strptime(date_end,   '%Y-%m-%d').date()
		while d_start <= d_end:

			# Change from Y-m-d to m/d/Y
			# date_converted = datetime.datetime.strptime(str(d_start), '%Y-%m-%d')
			# date_converted_zeros = '{0}/{1}/{2:02}'.format(date_converted.month, date_converted.day, date_converted.year % 100)

			# loop_key = date_converted_zeros+campaign_group
			loop_key = str(d_start)+campaign_group

			if loop_key not in dictObjects.keys():

				#coger llaves del dict
				list_keys = dictObjects.keys()
				#seleccionar una llave que coincida con campaign_group
				reference_key = ''
				for key in list_keys:
					if key.endswith(campaign_group) and reference_key == '':
						reference_key = key
					
				#extraer el objeto
				reference_object = dictObjects[reference_key]

				#usar ese objeto como referencia para rellenar el resto
				# date_action	os	device_family	campaign_id	supplier_id	impression	click	install	cost	campaign_group
				# 2013-10-14	ios	ipad			11558		58			267			0		0		0.0		Autoscout
				Object = RowCostRM(str(d_start), reference_object.os, reference_object.device_family,
					reference_object.campaign_id, reference_object.campaign_name, reference_object.supplier_id, 0, 0, reference_object.campaign_group )

				dictObjects[Object.key] = Object

			d_start = d_start + datetime.timedelta(days=1)

	return dictObjects

def getCustomAction(iFiles, costDict, campaignDict, supplierDict, custom_action_rules):
	log("Getting the custom actions")
	ca_File = open(iFiles, 'rU')

	# Put in a list of lists
	caList = [line.rstrip().split('\t') for line in ca_File]

	# firstTimeSeen	custom_action	campaign_id	supplier_id	os	device_family	num_users	num_events	campaign_group
	# 2013-10-14	a_opening		11558		297			i	ipad			1			2			Autoscout
	for ca in caList:
		if ca[0] == 'firstTimeSeen':
			continue
		
		# Get special rules
		custom_action_rules_keys = custom_action_rules.keys()
		custom_action_rule = [rule for rule in custom_action_rules_keys if rule in ca[1].lower()]


		# Get the dictionary IF exists
		if custom_action_rule:
			# Fulfill the rules for these custom_actions. Normally, what I would do is to 
			# check if every custom_action has the key word or key words that the value of the dictionary has.
			# Custom actions in config file are written as "key pattern": "Custom_action"

			# custom action and input custom action from config.json file are equal:

			## WARNING. THAT MEANS THAT EACH CUSTOM_ACTION_NAME CAN MATCH WITH ONE CUSTOM_ACTION_RULE
			#Exception

			if len(custom_action_rule) != 1:
				log('Exception: confusion with custom action names')
				continue
			elif custom_action_rule[0].lower() == ca[1].lower():
				ca[1] = custom_action_rules[custom_action_rule[0]]
			#ca[1] = ''.join(custom_action_rules[c] for c in custom_action_rule)
			else:
				ca[1] = custom_action_rules[custom_action_rule[0]]

		# HERE SOME CHANGES TO TODO:
		# ca[2] = campaignDict[ca[2]] # campaign_id
		ca[3] = supplierDict[ca[3]] # supplier_id

		# change a for 'android' for device family parameter
		if ca[5] == 'a':
			ca[5] = 'android'
		# Key of costs -- self.key = da+os+df+ci+si+cg
		ca_key = ca[0]+ca[4]+ca[2]+ca[3]+ca[8]
		#ca_key = ca[0]+ca[4]+ca[2]+ca[3]+ca[8]
		# Key checks perfectly
		if ca_key in costDict.keys():

			## FIRST OF ALL CHECK IF this CA is a new One
			# If it is, put this custom action to all the people in costDict
			if ',' in ca[1]:
				custom_action_splits = [cas.strip() for cas in ca[1].split(',')]
				custom_action_num_users = custom_action_splits[1]
				custom_action_num_events = custom_action_splits[0]
				#custom_action_num_users = ca[0]
				#custom_action_num_events = ca[1]
				print custom_action_num_users
				print custom_action_num_events
				if custom_action_num_users not in costDict[ca_key].custom_actions.keys():
					for key in costDict.keys():
						costDict[key].__addCustomAction__(custom_action_num_users, 0)
				if custom_action_num_events not in costDict[ca_key].custom_actions.keys():
					for key in costDict.keys():
						costDict[key].__addCustomAction__(custom_action_num_events, 0)

				costDict[ca_key].__addCustomAction__(custom_action_num_users, int(ca[6]))
				costDict[ca_key].__addCustomAction__(custom_action_num_events, int(ca[7]))

			else:
				if ca[1] not in costDict[ca_key].custom_actions.keys():
					for key in costDict.keys():
						# c = [custom_action_subname.strip() for custom_action_subname in custom_action_name.split(',')]
						costDict[key].__addCustomAction__(ca[1], 0)
				
				costDict[ca_key].__addCustomAction__(ca[1], int(ca[7]))

		else:
			log('EXCEPTION: A custom action not linked to a cost: %s' % ca_key)
	return costDict

def getDictCurrencies():
	url = 'http://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90d.xml'
	log("Getting the currencies from ECB -- %s" % (url))
	#last 90 days

	xml = urllib.urlopen(url).read()
	dict_xml = xmltodict.parse(xml)
	currencies_days = dict_xml['gesmes:Envelope']['Cube']['Cube']
	
	return currencies_days

def getFinalCosts(dictObjects, cpc_config):
	log("Calculating final costs")
	# REMEMBER JUST 90 DAYS
	# IMPROVE THE PERFORMANCE
	
	initial_currency = cpc_config['initial_currency']
	final_currency = cpc_config['final_currency']

	#cpc_net = float(cpc_config['CPC Net'])
	#margin = float(cpc_config['Margin'])
	cpc_net = 0.0
	margin = 0.0

	currencies_days = getDictCurrencies()
	days = [datetime.datetime.strptime(t['@time'], '%Y-%m-%d').date() for t in currencies_days]
	oldest_day = min(days)
	
	for d in dictObjects:

		# Before to check the currencies, we might the wich cpc corresponds to this campaign (if there is more than one)
		# Best way: check if IDs parameter exists.
		if 'IDs' in cpc_config:
			cpc_net, margin = check_CPC_json(dictObjects[d].campaign_id, cpc_config)

		else:
			cpc_net = float(cpc_config['CPC Net'])
			margin = float(cpc_config['Margin'])

		# Initial and final currency are the same
		if initial_currency == final_currency :

			dictObjects[d].__Costs__(cpc_net, margin)

		#Initial and final currency are different
		# Initial currency are EUR
		elif initial_currency == 'EUR':

			try:
				date_object = datetime.datetime.strptime(dictObjects[d].date_action, '%m/%d/%y').date()
			except:
				try:
					date_object = datetime.datetime.strptime(dictObjects[d].date_action, '%Y-%m-%d').date()
				except:
					log('Error getting date from the custom action %s' % (dictObjects[d].key))
					continue
			# It's Saturday or Sunday, go to Friday
			while date_object not in days:
				date_object = date_object - datetime.timedelta(days=1)
				# IF date_object is out of range...
				if date_object < oldest_day:
					date_object = oldest_day
					break

			currencies_day = [cube_day['Cube'] for cube_day in currencies_days if str(date_object) in cube_day['@time']][0]
			rate = [currency['@rate'] for currency in currencies_day if str(final_currency) in currency['@currency']][0]

			dictObjects[d].__Costs__(cpc_net, float(margin), float(rate))



		# Initial and final currency are different
		# Initial currency are different as EUR
		else:
			# Example
			# GBP to EUR to USD --> rate = x 	--> EUR x rate = GBP --> GBP / rate = EUR
			#																	| --> EUR x rate = USD

			# NOT TESTED UNTIL WE NEED IT

			date_object = datetime.datetime.strptime(dictObjects[d].date_action, '%m/%d/%y').date()

			# It's Saturday or Sunday, go to Friday
			while date_object not in days:
				date_object = date_object - datetime.timedelta(days=1)
				# IF date_object is out fo range...
				if date_object < oldest_day:
					date_object = oldest_day
					break

			currencies_day = [cube_day['Cube'] for cube_day in currencies_days if str(date_object) in cube_day['@time']][0]
			rate1 = [currency['@rate'] for currency in currencies_day if str(initial_currency) in currency['@currency']][0]
			rate2 = [currency['@rate'] for currency in currencies_day if str(final_currency) in currency['@currency']][0]

			dictObjects[d].__Costs__(cpc_net, float(margin), float(rate1), float(rate2))

	return dictObjects

def check_CPC_json(campaign_id, cpc_dict):
	# LOOK HERE!!
	# INPUT: campaign_id, campaign_dict (always the same, so it shouldn't be a direct input)

	# try
	try:

		# Check lenght of ID value
		len_ids = len(cpc_dict['IDs'])

		# Check if ID lengh matches with Margin and CPC NET length
		if (len_ids == len(cpc_dict['CPC Net']) and len_ids == len(cpc_dict['Margin'])):

			# Make the next loop: for each id in the same array position (first split ids in the same array position)
			for index, c in enumerate(cpc_dict['IDs']):
				if campaign_id in c:
					# put the CPC Net and the margin corresponding to the same array position
					cpc_net = cpc_dict['CPC Net'][index]
					margin = cpc_dict['Margin'][index]
					return float(cpc_net), float(margin)


			return 0.0, 0.0

		else:
			log('Wrong CPC Json Dict. Check with David how to build it')

	# JSON ERROR Construction exception
	except IOError, e:
		log('Wrong CPC Json Dict. Wrong built-in')
		log(e)


	# It should have to return the right cpc_net and margin



def makeFile(dictObjects, initial_currency, final_currency, file_name):


	log("Generating output file")
	# Sort dict

	#Get a certain campaign
	campaign_groups = list(set([objectR.campaign_identifier for objectR in dictObjects.values()]))
	campaign_groups.sort()

	row_lists = []

	todays_date = datetime.datetime.now().strftime('%Y-%m-%d')

	with open(todays_date+'_'+file_name+'_weekly_report.csv', 'wb') as fp:
		writer = csv.writer(fp, delimiter=',')

		header = []
		# ID values
		header.extend(['App', 'Date', 'Month', 'CW', 'Platform', 'Campaign name', 'Source'])
		# Costs
		#check if initial and final currency are the same
		if initial_currency == final_currency:
					header.extend(['Cost Net ' +  initial_currency, 'CPC Net ' + initial_currency, 'Cost Gross ' + initial_currency])
		else:
			header.extend(['Cost Net ' +  initial_currency, 'CPC Net ' + initial_currency, 'Cost Gross ' + initial_currency])
			header.extend([initial_currency+'/'+final_currency])
			header.extend(['Cost Net ' + final_currency, 'CPC Net ' + final_currency, 'Cost Gross ' + final_currency])
		# Impressions, clicks, installs
		header.extend(['Impressions', 'Clicks', 'Installs'])

		# Conversion rate (CR %)
		header.extend(['CR %'])

		# Get custom_actions from a dict
		random_key = random.choice(dictObjects.keys())

		# Get names of custom_actions
		custom_action_names=  dictObjects[random_key].custom_actions.keys()
		# custom_action_names = []
		# for custom_action_name in custom_action_names_basic:
		# 	if ',' in custom_action_name:
		# 		c = [custom_action_subname.strip() for custom_action_subname in custom_action_name.split(',')]
		# 		# custom_actions_names_extended.append()
		# 		custom_action_names.extend(c)
		# 	else:
		# 		custom_action_names.append(custom_action_name)

		# custom_action_names = [custom_action_name for custom_action_name in custom_action_names if custom_action_name.lower() != 'reopening' else custom_action_names.extend['Unique reopeners', custom_action_name]]
		# get other value called 'Unique reopeners'
		# for i in range(len(custom_action_names)):
		# 	if 'reopening' in custom_action_names[i]:
		# 		custom_action_names.extend([custom_action_names[i], 'Unique reopeners'])
		# 		del custom_action_names[i]


		custom_action_names.sort()

		header.extend(custom_action_names)
		row_lists.append(header)
		#OLD FILE
		writer.writerow(header)
	
		for campaign_group in campaign_groups:
			##GET THE CUSTOM_ACTIONS

			## print the header
			## print the custom actions coincidiendo header con custom_action
			campaign_group_keys = [objectR.key for objectR in dictObjects.values() if objectR.campaign_identifier == campaign_group]
			campaign_group_keys.sort()

			for key in campaign_group_keys:

				# self.date_action = da			# date_action
				# if os == 'ios':
				# 	self.os = 'i' 
				# elif os == 'android':
				# 	self.os = 'a' 
				# else: self.os = os 				# operating system
				# self.device_family = df			# device_family
				# self.campaign_id = ci			# campaign_id
				# self.supplier_id = si
				# self.campaign_group = cg		# campaign group
				# self.key = da+self.os+df+ci+si+cg

				custom_action_num_events = []
				for custom_action in custom_action_names:
					#Reopenings exception:
					# if 'reopening' in custom_action.lower():
						# print dictObjects[key].custom_actions[custom_action][0]
						# print dictObjects[key].custom_actions[custom_action][1]
					# if ',' in custom_action:
					#  	c = [custom_action_subname.strip() for custom_action_subname in custom_action_name.split(',')]
					#  	custom_action_num_events.append(dictObjects[key].custom_actions[custom_action][1])
					#  	custom_action_num_events.append(dictObjects[key].custom_actions[custom_action][0])

					# else:
					custom_action_num_events.append(dictObjects[key].custom_actions[custom_action])

		 		#KEY -- IN A LIST
		 		row_list = [dictObjects[key].campaign_group, dictObjects[key].date_action, dictObjects[key].month, dictObjects[key].cw,
		 			dictObjects[key].device_family, dictObjects[key].campaign_name, dictObjects[key].supplier_id]
		 		
		 		# VALUES of COST
		 		if initial_currency == final_currency:
		 			row_list.extend([dictObjects[key].cost_net_initial_currency, dictObjects[key].cpc_net_initial_currency,
				 		dictObjects[key].cost_gross_initial_currency])
		 		else:
			 		row_list.extend([dictObjects[key].cost_net_initial_currency, dictObjects[key].cpc_net_initial_currency,
			 			dictObjects[key].cost_gross_initial_currency, dictObjects[key].rate, 
			 			dictObjects[key].cost_net_final_currency, dictObjects[key].cpc_net_final_currency, dictObjects[key].cost_gross_final_currency])

		 		#VALUES of IMPRESSIONS, CLICKS and INSTALLS
		 		row_list.extend([dictObjects[key].impressions, dictObjects[key].clicks, dictObjects[key].installs])

		 		#VALUES of conversion rate CR
		 		row_list.extend([dictObjects[key].__getKPIs__('CR')])

		 		#VALUES of custom actions 
		 		row_list.extend(custom_action_num_events)

		 		row_lists.append(row_list)
		 		#OLD FILE
		 		writer.writerow(row_list)


	fp.close()
	return row_lists

#Get all the necesarry inputs
def weekly_report(client, config_file, dict_files):

	#Get python config files
	json_config	=	open(config_file)
	config 		=	json.load(json_config)

	#Get config variables
	start = config['date_start']
	end = config['date_end']


	#Check from files
	if dict_files:

		log('Using the next files for the report: %s' % ', '.join(file_name for file_name in dict_files.values()))
		campaigns = config['campaigns'] 
		suppliers = config['suppliers']

		if 'custom_actions' in config:
			custom_actions = config['custom_actions']
		else:
			custom_actions = {}

		#path= '../'
		path = ''
		costs = dict_files['cost']
		
		cpc = config['CPC']

		original_costs = getCostFile(path+costs, campaigns, suppliers, start, end)

		excel_data = {}

		if 'rm' in dict_files:
			log('Remarketing')
			rm = dict_files['rm']
			# JUST ONE PARAMETER HERE in campaigns_rm
			campaigns_rm = config['campaigns_rm'].keys()[0]
			rm_costs = dict((cost, original_costs[cost]) for cost in original_costs if original_costs[cost].campaign_group == campaigns_rm)
			rm_custom_actions_costs = getCustomAction(path+rm, rm_costs, campaigns, suppliers, custom_actions)
			rm_custom_actions_costs_final_costs = getFinalCosts(rm_custom_actions_costs, cpc)
			rows = makeFile(rm_custom_actions_costs_final_costs, cpc['initial_currency'], cpc['final_currency'], campaigns_rm)
			excel_data[campaigns_rm] = {'header' : 1, 'rows' : rows}


		if 'at' in dict_files:
			log('Audience Targeting')
			at = dict_files['at']
			campaigns_at = config['campaigns_at'].keys()[0]
			at_costs = dict((cost, original_costs[cost]) for cost in original_costs if original_costs[cost].campaign_group == campaigns_at)
			at_custom_actions_costs = getCustomAction(path+at, at_costs, campaigns, suppliers, custom_actions)
			at_custom_action_costs_final_costs = getFinalCosts(at_custom_actions_costs, cpc)
			rows = makeFile(at_custom_action_costs_final_costs, cpc['initial_currency'], cpc['final_currency'], campaigns_at)
			excel_data[campaigns_at] = {'header' : 1, 'rows' : rows}

		excel_filename = get_excel(client, excel_data)
		log('Done! gl & hf!')
		return excel_filename
	else:
		log('Not files found. Please check the script or go in touch with David.')
		sys.exit()


