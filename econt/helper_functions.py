import datetime
import xml.etree.ElementTree as ElemenTree


def add_attribute(xml, tag, attr, value):
    '''
    Description:
    Gets an XML file (string or xml) and adds the desired
    attribute with value to the given tag

    Parameters:
    -----------
    :param xml:  string or XML
    :param tag: string
    :param attr: string
    :param value: string

    Returns:
    ---------
    :return: XML
    '''
    tree = ElemenTree.XML(xml)
    for tag in tree.iter(tag):
        tag.set(attr,value)
    return ElemenTree.tostring(tree, encoding='UTF-8', method='xml')


def validate_date(date_text):
    try:
        param = datetime.datetime.strptime(date_text, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Incorrect data format, should be YYYY-MM-DD")
    today = datetime.datetime.today()
    if param.date() < today.date():
        raise ValueError('Date in the past!')


def next_working_day(date):
    # date has already gone through validate_date func
    param = datetime.datetime.strptime(date, '%Y-%m-%d')
    # Monday - 0
    # Tueday - 1
    # ...
    # Saturday - 5
    if param.weekday() == 5:
        param += datetime.timedelta(days=2)
    else:
        param += datetime.timedelta(days=1)
    return str(param.date())
