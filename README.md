# Brill

Download and parse invoices from Verizon business accounts.

<div align="center">
  <kbd>
    <img src="https://i.imgflip.com/3r3rm5.jpg" />
  </kbd>
</div>

## Description

The web interface for [Verizon My Business](b2b.verizonwireless.com/) is a pain to use. The invoice breakdowns are hard to make sense of, too. Brill uses Selenium to automate the process of logging in, listing/downloading invoices, and logging out; it'll then parse the invoices for you and group them according to the families that are sharing a single account.

## Getting started

### Install

```
git clone https://github.com/noperator/brill.git && cd brill
python3 -m venv env
source env/bin/activate
python3 -m pip install -U pip
python3 -m pip install -r requirements.txt
```

### Configure

Configure `config.toml` as needed. Ensure that you've installed matching versions of Chromium and ChromeDriver; you can find specific versions of both on the [Download Chromium page](https://www.chromium.org/getting-involved/download-chromium).

### Usage

Check balance and recent payments, and (if not specifying `-c` option) and fetch invoices:

```
$ python3 audit_account.py
Setting up...
Requesting home page...success. Took 2.21 seconds.
Submitting credentials and waiting for login confirmation...success.
Real-time balance: $325.16
Recent payments:
      Date       Amount    Method    Status
-------------- --------- --------- ---------
 Apr 23, 2020   $64.15    XXX1234   Success
 Apr 22, 2020   $137.53   XXX2345   Success
 Jan 15, 2020    $0.00     None     Success
 Dec 28, 2019   $122.82   XXX3456   Success
 Dec 28, 2019   $122.82   XXX3456   Failed
Listing invoices...success. Took 4.08 seconds.
[01] Apr 13, 2020
[02] Mar 13, 2020
[03] Feb 13, 2020
[04] Jan 13, 2020
[05] Dec 13, 2019
[06] Nov 13, 2019
[07] Oct 13, 2019
[08] Sep 13, 2019
[09] Aug 13, 2019
[10] Jul 13, 2019
[11] Jun 13, 2019
[12] May 13, 2019
Choose invoice date index: 3
Getting invoice page...success. Took 0.04 seconds.
Getting breakdown page...success.
Downloading bill...breakdown_feb_13_2020.xml
Would you like to get another invoice? (y/n): n
Logging out...success. Took 6.7 seconds.
```

Parse an invoice:

```
$ python3 parse_invoice.py breakdown_feb_13_2020.xml
Invoice: breakdown_feb_13_2020.xml
╭──────────────────┬────────╮
│       Item       │  Cost  │
├──────────────────┼────────┤
│  User subtotal   │ 116.7  │
├──────────────────┼────────┤
│ Account subtotal │ 59.72  │
├──────────────────┼────────┤
│      Total       │ 176.42 │
╰──────────────────┴────────╯
╭────────────────────────────┬────────╮
│           Family           │ Share  │
├────────────────────────────┼────────┤
│        Jane, John          │ 104.88 │
├────────────────────────────┼────────┤
│        Bob, Alice          │ 71.54  │
├────────────────────────────┼────────┤
│           Total            │ 176.42 │
╰────────────────────────────┴────────╯
```

## Back matter

### To-do

- [ ] Time out for invalid invoice
- [ ] Gracefully handle `SIGINT` (i.e., log out and stop WebDriver)
- [ ] Force two decimal places in BeautifulTable (currently shows between 1–3)

### License

This project is licensed under the [MIT License](LICENSE.md).
