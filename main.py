from panjiva import *
from parser import *

if __name__ == "__main__":
	files = [f for f in os.listdir('.') if os.path.isfile(f)]
	for file in files:
	    if file.endswith('csv') and 'China_Exports' in file:
	        china_exports_file = file
	    if file.endswith('csv') and 'US_Imports' in file:
	        us_imports_file = file

	china_exports = pd.read_csv(china_exports_file, low_memory=False)
	us_imports = pd.read_csv(us_imports_file, low_memory=False)
	# add year column
	china_exports['year'] = pd.DatetimeIndex(china_exports['Shipment Month']).year
	us_imports['year'] = pd.DatetimeIndex(us_imports['Arrival Date']).year
	# add month column
	china_exports['month'] = china_exports['Shipment Month'].str[0:7]
	us_imports['month'] = us_imports['Arrival Date'].str[0:7]
	# make recent 12 months df of us_imports
	starting_month = str(int(str(datetime.today())[:4]) -1) + str(datetime.today())[4:7]
	us_imports_12 = us_imports[us_imports['month'] >= starting_month]

	parser = parser('template.pptx', china_exports, us_imports, us_imports_12)
	parser.parse_shipment_destinations()
	parser.parse_yearly_exports()
	parser.parse_hs_exports()
	parser.parse_yearly_imports()
	parser.parse_hs_imports()
	parser.parse_consignees_imports()
	parser.parse_consignees_imports_12()
	parser.parse_recent_shipments()
