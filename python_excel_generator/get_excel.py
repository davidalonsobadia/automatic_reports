from xlwt import easyxf, Workbook
import re
import time

def headerStyle():

	header_style = easyxf(
		'font: name Calibri, bold True, color white, height 280;' # 14 * 20, for 14 point
		'alignment: horizontal center, vertical center;'
		'borders: left thin, right thin, top thin, bottom thin, left_colour white, right_colour white, top_colour white, bottom_colour white;'
    	'pattern: pattern solid, fore_colour dark_blue;'
    )
	
	return header_style

def typeOfData (data):

	if type(data) is float: # is a decimal number
		#print data
		return float("%.2f" % data)

	# elif type(data) is int: #is an integer number
	 	# continue

	# elif type(data) is str and len(data) == 10: # it could be a date
	# 	pattern = re.match(r'\d+-\d+-\d+', data)
	# 	if pattern: # yes, it is a date
	# 		print pattern.group()

	return data

def dataStyle():

	data_style = easyxf(
		'font: name Calibri, height 240;' # 12 * 20, for 12 point
		'alignment: horizontal center, vertical center;'
    	'pattern: pattern solid, fore_colour white;'
    )
		
	return data_style


def get_width(num_characters):
    return int((1+num_characters) * 350) # default 200 = 10 * 20 --> 256 !! 280 --> x  !! x = 280 * 356 / 200

def get_excel(client, data):

	book = Workbook()

	header_style = headerStyle()
	data_style = dataStyle()

	for item in data:
		sheet = book.add_sheet(item)

		sheet.panes_frozen = True
		#sheet.remove_splits = True
		#sheet.vert_split_pos = 1
		sheet.horz_split_pos = 1
				
		data_sheet = data[item]

		num_rows_header = 0
		num_columns_header = 0
		num_rows_total = 0

		if 'header' in data_sheet:
			num_rows_header = data_sheet['header']

		excel_list = []
		if 'rows' in data_sheet:
			excel_list = data_sheet['rows']
				
		for index_row_header in range(num_rows_header):
			row_list = excel_list[index_row_header]
			num_columns_header = len(row_list)
			num_rows_total = len(excel_list)
			
			row_header = sheet.row(index_row_header)
			row_header.height_mismatch = 1
			row_header.height = 500

			for index_col_cell, cell in enumerate (row_list):
	
				row_header.write(index_col_cell, cell, header_style)
				sheet.col(index_col_cell).width = get_width(len(cell))

		for index_row_data in range(len(excel_list) - num_rows_header):
 
			row_data_list = excel_list[index_row_data+num_rows_header]

			row_data = sheet.row(index_row_data+num_rows_header)
			row_data.height_mismatch = 1
			row_data.height = 380

			for index_col_data, data_cell in enumerate (row_data_list):
				# call typeOfData
				#row_data.write(index_col_data, typeOfData(data_cell), data_style)
				row_data.write(index_col_data, typeOfData(data_cell), data_style)

			sheet.flush_row_data()


	excel_filename = time.strftime('%Y-%m-%d')+'_'+client+'_RTB_weekly_report.xls'
	book.save(excel_filename)		

	return excel_filename

