import os

# Setting the environment paths as global variables
#global myMainPath
#myMainPath = "../venv"

# Importing local modules
import dispatch_reporting
import environment_handling
import cioffi_email

def main_function():
    """
        ** Runs through all the automation steps for Cioffi's Reporting **

        Currently runs through:

            -> Runs through Dispatch Driver Report
            -> Setups the Secure Server and Email then grabs the XSLX sheet and appends it to the email and send the email

        :param: None needed for the function. (User Inputs: Nero Credentials and Email Credentials)
        :return: None provided from the function. (Send the email)
    """

    # Calls the dispatch reporting functionality. Goes to the dispatch_reporting module
    dispatch_reporting.dispatch_reporting()

    # Creating a secure server. Goes to the cioffi_email module
    cioffi_email.SMTP_Server()

if __name__ == "__main__":
    main_function()