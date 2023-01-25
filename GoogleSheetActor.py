from oauth2client.service_account import ServiceAccountCredentials
import gspread
import json
import time
import os

# Read gspread documentation for details about the sheet api

class GoogleSheetActor(object):

    def __init__(self, *args, **kwargs):
        # index for google sheet tab
        self.sheetidx = int(os.getenv('GSHEETIDX', "0"))

        self.scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        self.credentials = ServiceAccountCredentials.from_json_keyfile_name("hkuct-369514-e504bca2875f.json", self.scopes) #access the json key you downloaded earlier 
        self.file = gspread.authorize(self.credentials) # authenticate the JSON key with gspread
        self.sheet = self.file.open("BioDataKit")  #open sheet
        #print(dir(sheet))
        try:
            self.sheet = self.sheet.get_worksheet(self.sheetidx)
            #replace sheet_name with the name that corresponds to yours, e.g, it can be sheet1
        except Exception(e):
            print(e)
            print("WARNING: sheet not found, using the first sheet instead")
            self.sheet = self.sheet.get_worksheet(0)
        self.prepend_timestamp = True

    def handleSocket(self, address, data, *args, **kwargs):
        if self.prepend_timestamp:
            data = list(data)
            data.insert(0, time.time())
        self.sheet.append_row(data)

    def handleStop(self, *args, **kwargs):
        pass
