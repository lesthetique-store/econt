import dicttoxml
import logging
import requests
import xmltodict
from json import loads, dumps
from collections import OrderedDict

from nested_lookup import nested_lookup
from xml.parsers.expat import ExpatError
from helper_functions import *
from request_types import RequestType
from report_types import ReportType
from status_codes import StatusCode

ECONT_PARCELS_DEMO_URL = 'http://demo.econt.com/e-econt/xml_parcel_import2.php'
ECONT_PARCELS_URL = 'http://www.econt.com/e-econt/xml_parcel_import2.php'
ECONT_SERVICE_URL = 'http://econt.com/e-econt/xml_service_tool.php'
ECONT_SERVICE_DEMO_URL = 'http://demo.econt.com/e-econt/xml_service_tool.php'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler('econt.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class Econt:
    def __init__(self, username, password, demo=True):
        self.username = username
        self.password = password

        logger.info('Creating Econt object')
        self.demo = demo
        if self.demo:
            self.service_url = ECONT_SERVICE_DEMO_URL
            self.parcels_url = ECONT_PARCELS_DEMO_URL
        else:
            self.service_url = ECONT_SERVICE_URL
            self.parcels_url = ECONT_PARCELS_URL

    def to_dict(self, input_ordered_dict):
        return loads(dumps(input_ordered_dict))

    def __build_request(self, request_type, authenticate=False):
        '''
        Description:
        ------------
        The method takes request_type and authenticate as arguments,
        builds and sends an xml request to the server and returns the
        response corresponding to the request_type

        Parameter:
        ----------
        :param request_type : string
        :param authenticate : bool

        Returns:
        --------
        :return python dictionary, where the first key 'status' holds
        the status of the response, whereas the second key 'message' holds
        the desired python dictionary if the status is 0
        '''
        return self.request(url=self.service_url,
                            xml=self.xml_builder(
                                data={'request_type': request_type},
                                authenticate=authenticate))

    def request(self, url, xml):
        '''
        Description:
        -----------
        The method takes XML and URL as strings and sends an XML request
        to the given url, the response is converted into a python dictionary
        and then returned to the user

        Parameters:
        -----------
        :param url: string
        :param xml: string

        Returns:
        --------
        :return python dictionary, where the first key 'status' holds
        the status of the response, whereas the second key 'message' holds
        the desired python dictionary if the status is 0

        Status Codes:
        --------------
        0 = OK
        1 = CONNECTION ERROR
        2 = INVALID URL
        3 = EMPTY URL
        4 = XML PARSE ERROR
        5 = ECONT API XML ERROR
        6 = UNEXPECTED ERROR
        '''
        logger.info('Calling request')
        logger.debug('In request with {} and {}'.format(url, xml))

        xml_session = requests.session()
        xml_session.headers = {'Content-Type': 'text/xml'}
        if not xml:
            raise ValueError("Empty XML!")
        try:
            response_xml = xml_session.post(url=url, data=xml)
            result = xmltodict.parse(response_xml.text)
            response = None
            if 'API_ERR' in response_xml.text:
                error_message = nested_lookup(document=result, key='error')
                try:
                    # if the error message resides in <message> </message>
                    # the code below throws an exception
                    # because it cant covert dict to string
                    response = {'status': StatusCode.ECONT_API_XML_ERROR,
                                'message': ''.join(error_message),
                                'data': None}
                except:
                    # here we are getting the contents of
                    # the previously mentioned <message> </message>
                    logger.exception('''Conversion from dict to string failed
                                     because error message is in message tag''')
                    nested_message = nested_lookup(document=error_message, key='message')
                    response = {'status': StatusCode.ECONT_API_XML_ERROR,
                                'message': ''.join(nested_message),
                                'data': None}
            else:
                response = {'status': StatusCode.STATUS_OK,
                            'message': 'OK',
                            'data': result}
        except requests.exceptions.InvalidURL:
            logger.exception('The provided url is invalid')
            response = {'status': StatusCode.INVALID_URL_ERROR,
                        'message': 'The url you provided is invalid!',
                        'data': None}
        except requests.exceptions.MissingSchema:
            logger.exception('No http:// or https:// in url')
            response = {'status': StatusCode.EMPTY_URL_ERROR,
                        'message': 'Please provide http:// or https://!',
                        'data': None}
        except requests.exceptions.ConnectionError:
            logger.exception('Connection Error')
            response = {'status': StatusCode.CONNECTION_ERROR,
                        'message': 'There has been a connection error!',
                        'data': None}
        except ExpatError:
            logger.exception('XML parsing failed')
            response = {'status': StatusCode.XML_PARSE_ERROR,
                        'message': 'XML parsing failed!',
                        'data': None}
        except:
            logger.exception('Unexpected error')
            response = {'status': StatusCode.UNEXPECTED_ERROR,
                        'message': 'An unexpected error occurred!',
                        'data': None}
        finally:
            xml_session.close()

            logger.debug('request returned {}'.format(response))

            return response

    def xml_builder(self, data, root_element='request', authenticate=False):
        '''
        Description:
        -----------
        The method takes data, root_element, and authenticate as
        json, string, and bool respectively and returns an xml. When
        authenticate equals True, custom_root is set to root_element
        and client username and password are added to the json.
        Then, the json is converted to an xml and returned to the user.

        Parameters:
        -----------
        :param data: json
        :param root_element: str
        :param authenticate: bool

        Returns:
        --------
        :return xml
        '''
        logger.info('Calling xml_builder')

        if authenticate:
            data.update(self.get_user_credentials())
        return dicttoxml.dicttoxml(data, custom_root=root_element,
                                   attr_type=False)

    def get_user_credentials(self):
        '''
        Description:
        -----------
        The method returns the previously set client information
        consisting of username and password in a dictionary

        Returns:
        --------
        :return python dictionary

        >>> a = Econt('username', 'password')
        >>> a.get_user_credentials()
        {'client': {'username': 'username', 'password': 'password'}}

        '''
        logger.info('Calling get_user_credentials')

        return {
            'client': {
                'username': self.username,
                'password': self.password
            }
        }

    def validate_address(self, address_json):
        '''
        Description:
        ------------
        The method takes an address as a json object
        and sends an XML request to the server to determine
        if the address is valid

        Parameter
        ---------
        param : json

        Returns
        -------
        json
            If the address is VALID
            a json object with 'status' : 0 is returned

            If the address is INVALID
            a json object with an error message is returned
        '''
        # adding the <address> </address>
        # and <request_type> check_address <request_type>
        address_json = {'request_type': RequestType.CHECK_ADDRESS,
                        'address': address_json}

        logger.info('Calling validate_address')

        response = self.request(url=self.service_url,
                                xml=self.xml_builder(data=address_json,
                                                     authenticate=True))
        # the condition below checks if we have managed to get data from ECONT
        # the invalid message doesnt carry an API ERROR TAG
        # so we check for errors below
        if response['data']:
            if response['data']['response']['address']['validation_status'] == 'invalid':
                return {'status': StatusCode.ECONT_API_XML_ERROR,
                        'message': response['data']['response']['address']['error'],
                        'data': None}
        return response

    def register(self, data):
        '''
        Description:
        ------------
        The method takes a json object
        and sends an XML request to the server to
        create an account in Econt

        Parameter
        ---------
        param : json

        Returns
        -------
        :return python dictionary, where the first key 'status' holds
        the status of the response, whereas the second key 'message' holds
        the desired python dictionary if the status is 0
        '''
        logger.info('Calling register')

        data = {'system': {'api_action': 'validate'},
                'request_type': RequestType.E_ECONT_REGISTRATION,
                'data': data}
        return self.request(url=self.service_url,
                            xml=self.xml_builder(data=data,
                                                 authenticate=True))

    def retrieve_profile(self):
        '''
        Description:
        ------------
        The method sends an XML request to the server to
        retrieve information about the profile of the current user

        Parameter
        ---------
        :param None

        Returns
        -------
        :return python dictionary with status, message and data
        '''
        logger.info('Calling retrieve_profile')

        response = self.__build_request(RequestType.PROFILE, authenticate=True)
        if response['data']:
            response['data'] = response['data']['response']
        return response

    def get_offices(self):
        '''
        Description:
        ------------
        The method sends an XML request to the server to
        get information about the offices of Econt

        Parameter
        ---------
        :param None

        Returns
        -------
        :return json
        '''
        logger.info('Calling get_offices')

        return self.__build_request(RequestType.OFFICES, authenticate=True)

    def cancel_shipment(self, shipment_number):
        '''
        Description:
        ------------
        The method sends an XML request to the server
        to cancel shipments

        Parameter
        ---------
        :param shipment_number: a unique number corresponding to
                                the particular shipment
        Returns
        -------
        :return python dictionary : with status and message keys
        '''
        logger.info('Calling cancel_shipment')

        data = {'request_type': RequestType.CANCEL_SHIPMENTS,
                'cancel_shipments': {'num': shipment_number}}
        response = self.request(url=self.service_url,
                                xml=self.xml_builder(data=data,
                                                     authenticate=True))
        return response

    def get_streets(self):
        '''
        Description:
        ------------
        The method sends an XML request to the server
        to get information about the streets in different cities

        Parameter:
        ----------
        :param None

        Returns:
        --------
        :return python dictionary received from Econt's server with info about streets
        '''
        logger.info('Calling get_streets')

        return self.__build_request(RequestType.STREETS, authenticate=True)

    def get_cities(self, id_zone=None, report_type=ReportType.SHORT):
        '''
        Description:
        ------------
        The method sends an XML request to the server
        to get information about the cities Econt operates in

        Parameter:
        ----------
        :param id_zone: number (int or string)
        :param report_type: ReportType('all' or 'short')

        Returns:
        --------
        :return: python dictionary with status, message
        and data received from Econt's server about cities
        '''
        logger.info('Calling get_cities')
        logger.debug('In get_cities with id_zone {} and report type {}'.format(id_zone, report_type))
        if report_type == ReportType.ALL and not id_zone:
            return self.__build_request(RequestType.CITIES, authenticate=True)
        else:
            cities_request_info = {'report_type': report_type}
            if id_zone:
                cities_request_info['id_zone'] = str(id_zone)
            data = {'request_type': RequestType.CITIES,
                    'cities': cities_request_info}
            return self.request(url=self.service_url,
                                xml=self.xml_builder(data=data,
                                                     authenticate=True))

    def get_streets_by_city(self, city_post_code):
        '''
        Description:
        ------------
        The method calls get_streets() and uses the city_post_code
        given as argument to find all the streets in the given city.

        Parameter:
        ----------
        :param city_post_code : str or int

        Returns:
        --------
        :return Python dict that contains status, message and data keys
        containing respectively the status code as an int, the message as a str
        and a dict containing all the streets in the given city
        '''

        if not city_post_code:
            logger.exception('Post code in get_streets_by_city is empty')
            raise ValueError("Post code can't be empty")

        logger.info('Calling get_streets_by_city')
        logger.debug('In get_streets_by_city with post code {}'.format(city_post_code))
        city_post_code = str(city_post_code)
        streets_dict = self.get_streets()
        streets_list = []
        streets_dict = self.to_dict(streets_dict)
        if streets_dict['data']['response']:
            streets_data = streets_dict['data']['response']['cities_street']['e']
            for street in streets_data:
                if street['city_post_code'] == city_post_code:
                    streets_list.append(street)
        streets_dict['data'] = {'streets': streets_list}
        return streets_dict

    def get_offices_by_city(self, city_post_code):
        '''
        Description:
        ------------
        The method calls get_offices() and uses the post_code
        given as an argument to find all the offices in the given area

        Parameter:
        ----------
        :param city_post_code : string or integer

        Returns:
        --------
        :return python list that contains all of the offices in the city
        '''

        if not city_post_code:
            logger.exception('Post code in get_offices_by_city is empty')
            raise ValueError("Post code can't be empty")

        logger.info('Calling get_streets_by_city')
        logger.debug('In get_streets_by_city with post code {}'.format(city_post_code))

        city_post_code = str(city_post_code)
        offices_list = []
        offices_dict = self.to_dict(self.get_offices())
        if offices_dict['data']['response']:
            offices_data = offices_dict['data']['response']['offices']['e']
            for office in offices_data:
                if office['post_code'] == city_post_code:
                    offices_list.append(office)
        offices_dict['data'] = {'streets': offices_list}
        return offices_dict

    def get_countries(self):
        '''
        Description:
        ------------
        The method sends an XML request to Econt
        to find all the countries they work with

        Parameter:
        ----------
        :param none

        Returns:
        --------
        :return python dict with status, message and data
        '''
        logger.info('Calling get_countries')

        response = self.__build_request(RequestType.COUNTRIES, authenticate=True)
        if response['data']:
            all_countries = response['data']['response']['e']
            response['data'] = {'countries': all_countries}
        return response

    def get_seller_addresses(self):
        '''
        Description:
        ------------
        The method calls retrieve_profile() and
        extracts the addresses from the result

        Parameter:
        ----------
        :param none

        Returns:
        --------
        :return python dictionary with status, message and data
        '''
        logger.info('Calling get_seller_addresses')

        response = self.retrieve_profile()
        response = self.to_dict(response)
        if response['data']:
            addresses = response['data']['addresses']['e']
            response['data'] = {'addresses': addresses}
        return response

    def get_quarters(self):
        '''
        Description:
        ------------
        The method sends an XML request to the server
        to get information about all the quarters in all cities

        Parameter:
        ----------
        :param None

        Returns:
        --------
        :return python dictionary received from Econt's server with
        info about quarters
        '''
        logger.info('Calling get_quarters')

        return self.__build_request(RequestType.QUARTERS, authenticate=True)

    def get_quarters_by_post_code(self, city_post_code):
        '''
        Description:
        ------------
        The method calls get_quarters() and uses the post_code
        given as an argument to find all the quarters in the given area

        Parameter:
        ----------
        :param city_post_code : string or integer

        Returns:
        --------
        :return python dictionary with status, message and data,
        where data contains a list of all the quarters in the city
        '''
        logger.info('Calling get_quarters_by_post_code')
        logger.debug('In get_quarters_by_post_code with post code {}'.format(city_post_code))

        if not city_post_code:
            logger.exception('Post code in get_quarters_by_post_code is empty')
            raise ValueError("Post code can't be empty")

        city_post_code = str(city_post_code)
        response = self.get_quarters()
        sought_quarters = []

        if response['data']:
            all_quarters = response['data']['response']['cities_quarters']['e']
            if isinstance(all_quarters, dict):
                if all_quarters['city_post_code'] == city_post_code:
                    sought_quarters = [all_quarters]
            else:
                sought_quarters = [quarter
                                   for quarter in all_quarters
                                   if quarter['city_post_code'] == city_post_code]
            response['data'] = {'quarters': sought_quarters}
        return response

    def get_regions(self):
        '''
        Description:
        ------------
        The method sends an XML request to the server
        to get information about all the regions in all cities

        Parameter:
        ----------
        :param None

        Returns:
        --------
        :return python dictionary received from Econt's server with
        info about regions
        '''
        logger.info('Calling get_regions')

        return self.__build_request(RequestType.REGIONS, authenticate=True)

    def get_zones(self):
        '''
        Description:
        ------------
        The method sends an XML request to the server
        to get information about all the zones in all cities

        Parameter:
        ----------
        :param: None

        Returns:
        --------
        :return: python dictionary received from Econt's server with
        info about zones
        '''
        logger.info('Calling get_zones')

        return self.__build_request(RequestType.ZONES, authenticate=True)

    def __build_shipment(self, sender_data, receiver_data,
                         shipment_data, services_data,
                         payment_data, instructions_data,
                         validate=False,
                         only_calculate=False,
                         process_all_parcels=False, error_email=''):
        '''
        Description:
        ------------

        The method sends an XML request to Econt to get information
        to generate a shipment. You can set validate / only_calculate
        to true if you only want to
        ensure that your data is correct/ calculate the price of your cargo.
        Otherwise the shipment will be processed.
        error_email can be used to send any errors to the given email address.
        process_all_parcels - in case of multiple parcels :
        if FALSE : if there is an error, NO shipments are generated
        if TRUE : if there is an error, only the correct shipments are generated


        Parameters:
        -----------
        
        :param sender_data: json
        :param receiver_data: json
        :param shipment_data: json
        :param services_data: json
        :param payment_data: json
        :param instructions_data: json
        :param validate: bool
        :param only_calculate: bool
        :param process_all_parcels: bool
        :param error_email: string


        Returns:
        --------

        :return: python dictionary with status, message and data,
        where data contains information about your shipment
        '''
        logger.info('Calling __build_shipment')

        if payment_data['side'] == 'SENDER':  # GET
            add_attribute(dicttoxml.dicttoxml(payment_data), 'cd', 'type', 'GET')
        else:  # GIVE
            add_attribute(dicttoxml.dicttoxml(payment_data), 'cd', 'type', 'GIVE')

        data = {'system': {'response_type': 'XML',
                           'validate': int(validate),
                           'only_calculate': int(only_calculate),
                           'process_all_parcels': int(process_all_parcels),
                           'email_errors_to': error_email
                           },
                'request_type': RequestType.SHIPPING,
                'loadings': {'row':
                                    {'sender': sender_data,
                                     'receiver': receiver_data,
                                     'shipment': shipment_data,
                                     'services': services_data,
                                     'payment': payment_data,
                                     'instructions': instructions_data
                                     }
                             }
                }
        response = self.request(url=self.parcels_url,
                                xml=self.xml_builder(data=data,
                                                     root_element='parcels',
                                                     authenticate=True))
        if response['data']:
                if error_email and 'message' in response['data']['response']['result']:
                    response['message'] = response['data']['response']['result']['message']
                    response['data'] = None
                    response['status'] = StatusCode.ECONT_API_XML_ERROR
                else:
                    result_info = response['data']['response']['result']['e']
                    pdf_info = None
                    # before we used to find Errors using API_ERR
                    # but now in the demo ver, they are returned
                    # in a different way
                    if result_info['error']:
                        response['message'] = result_info['error']
                        response['status'] = StatusCode.ECONT_API_XML_ERROR
                        response['data']= None
                    else:
                        del result_info['error']
                        del result_info['error_code']
                        if not validate and not only_calculate:
                            pdf_info = response['data']['response']['pdf']
                        response['data'] = {'result': result_info,
                                            'pdf': pdf_info}
        logger.debug('_build_shipment returned {}'.format(response))
        return response

    def create_shipment(self, sender_data, receiver_data,
                        shipment_data, services_data,
                        payment_data, instructions_data, error_email=''):
        '''
        Description:
        ------------

        The method sends an XML request to Econt to get information
        to generate a shipment.


        Parameters:
        -----------

        :param sender_data: json
        :param receiver_data: json
        :param shipment_data: json
        :param services_data: json
        :param payment_data: json
        :param instructions_data: json
        :param error_email: string


        Returns:
        --------

        :return: python dictionary with status, message and data,
        where data contains information about your shipment
        '''
        logger.info('Calling create_shipment')

        return self.__build_shipment(sender_data, receiver_data,
                                     shipment_data, services_data,
                                     payment_data, instructions_data,
                                     error_email=error_email)

    def calculate_shipment_price(self, sender_data, receiver_data,
                                 shipment_data, services_data,
                                 payment_data, instructions_data,
                                 error_email=''):
        '''
        Description:
        ------------

        The method sends an XML request to Econt to calculate
        the price of a shipment.


        Parameters:
        -----------

        :param sender_data: json
        :param receiver_data: json
        :param shipment_data: json
        :param services_data: json
        :param payment_data: json
        :param instructions_data: json
        :param error_email: string


        Returns:
        --------

        :return: python dictionary with status, message and data,
        where data contains information about your shipment
        '''
        logger.info('Calling calculate_shipment_price')

        return self.__build_shipment(sender_data, receiver_data,
                                     shipment_data, services_data,
                                     payment_data, instructions_data,
                                     only_calculate=True,
                                     error_email=error_email)

    def validate_shipment(self, sender_data, receiver_data,
                          shipment_data, services_data,
                          payment_data, instructions_data, error_email=''):
        '''
        Description:
        ------------

        The method sends an XML request to Econt to ensure
        that data of your shipment is correct.


        Parameters:
        -----------

        :param sender_data: json
        :param receiver_data: json
        :param shipment_data: json
        :param services_data: json
        :param payment_data: json
        :param instructions_data: json
        :param error_email: string


        Returns:
        --------

        :return: python dictionary with status, message and data,
        where data contains information about your shipment
        '''
        logger.info('Calling validate_shipment')

        return self.__build_shipment(sender_data, receiver_data,
                                     shipment_data, services_data,
                                     payment_data, instructions_data,
                                     validate=True, error_email=error_email)

    def get_clients(self):
        '''
        Description:
        ------------
        The method sends an XML request to the server
        to get information about the clients of the user

        Parameter:
        ----------
        :param: None

        Returns:
        --------
        :return: python dictionary received from Econt's server with
        status, message and data as keys
        where data holds the info about the clients
        '''
        logger.info('Calling get_clients')

        response = self.__build_request(RequestType.ACCESS_CLIENTS,authenticate=True)
        if response['data']:
            response['data'] = response['data']['response']
        return response

    def validate_cd_agreement(self, name, cd_no):
        '''
        Description:
        ------------
        The method creates an XML request to see whether the user's
        agreement for Punitive Decree is valid or not.

        Parameter:
        ----------
        :param: name : str
        :param: cd_no : str
        info about the validity in the data key.
        '''
        logger.info('Calling validate_cd_agreement')
        logger.debug('In validate_cd_agreement with name {} and cd_no {}'.format(name,
                                                                                 cd_no))

        data = {
            'request_type': RequestType.CD_AGREEMENT,
            'client_name': name,
            'cd_agreement': cd_no
        }
        response = self.request(url=self.service_url,
                                xml=self.xml_builder(data=data,
                                                     authenticate=True))
        if response['data']:
            response['data'] = {'is_valid': response['data']['response']['is_valid']}
        return response

    def get_postboxes(self, city_name='', quarter_name=''):
        '''
        Description:
        ------------
        The method sends an XML request to the server to get information
        about all the postboxes and optionally filters the response according
        to the given city_name and quarter_name arguments

        Parameter:
        ----------
        :param: city_name : (optional) str
        :param: quarter_name : (optional) str

        Returns:
        --------
        :return: python dictionary received from Econt's server with        
        info about postboxes
        '''
        logger.info('Calling get_postboxes')
        logger.debug('In get_postboxes with city {} and quarter {}'.format(city_name,
                                                                           quarter_name))

        if quarter_name and not city_name:
            raise ValueError('You must supply city name to'
                             ' perform this search!')
        else:
            data = {
                'request_type': RequestType.POSTBOXES,
                'post_boxes': {
                    'e': {
                        'city_name': city_name,
                        'quarter_name': quarter_name
                    }
                }
            }
            response = self.request(url=self.service_url,
                                    xml=self.xml_builder(data=data,
                                                         authenticate=True))
            response['data'] = {
                'post_boxes':
                    response['data']['response']['post_boxes']['e']
            }
            return response

    def retrieve_shipment_info(self, shipment_ids, full_tracking=False):
        '''
        Description:
        ------------
        The method sends an XML request to Econt to get info
        about shipments using shipment_numbers.

        Parameter:
        ----------
        :param shipment_ids : list
        :param full_tracking: boolean

        Returns:
        --------
        :return python dictionary with status, message and data,
        where data contains a list of the shipments
        '''
        logger.info('Calling retrieve_shipment')
        logger.debug('In retrieve_shipment with shipment ids {}'.format(shipment_ids))

        data = {'request_type': RequestType.SHIPMENTS,
                RequestType.SHIPMENTS: shipment_ids}
        data.update(self.get_user_credentials())

        xml = dicttoxml.dicttoxml(data, custom_root='request',
                                  attr_type=False, item_func=lambda x: 'num')

        if full_tracking:
            xml = add_attribute(xml,'shipments','full_tracking','ON')
        response = self.request(url=self.service_url, xml=xml)
        if response['data']:
            # {'shipments' : [...]} as a result
            ships = response['data']['response']['shipments']['e']
            if len(shipment_ids) == 1:
                ships = [ships]
            response['data'] = {'shipments': ships}
        return response

    def get_post_tariff(self):
        '''
        Description:
        ------------
        The method sends an XML request to Econt to get info
        about the current post tariff.

        The method causes errors when using the ECONT_SERVICE_DEMO_URL
        and returns the desired information only when using the
        ECONT_SERVICE_URL. Hence, we use ECONT_SERVICE_URL here.

        Parameter:
        ----------
        :param: None

        Returns:
        --------
        :return python dictionary with status, message and data,
        where data contains a dict with the post tariff info.
        '''
        logger.info('Calling get_post_tariff')

        return self.request(url=ECONT_SERVICE_URL,
                            xml=self.xml_builder(
                                data={'request_type': RequestType.POST_TARIFF},
                                authenticate=True))

    def get_delivery_days(self, date):
        '''
         Description:
         ------------
         The method sends an XML request to Econt to get info
         about the delivery days for the given date.

         Parameter:
         ----------
         :param date: string in YYYY-MM-DD Format

         Returns:
         --------
         :return python dictionary with status, message and data,
         where data contains a dict with delivery date info in a list.
         '''
        logger.info('Calling get_delivery_days')
        logger.debug('In get_delivery_days with date {}'.format(date))

        validate_date(date)
        response = self.request(url=self.service_url,
                                xml=self.xml_builder(data={'request_type': RequestType.DELIVERY_DAYS,
                                                           'delivery_days': date,
                                                           'system': {'response_type': 'XML'}},
                                                     authenticate=True))
        if response['data']:
            if response['data']['response']['delivery_days']:
                days_list = response['data']['response']['delivery_days']['e']
                result = []
                if isinstance(days_list, list):
                    for day_dict in days_list:
                        for key, value in day_dict.items():
                            result.append(value)
                else:
                    result.append(days_list['date'])
                response['data'] = {'delivery_days': result}
            else:
                response['data'] = {'delivery_days': [next_working_day(date)]}
        return response


if __name__ == '__main__':
    import doctest
    doctest.testmod()
