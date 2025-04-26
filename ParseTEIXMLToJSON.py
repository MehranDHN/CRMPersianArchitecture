import json
import xmltodict
import pprint


data_dict = {}
with open("I:\IAPython\AAT\TEIXml\\bv_053_TEI.xml") as xml_file:
    data_dict = xmltodict.parse(xml_file.read())

print('reading xml complete')
json_data = json.dumps(data_dict)
#pp = pprint.PrettyPrinter(indent=4)
#pp.pprint(json.dumps(data_dict))  

with open("I:\IAPython\AAT\TEIXml\\bv_053_TEI.json", "w") as json_file:
        json_file.write(json_data)

print('Finished.')        