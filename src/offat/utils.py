"""
utils module
"""
from json import loads as json_load, dumps as json_dumps, JSONDecodeError
from re import compile as re_compile, match
from urllib.parse import urlparse, urljoin
from os.path import isfile
from importlib.metadata import version
from yaml import safe_load, YAMLError

from .logger import logger


def get_package_version():
    '''Returns package current version

    Args:
        None

    Returns:
        String: current package version
    '''
    return version('offat')


def read_yaml(file_path: str) -> dict:
    '''Reads YAML file and returns as python dict.
    returns file not found or yaml errors as dict.

    Args:
        file_path (str): path of yaml file

    Returns:
        dict: YAML contents as dict else returns error
    '''
    if not file_path:
        return {'error': 'ValueError, path cannot be of None type'}

    if not isfile(file_path):
        return {'error': 'File Not Found'}

    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            return safe_load(f.read())
        except YAMLError:
            return {'error': 'YAML error'}


def read_json(file_path: str) -> dict:
    '''Reads JSON file and returns as python dict.
    returns file not found or JSON errors as dict.

    Args:
        file_path (str): path of yaml file

    Returns:
        dict: YAML contents as dict else returns error
    '''
    if not isfile(file_path):
        return {'error': 'File Not Found'}

    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            return json_load(f.read())
        except JSONDecodeError:
            return {'error': 'JSON error'}


def read_openapi_file(file_path: str) -> dict:
    '''Returns Open API Documentation file contents as json
    returns file not found or yaml errors as dict.

    Args:
        file_path (str): path of openapi file

    Returns:
        dict: YAML contents as dict else returns error
    '''
    if not isfile(file_path):
        return {'error': 'File Not Found'}

    file_ext = file_path.split('.')[-1]
    match file_ext:
        case 'json':
            return read_json(file_path)
        case 'yaml':
            return read_yaml(file_path)
        case _:
            return {'error': 'Invalid file extension'}


def write_json_to_file(json_data: dict, file_path: str):
    '''Writes dict obj to file as json

    Args:
        json_data (dict): JSON payload to be written into file
        file_path (str): path of output json file

    Returns:
        bool: True is `json_data` is written into `file_path` else
        returns False (in case of any exception)

    Raises:
        Any exception occurred during operation
    '''
    if isfile(file_path):
        logger.info('%s file will be overwritten.', file_path)

    logger.info('Writing data to file: %s', file_path)
    try:
        with open(file_path, 'w') as f:
            f.write(json_dumps(json_data))
            logger.info('Completed writing data to file: %s', file_path)
            return True

    except JSONDecodeError:
        logger.error('Invalid JSON data, error while writing to %s file.', file_path)

    except Exception as e:
        logger.error(
            'Unable to write JSON data to file due to below exception:\n%s', repr(e)
        )

    return False


def str_to_dict(key_values: str) -> dict:
    '''Takes string object and converts to dict
    String should in `Key1:Value1,Key2:Value2,Key3:Value3` format

    Args:
        key_values (str): dict as str separated by commas `,`

    Returns:
        dict: Returns dict from str after conversion

    Raises:
        Any exception occurred during operation
    '''
    new_dict = dict()
    for key_value in key_values.split(','):
        try:
            key_value_list = key_value.split(':')
            key = key_value_list[0].strip()
            value = key_value_list[1].strip()
            new_dict[key] = value
        except (IndexError, KeyError) as e:
            logger.error(str(e))

    return new_dict


def headers_list_to_dict(headers_list_list: list[list[str]] | None) -> dict:
    '''Takes list object and converts to dict
    String should in `[['Key1:Value1'],['Key2:Value2'],['Key3:Value3']]` format

    Args:
        headers_list_list (list): headers value as list[list[str]], where str
        is in `key:value` format

    Returns:
        dict: Returns dict from str after conversion

    Raises:
        Any exception occurred during operation
    '''
    if not headers_list_list:
        return {}

    response_headers_dict: dict = dict()

    for header_list in headers_list_list:
        for header_data in header_list:
            header_key_value = header_data.split(':')
            k = header_key_value[0].strip()
            v = header_key_value[1].strip()
            response_headers_dict[k] = v

    return response_headers_dict


def is_valid_url(url: str) -> bool:
    '''Accepts string as an parameter and returns bool
    whether str is url or not

    Args:
        url (str): string value which could be url

    Returns:
        bool: Returns True str is url else False

    Raises:
        Any exception occurred during operation
    '''
    url_regex = re_compile(
        r'https?:\/\/([a-z.-]|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})+(:\d+)?.*'
    )
    return bool(match(url_regex, url))


def parse_server_url(url: str) -> tuple:
    '''Parses url and returns scheme, host, port and basepath.

    Args:
        url (str): url to be parsed

    Returns:
        tuple: (scheme:str, host:str, port:int|None, basepath:str|None)

    Raises:
        Any exception occurred during operation
    '''
    # TODO: implement url parse security https://docs.python.org/3/library/urllib.parse.html#url-parsing-security
    parsed_url = urlparse(url)

    netloc = parsed_url.netloc
    port = 443 if parsed_url.scheme == 'https' else 80
    if ':' in netloc:
        tokens = netloc.split(':')
        host = tokens[0]
        try:
            port = int(tokens[1])
        except ValueError:
            logger.error(
                'Invalid Port Number: failed to parse port in url. Using port %d according to scheme %s',
                port,
                parsed_url.scheme,
            )
    else:
        host = netloc

    if parsed_url.scheme not in ['http', 'https']:
        raise ValueError('only http and https schemes are allowed')

    return parsed_url.scheme, host, port, parsed_url.path


def join_uri_path(*args: str, remove_prefix: str = '/') -> str:
    '''constructs url from passed args using urljoin

    Args:
        *args (str): parts of uri
        remove_prefix (str): prefix to be removed from uri path before
        joining with previous uri path.

    Returns:
        str: constructed uri

    Raises:
        Any exception occurred during operation

    Example:
    ```python
    from offat.utils import join_uri_path

    url = join_uri_path('https://example.com:443','/v2/', '/pet/findByStatus/')
    print(url)
    # output: https://example.com:443/pet/findByStatus/
    ```
    '''
    url = args[0]
    if not url.endswith('/'):
        url += '/'

    for uri in args[1:]:
        if not url.endswith('/'):
            url += '/'
        url = urljoin(url, uri.removeprefix(remove_prefix))

    return url
