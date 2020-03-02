#!/usr/bin/env python3

# TODO:
# - proper wait for loading breakdown page
# - automate reports sent to terminal/file
#   - clean up redundant vbilling output

from os import path, rename
from pathlib import Path
from sys import stdout
from time import sleep

from selenium import webdriver  
from selenium.webdriver.chrome.options import Options  
from selenium.webdriver.common.keys import Keys  
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from toml import load

# Debug:
# from code import interact
# from pprint import pprint
# interact(local=locals())

def setup(chrome_config):
    print('Setting up...')
    
    # Set Chromium options and start WebDriver.
    chrome_options = Options()  
    chrome_options.add_argument('--headless')  
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--remote-debugging-port=' +       chrome_config['debug_port'])
    # chrome_options.add_argument('--proxy-server=' + proxy.proxy)
    chrome_options.binary_location = chrome_config['chromium_path']
    driver = webdriver.Chrome(
        executable_path=path.abspath(chrome_config['chromedriver_path']),
        options=chrome_options
        # service_args=['--verbose', '--log-path=./chromedriver.log']
    )
    
    # Enable automatic downloads to specified directory.
    driver.command_executor._commands['send_command'] = ('POST', '/session/$sessionId/chromium/send_command')
    params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': chrome_config['download_path']}}
    driver.execute('send_command', params)
    return driver

def login(driver, login_config):
    print('Requesting home page...', end='')
    stdout.flush()
    driver.get('https://b2b.verizonwireless.com/')
    try:
        WebDriverWait(driver, 10).until(ec.title_contains('Verizon business account login'))
        print('success.')
    except:
        print('failed.')
    
    # Populate login form with credentials and submit.
    print('Submitting credentials...')
    driver.find_element_by_name('userId').send_keys(login_config['user_id'])
    driver.find_element_by_name('password').send_keys(login_config['password'])
    driver.find_element_by_xpath("//*[@type='submit']").send_keys(Keys.ENTER)

    print('Waiting for login confirmation...', end='')
    stdout.flush()
    try:
        WebDriverWait(driver, 10).until(ec.title_contains('Landing Overview Page'))
        print('success.')
    except:
        print('unsuccessful.')
        print('Checking if OTP necessary...', end='')
        stdout.flush()
        try:
            WebDriverWait(driver, 10).until(ec.title_contains('Verizon Sign in'))
            driver.find_element_by_xpath("//button[contains(.,'Send One Time Passcode')]").send_keys(Keys.ENTER)
            print()
            otp_code = input('Enter OTP code: ')
            driver.find_element_by_name('otpCode').send_keys(otp_code)
            driver.find_element_by_xpath("//button[contains(.,'Verify and register device')]").send_keys(Keys.ENTER)
        except:
            print('Login unsuccessful.')

def list_invoices(driver):
    print('Getting invoice page...', end='')
    stdout.flush()
    driver.get('https://epb.verizonwireless.com/epass/reporting/main.go#/viewInvoices')
    try:
        WebDriverWait(driver, 10).until(ec.title_contains('Wireless Reports'))
        print('success.')
    except:
        print('unsuccessful.')
    sleep(5)
    
    # Get list of invoice dates from dropdown menu.
    return driver.execute_script('return angular.element($(\'#statementdates\')).scope().overview.invoiceData')

def get_invoice(driver, choice, date_str, download_path):
    print('Getting invoice page...', end='')
    stdout.flush()
    driver.get('https://epb.verizonwireless.com/epass/reporting/main.go#/viewInvoices')
    try:
        WebDriverWait(driver, 10).until(ec.title_contains('Wireless Reports'))
        print('success.')
    except:
        print('unsuccessful.')
    sleep(5)
    
    # Load invoice data for specified date.
    overview = "angular.element($(\'#statementdates\')).scope().overview"
    date = overview + '.invoiceData[' + str(choice) + ']'
    driver.execute_script('return ' + overview + '.updateQuickBillSummaryDataByDate(' + date + ')')

    print('Downloading bill...', end='')
    stdout.flush()
    driver.execute_script('angular.element($(\'[ng-if="!isBillAccountDetailLoading"]\')).scope().overview.navigateToBDownChargesPage()')
    sleep(5)
    driver.get('https://b2b.verizonwireless.com/sms/amsecure/bdownchargesusage/downloadTotalCharges.go?downloadType=XML')
    
    # Wait for download to finish, and rename XML file.
    while not list(Path(download_path).glob('Breakdown*')):
        sleep(1)
    download_name = list(Path(download_path).glob('Breakdown*'))[0]
    xml_bill = 'breakdown_' + date_str.replace(' ', '_').replace(',', '').lower() + '.xml'
    rename(download_name, download_path + '/' + xml_bill)
    print(xml_bill)

def logout(driver):
    print('Logging out...', end='')
    stdout.flush()
    driver.get('https://b2b.verizonwireless.com/sms/logout.go')
    try:
        WebDriverWait(driver, 10).until(ec.title_contains('Verizon business account login'))
        print('success.')
    except:
        print('unsuccessful.')
    driver.quit()

def yes_or_no(question):
    reply = str(input(question + ' (y/n): ')).lower().strip()
    if reply[0] == 'y':
        return True
    if reply[0] == 'n':
        return False
    else:
        return yes_or_no('Invalid response. Try again.')

if __name__== '__main__':
    config = load('config.toml')
    driver = setup(config['chrome'])
    login(driver, config['login'])
    dates = list_invoices(driver)
    for i, date in enumerate(dates):
        print('[' + str(i + 1) + ']', date['invoiceFormattedDate'])
    choice = int(input('Choose invoice date index: ')) - 1
    get_invoice(driver, choice, dates[choice]['invoiceFormattedDate'], config['chrome']['download_path'])
    while yes_or_no('Would you like to get another invoice?'):
        for i, date in enumerate(dates):
            print('[' + str(i + 1) + ']', date['invoiceFormattedDate'])
        choice = int(input('Choose invoice date index: ')) - 1
        get_invoice(driver, choice, dates[choice]['invoiceFormattedDate'], config['chrome']['download_path'])
    logout(driver)
