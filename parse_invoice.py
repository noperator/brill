#!/usr/bin/env python3

from sys import argv

from bs4 import BeautifulSoup
from toml import load

def print_table(data):
    headers = ['Billing Item', 'Cost']
    def print_row(row, wid, sep, fil):
        for i, elem in enumerate(row):
            print(sep + fil + elem  + fil * (wid[i] - len(elem) - 1),
                  end = sep + '\n' if i == len(wid) - 1 else '')
    widths = [len(max([row[i] for row in data] + [headers[i]], key=len)) + 2
            for i in range(len(headers))]
    print_row([''] * len(widths), widths, '+', '-')
    print_row(headers, widths, '|', ' ')
    print_row([''] * len(widths), widths, '+', '-')
    for row in data: print_row(row, widths, '|', ' ')
    print_row([''] * len(widths), widths, '+', '-')

def get_shared(xml_bill):
    soup = BeautifulSoup(open(xml_bill, 'r').read(), 'xml')
    mtns = soup.find_all('mtn')
    gtc = lambda tag: float(tag.find('Total_Charges').contents[0][1:])
    user_subtotal     = gtc(soup.find('Cost_Center', text='Subtotal').parent)
    acct_subtotal     = gtc(soup.find('Account_Charges_Voice_and_Data'))
    ff = lambda n: str('%.2f' % n)
    return [['User subtotal',    ff(user_subtotal)],
            ['Account subtotal (shared)', ff(acct_subtotal)],
            ['Total',            ff(user_subtotal + acct_subtotal)]]

def get_data(xml_bill, accountable_mtns, family):
    soup = BeautifulSoup(open(xml_bill, 'r').read(), 'xml')
    mtns = soup.find_all('mtn')
    gtc = lambda tag: float(tag.find('Total_Charges').contents[0][1:])
    user_subtotal     = gtc(soup.find('Cost_Center', text='Subtotal').parent)
    acct_subtotal     = gtc(soup.find('Account_Charges_Voice_and_Data'))
    accountable_costs = sum(gtc(mtn.parent) + acct_subtotal / len(mtns)
    	                    for mtn in mtns if mtn.contents[0] in accountable_mtns)
    ff = lambda n: str('%.2f' % n)
    return [[', '.join(family), ff(accountable_costs)]]

if __name__== '__main__':
    config = load('config.toml')
    xml_bill = argv[1]
    lines = get_shared(xml_bill)
    for family in config['families']:
        numbers = [config['phone'][member] for member in family]
        lines += get_data(xml_bill, numbers, family)
    print_table(lines)
