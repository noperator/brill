#!/usr/bin/env python3

from sys import argv

from beautifultable import BeautifulTable
from bs4 import BeautifulSoup
from toml import load

# Get total charges for a given section.
gtc = lambda tag: float(tag.find('Total_Charges').contents[0][1:])

def get_overview(soup):
    user_subtotal = gtc(soup.find('Cost_Center', text='Subtotal').parent)
    acct_subtotal = gtc(soup.find('Account_Charges_Voice_and_Data'))
    return user_subtotal, acct_subtotal, user_subtotal + acct_subtotal

def get_share(soup, accountable_mtns, acct_subtotal):
    mtns = soup.find_all('mtn')
    return sum(gtc(mtn.parent) + acct_subtotal / len(mtns)
    	       for mtn in mtns if mtn.contents[0] in accountable_mtns)

def create_table(headers):
    table = BeautifulTable()
    table.set_style(BeautifulTable.STYLE_BOX_ROUNDED)
    table.intersect_top_left = '╒'
    table.top_border_char = '═'
    table.intersect_top_mid = '╤'
    table.intersect_top_right = '╕'
    table.intersect_header_left = '╞'
    table.header_separator_char = '═'
    table.intersect_header_mid = '╪'
    table.intersect_header_right = '╡'
    table.column_headers = headers
    return table

if __name__== '__main__':
    xml_bill = argv[1]
    soup = BeautifulSoup(open(xml_bill, 'r').read(), 'xml')
    config = load('config.toml')

    overview = create_table(['Item', 'Cost'])
    user, account, total = get_overview(soup)
    overview.append_row(['User subtotal', user])
    overview.append_row(['Account subtotal', account])
    overview.append_row(['Total', total])

    split = create_table(['Family', 'Share'])
    combined = 0
    for family in config['families']:
        numbers = [config['phone'][member] for member in family]
        share = get_share(soup, numbers, account)
        combined += share
        split.append_row([', '.join([member.title() for member in family]), share])
    split.append_row(['Total', combined])

    print('Invoice:', xml_bill)
    print(overview)
    print(split)
