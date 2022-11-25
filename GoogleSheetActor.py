from oauth2client.service_account import ServiceAccountCredentials
import gspread
import json

class GoogleSheetActor(object):

    def __init__(self, *args, **kwargs):
        self.scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        self.credentials = ServiceAccountCredentials.from_json_keyfile_name("hkuct-369514-e504bca2875f.json", self.scopes) #access the json key you downloaded earlier 
        self.file = gspread.authorize(self.credentials) # authenticate the JSON key with gspread
        self.sheet = self.file.open("BioDataKit")  #open sheet
        #print(dir(sheet))
        self.sheet = self.sheet.sheet1  #replace sheet_name with the name that corresponds to yours, e.g, it can be sheet1
        #print(dir(sheet))
        #all_cells = sheet.range('A1:C6')
        #print(all_cells[0])
        #report_line = ['name', 'finished <None or int>', 'duration <str>', 'id']
        #self.sheet.append_row(report_line)

    def handleSocket(self, address, data, *args, **kwargs):
        self.sheet.append_row(data)
