#!/usr/bin/python
import datetime

class RowCostRM:

	def __init__(self, da, os, df, ci, cn, si, imp, cl, cg):

		# date_action	os	device_family	campaign_id	supplier_id	impression	click	install	cost	campaign_group
		# 2013-10-14	ios	ipad	11558	58	267	0	0	0.0	Autoscout

		self.date_action = da			# date_action
		if os == 'ios':
			self.os = 'i' 
		elif os == 'android':
			self.os = 'a' 
		else: self.os = os 				# operating system
		if df == 'ipod':
			self.device_family = 'iphone'
		elif df == 'a':
			self.device_family = 'android'
		else:
			self.device_family = df		# device_family
		self.campaign_id = ci			# campaign_id
		self.campaign_name = cn 		# campaign_name
		self.supplier_id = si 			# supplier_id
		self.campaign_group = cg		# campaign group

		date_time_format = datetime.datetime.strptime(self.date_action, '%Y-%m-%d').date() 
		self.month = date_time_format.month				# month number
		self.cw = date_time_format.isocalendar()[1]		# week number

		# self.key = self.date_action+self.os+self.device_family+self.campaign_id+self.supplier_id+self.campaign_group # key
		self.key = self.date_action+self.os+self.campaign_id+self.supplier_id+self.campaign_group # key

		# self.campaign_identifier = self.os+self.device_family+self.campaign_id+self.supplier_id+self.campaign_group #campaign group identifier
		self.campaign_identifier = self.os+self.campaign_id+self.supplier_id+self.campaign_group #campaign group identifier

		self.impressions = int(imp)
		self.clicks = int(cl)
		self.installs = 0 # made with a_openings custom_actions

		self.custom_actions = {} # custom actions that we will have per each Object


	def __sumValues__(self, impressions, clicks):

		self.impressions += int(impressions)
		self.clicks += int(clicks)


	# ADD CUSTOM ACTION
	def __addCustomAction__(self, ca_name, num_events, *num_users):
		# firstTimeSeen	custom_action	campaign_id	supplier_id	os	device_family	num_users	num_events	campaign_group
		# 2013-10-14	a_opening	11558	297	i	ipad	1	2	Autoscout
		# Openings exception
		if ca_name == 'a_opening' or ca_name == '01_Installs':
			self.installs += num_events

		elif ca_name in self.custom_actions.keys():
			#n_users_prev = self.custom_actions[ca_name][0]
			n_events_prev = self.custom_actions[ca_name]
			#n_users_new = num_users + n_users_prev
			n_events_new = num_events + n_events_prev

			self.custom_actions[ca_name] = n_events_new

		else:
			self.custom_actions[ca_name] = num_events


	def __Costs__(self, cpc_net, margin, *rate):

		#
		# Costs that we need for the weekly report (net and gross):
		# 
		#	- CPC
		#	- Cost
		#	- CPI
		# 		- In overall, 3x2 = 6 values --> if we have 2 currencies, 12 values 
		#

		# costNet = CPC_net * clicks
		# costGross = costNet * (1 + margin)

		#initial currency
		self.cost_net_initial_currency = cpc_net * self.clicks
		self.cost_gross_initial_currency = self.cost_net_initial_currency * (1 + margin)
		#cpc
		if self.clicks == 0:
			self.cpc_net_initial_currency = 0
			self.cpc_gross_initial_currency = 0
		else:
			self.cpc_net_initial_currency = cpc_net
			self.cpc_gross_initial_currency = cpc_net * (1 + margin)
		#cpi
		if self.installs == 0:
			self.cpi_net_initial_currency = 0
			self.cpi_gross_initial_currency = 0
		else:
			self.cpi_net_initial_currency = self.cost_net_initial_currency / self.installs
			self.cpi_gross_initial_currency = self.cpi_net_initial_currency * (1 + margin)

		# check if we have more than one currency
		if len(rate) == 1:
			# other_args = rate
			self.rate = rate[0]
			self.cost_net_final_currency = self.cost_net_initial_currency * self.rate
			self.cost_gross_final_currency = self.cost_gross_initial_currency * self.rate
			self.cpc_net_final_currency = self.cpc_net_initial_currency * self.rate
			self.cpc_gross_final_currency = self.cpc_gross_initial_currency * self.rate
			self.cpi_net_final_currency = self.cpi_net_initial_currency * self.rate
			self.cpi_gross_final_currency = self.cpi_gross_initial_currency * self.rate

		elif len(rate) == 2:

			# Example
			# GBP to EUR to USD --> rate = x 	--> EUR x rate = GBP --> GBP / rate = EUR
			#																	| --> EUR x rate = USD
			rate1 = rate[0]
			rate2 = rate[1]
			self.rate = rate2 / rate1

			self.cost_net_final_currency = self.cost_net_initial_currency / rate1 * rate2
			self.cost_gross_final_currency = self.cost_gross_intial_currency / rate1 * rate2
			self.cpc_net_final_currency = self.cpc_net_initial_currency / rate1 * rate2
			self.cpc_gross_final_currency = self.cpc_gross_initial_currency / rate1 * rate2
			self.cpi_net_final_currency = self.cpi_net_initial_currency / rate1 * rate2
			self.cpi_gross_final_currency = self.cpi_gross_initial_currency / rate1 * rate2

		#no rate --> same currency at the beginning
		else:
			self.cost_net_final_currency = self.cost_net_initial_currency
			self.cost_gross_final_currency = self.cost_gross_initial_currency
			self.cpc_net_final_currency = self.cpc_net_initial_currency
			self.cpc_gross_final_currency = self.cpc_gross_initial_currency
			self.cpi_net_final_currency = self.cpi_net_initial_currency 
			self.cpi_gross_final_currency = self.cpi_gross_initial_currency 

	def __getKPIs__(self, kpi):

		if kpi == 'CTR':
			#CTR = self.clicks / self.impressions

			return 0.00 if self.impressions == 0 else float(self.clicks) / float(self.impressions) * 100.00
			# if self.impressions == 0:
			# 	return 0.00
			# return float(self.clicks / self.impressions) * 100.00 # It is a percentage
		elif kpi == 'CR':
			#CR = self.installs / self.impressions
			return 0.00 if self.clicks == 0 else float(self.installs) / float(self.clicks) * 100.00
			# if self.clicks == 0:
			# 	return 0.00
			# return float(self.installs / self.clicks) * 100.00 # It is a percentage
		
		return 0.00


