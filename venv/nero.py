import os
import json
import requests
from requests.auth import HTTPBasicAuth
import csv
import pandas as pd
import xml.etree.ElementTree as ET
import openpyxl as xl
import tempfile
from datetime import datetime, timezone
from dateutil import tz
import getpass

from environment_handling import fromXL, time_handler

class neroApi():
    """
        ** Sets up the API to Nero Tracking system and pulls the corresponding data. **

        :return:
    """
    def __init__(self):
        """
            ** Grabs all data from Nero **

                This function iterates through each department (we only have one).
                Then iterates through each vehicle to grab each event associated with each vehicle.
                There are all other calls available and working, we just need to uncomment them when required.
                Some of the data is pulled in XML, then converted to XLSX; and, some of them are pulled in JSON.

            TODO: BREAK INTO SMALLER FUNCTIONS & CLEAN!!!

            :param:
            :return:
        """
        base_link = 'https://nero.contigo.com/dex/08/1'

        url_session, url_response, credentials = self.nero_credentials(base_link)

        # Get Day Start and Current Time
        day_start = time_handler.day_start(self)
        current_time = time_handler.current_time(self)

        # Uses UNIX time standards with UTC time zone
        starttime = day_start
        endtime = current_time

        os.chdir('../Dispatch_Reporting/Nero_Data')

        # Our current department is 6162, add any new departments to the list ['6162', '6182', ...]
        departments = ['6162']

        for d in departments:

            # Pull Dept Data (6162)
            link_dept = base_link + '/dept/' + d
            xlsx_name = 'department'
            description = 'department'
            col_names = ['uri', 'name']
            et_cols = ['tag', 'text', 'attribute']
            self.pull_data_to_xml(link_dept, url_session, credentials, xlsx_name)
            self.xml_to_xl(xlsx_name, description, et_cols, col_names)

            # Getting Vehicles in fleet
            link_vehicle = link_dept + '/vehicle'
            xlsx_name = 'vehicle_list'
            description = 'vehicle'
            col_names = ['uri', 'name']
            self.pull_data_to_xml(link_vehicle, url_session, credentials, xlsx_name)
            self.xml_to_xl(xlsx_name, description, et_cols, col_names)

            # Grab vehicle list
            sheet = 'Data_Columns'
            column = 'A'
            vehicle_dataframe = fromXL().select_column(xlsx_name, sheet, column)
            remove_string = 'https://nero.contigo.com/dex/08/1/dept/6162/vehicle/'
            replace_string = ''
            vehicle_list = fromXL.extract_info(self, vehicle_dataframe, remove_string, replace_string)

            # Grab vehicle name
            xlsx_name = 'vehicle_list'
            sheet = 'Data_Columns'
            column = 'B'
            vehicle_namelist = self.name_extraction(xlsx_name, sheet, column)

            # Vehicle Details
            for vehicleID, vehicleName in zip(vehicle_list, vehicle_namelist):
                link_vehicleID = link_vehicle + '/' + str(vehicleID)

                link_events = link_vehicleID + '/' + 'events' + '?ts.gte=' + str(starttime)# + '&ts.lt=' + str(endtime) #Note: If we declare an end time sometimes it is out of bounds that Nero can send data...
                xlsx_name = 'events' + vehicleName
                description = 'eventList'
                col_names = ['uri']
                self.pull_data_in_json(link_events, url_session, credentials, xlsx_name)

            # Landmark
            link_landmark = link_dept + '/landmark'
            xlsx_name = 'landmark'
            col_names = ['uri', 'name']
            description = 'landmark'
            self.pull_data_to_xml(link_landmark, url_session, credentials, xlsx_name)
            self.xml_to_xl(xlsx_name, description, et_cols, col_names)

            # Pull landmark list
            sheet = 'Data_Columns'
            column = 'A'
            landmark_dataframe = fromXL().select_column(xlsx_name, sheet, column)
            remove_string = 'https://nero.contigo.com/dex/08/1/dept/6162/landmark/'
            replace_string = ''
            landmark_list = fromXL.extract_info(self, landmark_dataframe, remove_string, replace_string)

            # Grab landmark name
            xlsx_name = 'landmark'
            sheet = 'Data_Columns'
            column = 'B'
            landmark_namelist = self.name_extraction(xlsx_name, sheet, column)

            # Check the length of the landmark list (+1 because it doesn't count header row) and landmark info
            if os.path.exists('landmark_csv.csv'):
                with open('landmark_csv.csv') as f:
                    csv_landmark_info_rowcount = sum(1 for line in f)
            else:
                csv_landmark_info_rowcount = 0

            if csv_landmark_info_rowcount != (len(landmark_namelist) + 1):

                # Try creating the data template in Pandas and then paste it into excel
                landmark_data = {'id': [], 'name': [], 'category': [], 'address': [], 'city': [], 'state': [], 'country': [],
                                 'zipcode': [], 'lon': [], 'lat': [], 'shape': [], 'radius': [], 'active': []}

                landmark_headers = ['id', 'name', 'category', 'address', 'city', 'state', 'country',
                                    'zipcode', 'lon', 'lat', 'shape', 'radius', 'active']

                for landmarkID, landmarkName in zip(landmark_list, landmark_namelist):
                    link = link_landmark + '/' + str(landmarkID)
                    landmark_dict = self.pull_data_to_dict(link, url_session, credentials)

                    #landmark_data = self.mergeDict(landmark_data, landmark_dict)
                    # Format should be:
                    # dict = [{'id': '892749', 'name': 'Arms Reach', ... },
                    #         {'id': '2742353', 'name': 'Nook Kits', ... }]
                    for k, v in landmark_data.items():
                        value = landmark_dict.get(k)
                        landmark_data[k].append(value)

                csv_file = "landmark_csv.csv"
                temp_df = pd.DataFrame()
                try:
                    with open(csv_file, 'w', newline='') as output_file:
                        writer = csv.writer(output_file)
                        writer.writerow(landmark_headers)
                        writer.writerows(zip(*landmark_data.values()))
                except IOError:
                    print("I/O error")

    def nero_credentials(self, base_link):
        """
            ** Checks the credentials of the user to the Nero Portal. **

                This function is an initial check of the user's credentials. If they fail, it will just loop through
                until they get it right.

            :param: base_link - the link to the Nero portal
            :return: url_response - The code the website returns (200 Pass, anything else fails)
                     credentials - saves the credentials for logins later (to gather the data)
        """
        # Gathering users credentials to access the Nero Portal
        login_check = 'n'
        while login_check == 'n':
            nero_login = input("Enter your login/email to the Nero portal: ")
            nero_password = input("Enter your password to the Nero portal:")
            print('Attempting to connect...')
            credentials = HTTPBasicAuth(nero_login, nero_password)
            try:
                url_session, url_response = self.call_url(base_link, credentials)
                if url_response.status_code == 200:
                    print('Successfully Logged In!')
                    login_check = 'y'
                else:
                    print('Login Failed!')
                    login_check = 'n'
            except:
                print('Login Failed!')
                login_check = 'n'
        return url_session, url_response, credentials

    def call_url(self, base_link, credentials):
        """
            ** Sets up the API to Nero Tracking system and pulls the corresponding data. **

            :param: base_link - the link to the Nero portal
                    credentials - passes in the credentials the user inputs
            :return: url_response - returns the website response (200 Pass, anything else fails)
        """
        url_session = requests.Session()
        url_response = url_session.get(base_link, auth=credentials, allow_redirects=True)
        return url_session, url_response

    def redirect_url(self, link, url_session, credentials):
        """
            ** Redirects the API to Nero Tracking system to the nested data feature and pulls the corresponding data. **

            :param: link - the overall link to access the specific data
                    url_session - Is the Nero API session previously setup with credentials
                    credentials - the username and password required to access the Nero portal
            :return: url_response - returns the website response (200 Pass, anything else fails)
        """
        url_session.post(link, auth=credentials, allow_redirects=True)
        url_response = url_session.get(link, auth=credentials)
        return url_response

    def pull_data_to_xml(self, link, url_session, credentials, xlsx_name):
        """
            ** Pulls data to XML file **

                Pulls the data from the Nero portal and saves the data into a XML file under the Nero_Data folder.

            :param: link - The link to the Nero portal
                    credentials - Credentials of the user for the Nero Portal
                    xlsx_name - The string that we will label the XML file.
            :return:
        """
        response = self.redirect_url(link, url_session, credentials)
        with open('%s.xml' % xlsx_name, 'wb') as foutput:
            foutput.write(response.content)

    def pull_data_in_json(self, link, url_session, credentials, xlsx_name):
        """
            ** Pulls data to JSON file. **

                Pulls the data from the Nero portal and saves the data into a JSON file under the Nero_Data folder.

            :param: link - The link to the Nero portal
                    credentials - Credentials of the user for the Nero Portal
                    xlsx_name - The string that we will label the XML file.
            :return:
        """
        response = self.redirect_url(link, url_session, credentials)
        data = json.dumps(response.json(), indent=4)
        with open('%s.json'% xlsx_name, 'w') as outfile:
            outfile.write(data)

    def xml_to_xl(self, xlsx_name, description, et_cols, col_names):
        """
            ** Converts XML file data to XLSX file. **

                Grabs and reads the XML file that was saved then it converts the data to XLSX readable
                format for reporting.

            :param: xlsx_name - The name of the XML file to be called and XLSX written.
                    description - The description of the data to pull
                    et_cols - The label of the sheet in the XLSX file, ET stands for the Element Tree package
                    col_names - The column names to extract
            :return:
        """
        try:
            tree = ET.parse(('%s.xml' % xlsx_name).encode('utf-8'))
            root = tree.getroot()
        except ET.ParseError as e:
            print("{} is not valid XML: {}".format(xlsx_name, e))

        # open a file for writing
        wb = xl.Workbook()
        ws1 = wb.create_sheet(title="ET_Columns")   # Creating the first sheet
        wb.active = 1

        # This is very hacky... TODO: figure out a better solution in creating a sheet without creating a blank one and then deleting it
        sheet = wb.get_sheet_by_name('Sheet')
        wb.remove_sheet(sheet)

        # create the csv writer object
        ws1.append(et_cols)
        # Get the useful data
        for data in root.getchildren():
            ws1.append([str(data.tag), str(data.text), str(data.attrib)])

        ws2 = wb.create_sheet(title="Data_Columns")  # Creating the second sheet
        wb.active = 2
        ws2.append(col_names)
        for data in root.findall('%s' % description):
            if data != None:
                column = []
                for col in col_names:
                    column.append(data.get('%s' % col))
                ws2.append(column)

        wb.save("%s.xlsx" %xlsx_name) # save

    def pull_data_to_temp(self, link, credentials):
        """
            ** Pulls data from API to temperary file to extract data **

                Pulls the data from the Nero portal and places the data into a temperary file.

            :param: link - The link to the Nero portal
                    credentials - Credentials of the user for the Nero Portal
            :return:
        """
        response = self.redirect_url(link, url_session, credentials)
        response_dump = response.content.decode('utf-8')

        try:
            root = ET.fromstring(response_dump)
        except ET.ParseError as e:
            print("{} is not valid XML: {}".format(xlsx_name, e))

        tmp = tempfile.TemporaryFile('w+t')
        try:
            for data in root.getchildren():
                # Save header
                with open('landmark_list.xlsx'):
                    print(data.tag)
                #for i in data:
                tmp.write(data.text + ' ')
            tmp.seek(0)
            print('Reading Temporary file: \n{0}'.format(tmp.read()))
        finally:
            tmp.close()

    def pull_data_to_dict(self, link, url_session, credentials):
        """
            ** Pulls data from API to DataFrame to extract data **

                Pulls the data from the Nero portal and places the data into a DataFrame.

            :param: link - The link to the Nero portal
                    credentials - Credentials of the user for the Nero Portal
            :return:
        """
        response = self.redirect_url(link, url_session, credentials)
        response_dump = response.content.decode('utf-8')

        try:
            root = ET.fromstring(response_dump)
        except ET.ParseError as e:
            print("{} is not valid XML: {}".format(xlsx_name, e))

        tag_vector = []
        data_vector = []
        dict1 = {'id': [], 'name': [], 'category': [], 'address': [], 'city': [], 'state': [], 'country': [],
                 'zipcode': [], 'lon': [], 'lat': [], 'shape': [], 'radius': [], 'active': []}
        for data in root.getchildren():
            dict1[str(data.tag)].append(str(data.text))
        return dict1

    def name_extraction(self, xlsx_name, sheet, column):
        """
            ** Pulls data from API to DataFrame to extract data **

                Pulls the data from the Nero portal and places the data into a DataFrame.

            :param: xlsx_name - (string) Name of the xlsx which we would like to pull the data from
                    sheet - (string) The name of the sheet inside of the xlsx that we want to pull the data from
                    column - (string) The name of the column inside the sheet and xlsx spreadsheet where we want to grab the data
            :return: namelist - (list of strings) extracted names from the xlsx, with a cleaned string of only the names
        """
        replace_string = ''
        nameframe = fromXL().select_column(xlsx_name, sheet, column)
        namelist = nameframe.values
        remove_string = '[\''
        namelist = fromXL.extract_info(self, nameframe, remove_string, replace_string)
        remove_string = '\']'
        namelist = fromXL.extract_info(self, nameframe, remove_string, replace_string)
        remove_string = ' '
        replace_string = '_'
        namelist = fromXL.extract_info(self, nameframe, remove_string, replace_string)
        return namelist

    def mergeDict(self, dict1, dict2):
        """
            ** Merges two dictionaries with appropriate keys, keeping both values **

                Merges two dictionaries with appropriate keys, keeping both values. Dictionary 2 will be appended to
                Dictionary 1.

            :param: dict1 - The link to the Nero portal
                    dict2 - Credentials of the user for the Nero Portal
            :return:
        """
        dict3 = {**dict1, **dict2}
        return dict3

    def merge_values(self, val1, val2):
        """
            ** Merges two values into a list **

                Checks if two values exist. If they don't it returns a list containing an empty string. If the values do
                exist, it returns a list with both values in it.

                !!! Currently this function is not used. TODO: Move this function to general functionality since it isn't
                Nero specific

            :param: val1 - (string) the first string of characters to merge
                    val2 - (string) the second string of characters to merge
            :return: a list of the two values merged
        """
        if val1 is None:
            return ['']
        if val2 is None:
            return ['']
        else:
            return [val1, val2]

