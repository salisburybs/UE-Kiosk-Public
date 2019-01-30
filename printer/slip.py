import cups
import tempfile
import pdfkit
import os

conn = cups.Connection()


def get_printer():
    if 'none' in conn.getPrinterAttributes(conn.getDefault(), requested_attributes=['printer-state-reasons']).\
            get('printer-state-reasons'):
        return conn.getDefault()

    for printer in conn.getPrinters():
        if 'none' in conn.getPrinterAttributes(printer, requested_attributes=['printer-state-reasons']).\
                get('printer-state-reasons'):
            return printer
    return None


def print_slip_from_html(html, printer=None):
    options = {
        'page-size': 'Letter',
        'margin-top': '0.5in',
        'margin-right': '0.5in',
        'margin-bottom': '0.5in',
        'margin-left': '0.5in',
        'encoding': "UTF-8",
        'orientation': 'landscape'
    }

    if printer is None:
        printer = get_printer()

    with tempfile.NamedTemporaryFile(mode='w', delete=True, suffix='.pdf') as tf:
        pdfkit.from_string(input=html, output_path=tf.name, options=options)
        conn.printFile(printer=printer, title='Pick Slip', filename=tf.name, options={})


if __name__ == '__main__':
    from pprint import pprint
    pprint(conn.getPrinterAttributes('Netadmin-LJ-CP4520-02'))
