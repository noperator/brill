<div align="center">
  <img src="https://i.imgflip.com/3r3rm5.jpg" />
</div>

### Description

The web interface for [Verizon My Business](b2b.verizonwireless.com/) is a pain to use. The invoice breakdowns are hard to make sense of, too. Brill uses Selenium to automate the process of logging in, listing/downloading invoices, and logging out; it'll then parse the invoices for you and group them according to the families that are sharing a single account.

### Install

```
git clone https://github.com/noperator/brill.git && cd brill
python3 -m venv env
source env/bin/activate
python3 -m pip install -U pip
python3 -m pip install -r requirements.txt
```

Configure `config.toml` as needed, using `config_example.toml` as a reference. Ensure that you've installed matching versions of Chromium and ChromeDriver; you can find specific versions of both on the [Download Chromium page](https://www.chromium.org/getting-involved/download-chromium).

### Usage
Fetch invoices:
```
python3 get_invoice.py
```

Parse an invoice:
```
python3 parse_invoice.py breakdown_feb_13_2020.xml
```