# This file is for the Nero API calling/polling
if __name__ == "__nero__":
    neroApi()

# If more data is required from nero, below is the format for each type of data. The indented lines are supposed to be
# in the vehicle loop. (dependent for each vehicle)

            # xlsx_name = 'vehicle' + vehicleName
            # description = 'vehicle'
            # col_names = ['id', 'other', 'zoning', 'motiondetector', 'vin', 'license', 'year', 'color', 'model', 'make',
            #             'name', 'description', 'state', 'country', 'timezone', 'daylightsavings', 'synchedmileage',
            #             'synchedtimestamp', 'enginehours', 'events', 'eventlist']
            # self.pull_data_to_xml(link_vehicleID, url_response, xlsx_name)
            # self.xml_to_xl(xlsx_name, description, et_cols, col_names)

            # Getting events in relation to vehicle
            # link_event = link_vehicleID + '/' + 'event'
            # xlsx_name = 'event' + vehicleName
            # description = 'event'
            # col_names = ['uri']
            # self.pull_data_to_xml(link_event, url_response, xlsx_name)
            # self.xml_to_xl(xlsx_name, description, et_cols, col_names)

            # For each VehicleID/Event/ -> location|auxinput|startstop|ignition

            # Event Location Reports
            #link_location = link_event + '/' + 'location' + '?starttime=' + str(starttime)# + '&endtime=' + str(endtime)
            #xlsx_name = 'location' + 'event' + vehicleName
            #description = 'location'
            #col_names = ['uri']
            #self.pull_data_to_xml(link_location, credentials, xlsx_name)
            #self.xml_to_xl(xlsx_name, description, et_cols, col_names)

            # Auxiliary Event Input (Currently don't have any, implemented for future use)
            #link_aux = link_event + '/' + 'auxinput' + 'starttime=' + str(starttime) #+ '&endtime=' + str(endtime)
            #xlsx_name = 'aux' + 'event' + vehicleName
            #description = 'auxinput'
            #col_names = ['uri']
            #self.pull_data_to_xml(link_aux, credentials, xlsx_name)
            #self.xml_to_xl(xlsx_name, description, et_cols, col_names)

            # Start/Stop Event
            #link_startstop = link_event + '/' + 'startstop' + '?starttime=' + str(starttime) #+ '&endtime=' + str(endtime)
            #xlsx_name = 'startstop' + 'event' + vehicleName
            #description = 'location'
            #col_names = ['uri']
            #self.pull_data_to_xml(link_startstop, credentials, xlsx_name)
            #self.xml_to_xl(xlsx_name, description, et_cols, col_names)

            # Ignition Event
            #link_ignition = link_event + '/' + 'ignition' + '?starttime=' + str(starttime) #+ '&endtime=' + str(
            #    endtime)
            #xlsx_name = 'ignition' + 'event' + vehicleName
            #description = 'ignition'
            #col_names = ['uri']
            #self.pull_data_to_xml(link_ignition, credentials, xlsx_name)
            #self.xml_to_xl(xlsx_name, description, et_cols, col_names)

        # Assets (We currently have none but this is implemented for future use)
        #link_asset = link_dept + '/asset'
        #description = 'asset'
        #col_names = ['']
        #self.pull_data_to_xml(link_asset, credentials)
        #self.xml_to_csv(description, col_names)

        # Asset Details
        # for asset in asset_list:
        #    link = link + '/' + str(asset)
        #    vehicle_details_response = self.call_url(link, credentials)
        #    print(asset_details_response.text)

        # Personnel (Currently don't have any personnel)
        #link = link_dept + '/personnel'
        #xlsx_name = 'personnel'
        #description = 'personnel'
        #col_names = ['uri', 'name']
        #self.pull_data_to_xml(link, credentials, xlsx_name)
        #self.xml_to_xl(xlsx_name, description, et_cols, col_names)

        # Personnel Details
        # for person in personnel_list:
        #    link = link + '/' + str(person)
        #    self.pull_data_to_xml(link, credentials, xlsx_name)
        #    self.xml_to_xl(xlsx_name, description, et_cols, col_names)

        # Personnel Reports
        # for person in personnel_list:
        #    link = link_report + '/' + str(person)
        #    personnel_reports_response = self.call_url(link, credentials)
        #    print(personnel_reports_response.text)

        # For each Report/ -> item_status/jonas
        # Reports
        #link_report = link_dept + '/report'
        #xlsx_name = 'report'
        #col_names = ['uri', 'name']
        #description = 'report'
        #self.pull_data_to_xml(link_report, credentials, xlsx_name)
        #self.xml_to_xl(xlsx_name, description, et_cols, col_names)

        # Item Status
        #link_item = link_report + '/item_status'
        #xlsx_name = 'itemstatus'
        #col_names = ['uri', 'name']
        #description = 'itemstatus'
        #self.pull_data_to_xml(link_item, credentials, xlsx_name)
        #self.xml_to_xl(xlsx_name, description, et_cols, col_names)

        # Fleet Summary
        #link_fleet = base_link + '/report/fleet_summary'
        #xlsx_name = 'fleet_summary'
        #col_names = ['uri', 'name']
        #description = 'fleet_summary'
        #self.pull_data_to_xml(link_fleet, credentials, xlsx_name)
        #self.xml_to_xl(xlsx_name, description, et_cols, col_names)

        # JONAS
        #link_jonas = link_report + '/jonas'
        #xlsx_name = 'jonas'
        #col_names = ['uri', 'name']
        #description = 'jonas'
        #self.pull_data_to_xml(link_jonas, credentials, xlsx_name)
        #self.xml_to_xl(xlsx_name, description, et_cols, col_names)