import sys
import os
import time
import re
sys.path.insert(0, './python_excel_generator')

from get_weekly_report import weekly_report, log


def main():
	# Check if we have all the inputs

	#FIRST: check number of arguments and if they are right
	if len(sys.argv) != 2:
		log('Wrong number of arguments. Please write the command in the right way (i.e. python main_weekly_report.py autoscout')
		sys.exit()

	# Now check if this arg matches with one of our clients looking at the json files
	client = sys.argv[1].lower() 
	#SECOND: input json file (config_XXXXXXX.json)
	config_file_path = 'config/config_'+client+'.json'
	config_file = ''
	dict_files = {}
	files_sent = False
	destination_excel = 'excel/'

	if os.path.isfile(config_file_path):
		#here we get the right config.json file
		config_file = config_file_path
	else:
		log('Wrong argument %s. Please write the command in the right way (i.e. python main_weekly_report.py autoscout' % client)
		sys.exit()

	file_list = [file_name for file_name in os.listdir('.') if os.path.isfile(file_name)]
	

	client_files = [item for item in file_list if re.search(r'\d{4}-\d{2}-\d{2}_%s' % client, item, re.IGNORECASE)]

	#check the newest cost file
	cost_files = [item for item in client_files if re.search(r'\d{4}-\d{2}-\d{2}_%s_costs' % client, item, re.IGNORECASE)]
	cost_files.sort(reverse=True)

	book = ''

	for cost_file in cost_files:
		for f in client_files:
			if not files_sent:
				basic_filename = cost_file[:-6]
				if basic_filename+"_remarketing_custom_actions" == f:
					# Here we have a cost file and a remarketing file with same date. we can do the excel
					# First of all check if we also have the audience targeting custom actions
					dict_files['cost'] = cost_file
					dict_files['rm'] = f
					files_sent = True

					for f2 in client_files:
						if basic_filename+"_audience_targeting_custom_actions" == f2:
							# we have both. we can go to the excel file
							# GO TO EXCEL FILE
							dict_files['at'] = f2
							book = weekly_report(client, config_file, dict_files)
					
					# HERE WE HAVE JUST REMARKETING
					# GO TO EXCEL FILE
					book = weekly_report(client, config_file, dict_files)

				elif basic_filename+"_audience_targeting_custom_actions" == f:
					# HERE WE HAVE AUDIENCE TARGETING CAMPAIGNS
					dict_files['cost'] = cost_file
					dict_files['at'] = f
					files_sent = True

					for f2 in client_files:
						if basic_filename+"_remarketing_custom_actions" == f2:
							# we have both. we can go to the excel file
							dict_files['rm'] = f2
							# GO TO EXCEL FILE
							book = weekly_report(client, config_file, dict_files)
					# HERE WE HAVE JUST AUDIENCE TARGETING
					# GO TO EXCEL FILE
					book = weekly_report(client, config_file, dict_files)

	# If we ahave arrived here, it is because we have no remarketing and/or audience targeting file associated to any cost file
	if len(cost_files) == 0 and book == '':
		log('No files found for %s. Please check again the input files' % client)
		sys.exit()

	os.rename(book, destination_excel+book)






if __name__ == '__main__':
	main()