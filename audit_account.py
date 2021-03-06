#!/usr/bin/env python3

from json import loads
from os import path, rename
from pathlib import Path
from sys import argv, stdout, exit
from time import sleep, perf_counter

from beautifultable import BeautifulTable
from selenium import webdriver  
from selenium.webdriver.chrome.options import Options  
from selenium.webdriver.common.keys import Keys  
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from toml import load

debug = '-d' in argv
check = '-c' in argv

if debug:
    from code import interact
    from pprint import pprint

def pause():
    if debug:
        interact(local=locals())

def load_page(message, url, title):
    print(message + '...', end='')
    stdout.flush()
    start = perf_counter()
    driver.get(url)
    try:
        WebDriverWait(driver, 10).until(ec.title_contains(title))
        print('success.', end=' ')
    except:
        print('failed.', end=' ')
    end = perf_counter()
    print('Took', round(end - start, 2), 'seconds.')

def setup(chrome_config):
    print('Setting up...')

    # Set Chromium options and start WebDriver.
    chrome_options = Options()  
    if not debug:
        chrome_options.add_argument('--headless')  
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--remote-debugging-port=' + chrome_config['debug_port'])
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
    load_page('Requesting home page',
              'https://b2b.verizonwireless.com/',
              'Verizon Business Account Sign In')

    # Populate login form with credentials and submit.
    print('Submitting credentials and waiting for login confirmation...', end='')
    driver.find_element_by_name('userId').send_keys(login_config['user_id'])
    driver.find_element_by_name('password').send_keys(login_config['password'])
    driver.find_element_by_xpath("//*[@type='submit']").send_keys(Keys.ENTER)
    stdout.flush()
    try:
        WebDriverWait(driver, 10).until(ec.title_contains('MyBusiness'))
        print('success.')
    except:
        print('failed.')
        print('Checking if OTP necessary...', end='')
        stdout.flush()
        try:
            WebDriverWait(driver, 10).until(ec.title_contains('Verizon Sign in'))
            driver.find_element_by_xpath("//button[contains(.,'Send One Time Passcode')]").send_keys(Keys.ENTER)
            print()
            otp_code = input('Enter OTP code: ')
            driver.find_element_by_name('otpCode').send_keys(otp_code)
            driver.find_element_by_xpath("//button[contains(.,'Verify and register device')]").send_keys(Keys.ENTER)
            try:
                WebDriverWait(driver, 10).until(ec.title_contains('MyBusiness'))
                print('success.')
            except:
                exit('login unsuccessful.')
        except:
            exit('login unsuccessful.')

def list_invoices(driver):
    load_page('Listing invoices',
              'https://epb.verizonwireless.com/epass/reporting/main.go#/viewInvoices',
              'Wireless Reports')

    # Get list of invoice dates from dropdown menu.
    dates = None
    while not dates:
        sleep(1)
        dates = driver.execute_script("return angular.element($('#statementdates')).scope().overview.invoiceData")
    return dates

def get_invoice(driver, dates, download_path):

    # Prompt user to specify which invoice to download.
    for i, date in enumerate(dates):
        print('[' + str(f"{i + 1:0>2}") + ']', date['invoiceFormattedDate'])
    choice = int(input('Choose invoice date index: ')) - 1
    date_str = dates[choice]['invoiceFormattedDate']

    load_page('Getting invoice page',
              'https://epb.verizonwireless.com/epass/reporting/main.go#/viewInvoices',
              'Wireless Reports')

    # Load invoice data for specified date.
    while True:
        try:
            overview = "angular.element($('#statementdates')).scope().overview"
            date = overview + '.invoiceData[' + str(choice) + ']'
            driver.execute_script('return ' + overview + '.updateQuickBillSummaryDataByDate(' + date + ')')
            break
        except:
            pass

    print('Getting breakdown page...', end='')
    stdout.flush()
    driver.execute_script('angular.element($(\'[ng-if="!isBillAccountDetailLoading"]\')).scope().overview.navigateToBDownChargesPage()')
    try:
        WebDriverWait(driver, 10).until(ec.title_contains('Total Charges'))
        print('success.')
    except:
        print('failed.')

    print('Downloading bill...', end='')
    stdout.flush()
    driver.get('https://b2b.verizonwireless.com/sms/amsecure/bdownchargesusage/downloadTotalCharges.go?downloadType=XML')

    # Wait for download to finish, and rename XML file.
    while not list(Path(download_path).glob('Breakdown*')):
        sleep(1)
    download_name = list(Path(download_path).glob('Breakdown*'))[0]
    xml_bill = 'breakdown_' + date_str.replace(' ', '_').replace(',', '').lower() + '.xml'
    rename(download_name, download_path + '/' + xml_bill)
    print(xml_bill)

def logout(driver):
    load_page('Logging out',
              'https://b2b.verizonwireless.com/sms/logout.go',
              'Verizon Business Account Sign In')
    driver.quit()

def yes_or_no(question):
    reply = str(input(question + ' (y/n): ')).lower().strip()
    if reply[0] == 'y':
        return True
    if reply[0] == 'n':
        return False
    else:
        return yes_or_no('Invalid response. Try again.')

def xhr(driver, url):
    js = '''var xhr = new XMLHttpRequest();
            xhr.send();
            return xhr.response;''' % url
    return driver.execute_script(js);

def get_payments(driver):
    load_page('Getting payments',
              'https://b2b.verizonwireless.com/sms/amsecure/payment/paymenthistorystatus/load.go',
              '')
    payments = driver.find_element_by_tag_name('pre').text
    table = BeautifulTable()
    table.set_style(BeautifulTable.STYLE_COMPACT)
    table.column_headers = ('Date', 'Amount', 'Method', 'Status')
    for p in loads(payments)['data']['paymentHistoryStatusList']:
        table.append_row((p['actionDate'],
                          '$' + str('{:.2f}'.format(float(p['paymentAmount']))),
                          p['paymentMethod'],
                          p['paymentStatus']))
    driver.execute_script('window.history.go(-1)')
    return table

def get_balance(driver):
    return driver.find_element_by_xpath('/html/body/app-root/app-main/app-dashboard/div[3]/app-billing/div/div[2]/div/div/swiper/div[1]/div[1]/div/div/div/div/div[1]/div[2]').text

if __name__== '__main__':
    config = load('config.toml')
    driver = setup(config['chrome'])
    login(driver, config['login'])

    print('Real-time balance:', get_balance(driver))
    print('Recent payments:\n', get_payments(driver))

    if not check:
        dates = list_invoices(driver)
        while True:
            get_invoice(driver, dates, config['chrome']['download_path'])
            if not yes_or_no('Would you like to get another invoice?'):
                break

    logout(driver)
