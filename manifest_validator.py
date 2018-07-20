url = ["https://ccr.linear-nat-pil-red.xcr.comcast.net/ZEETV_HD_NAT_25372_0_5671566327352803163.m3u8","https://ccr.linear-nat-pil-red.xcr.comcast.net/WLLWD_HD_NAT_25076_0_9020662125201164163.m3u8"]


#https://stackoverflow.com/questions/10588644/how-can-i-see-the-entire-http-request-thats-being-sent-by-my-python-application
#http://zetcode.com/web/pythonrequests/
#http://docs.python-requests.org/en/master/api/
#https://stackoverflow.com/questions/2785755/how-to-split-but-ignore-separators-in-quoted-strings-in-python
#https://github.com/globocom/m3u8
#https://www.quora.com/How-do-I-convert-list-of-key-value-values-to-dictionary-in-Python

import requests
import json
import re

def attribute_spliter(data):
    """
    Method to filter and split the attributes infor from Stream-Info,I-FRAME section
    :param data: attributes info of Stream-Info,I-FRAME section
    :return: Splitted string within the list ['codecs':'88888',...]
    """
    #data = """BANDWIDTH=689200,PROGRAM-ID=1,CODECS="avc1.4d4015,mp4a.40.5",RESOLUTION=512x288"""
    pattern = re.compile(r'''((?:[^,"']|"[^"]*"|'[^']*')+)''')
    return pattern.split(data)[1::2]

def url_requester(method=None,url=None,data=None,header=None):
    """
    Method to perform HTTP operations and response fetching
    :param method: Manifest URL/URI supported http request method(GET,PUT,POST,DELETE,HEAD,OPTIONS,PATCH)
    :param url: Manifest URL/URI of the asset/tv entity requested
    :param data: Applicable only POST,PUT,PATCH http method API's
    :param header: http request/response headers pass if any
    :return: http_status_code,response_content,error_message if available
    """
    status_code = 500
    error_msg = None
    response_data = None

    try:
        req = requests.request(method=method,url=url,data=data,headers=header)
        # print req.request.method #Getting the method
    except (requests.RequestException,requests.HTTPError,requests.ConnectionError,requests.Timeout) as e:
        error_msg = 'Connection error: {}'.format(e)
    except Exception as e:
        error_msg = 'Connection error: {}'.format(e)

    else:
        status_code = req.status_code
        response_data = req.content

    return status_code, response_data, error_msg

def asset_identifier_channel_retriever(manifest_url):
    """
    Method to frame the asset_identifier and channel info from the Manifest URL/URI provided
    :param manifest_url: Manifest URL/URI of the asset/tv entity requested
    :return: Identifier for the asset manifest requested,channel name
    """
    asset_identifier = None
    channel = None

    if manifest_url.endswith('.m3u8'):
        asset_identifier = manifest_url.split('.m3u8')[0].split('/')[-1]
        channel = manifest_url.split('.m3u8')[0].split('/')[-1].split('_')[0]

    return asset_identifier,channel

def get_host_url(manifest_url):
    """
    Method to frame the host_url from the Manifest URL/URI provided
    :param manifest_url: Manifest URL/URI of the asset/tv entity requested
    :return: hosturl (e.g. https://ccr.linear-nat-pil-red.xcr.comcast.net)
    """
    host_url = None
    if manifest_url.endswith('.m3u8'):
        host_url_split = manifest_url.split('/')
        host_url = '{}//{}/'.format(host_url_split[0],host_url_split[2])
    return host_url

def parent_manifest_url_loader_response_retrieve(http_request_method,manifest_url_list):
    """
    Method to send the manifest response for the asset/uri requested,retrieve response and parse the parameters
    :param http_request_method: Manifest URL/URI supported http request method(GET,PUT,POST,DELETE,HEAD,OPTIONS,PATCH)
    :param manifest_url_list: Manifest URL/URI in list data type/data structure
    :return: list of dicts i.e. set of parsed manifest response parameters enclosed with a dict and wrapped in a list
    """
    bulk_manifest_holder = []
    if len(manifest_url_list)!=0:
        for manifest_url in manifest_url_list:
            print(manifest_url)
            asset_identifier, channel = asset_identifier_channel_retriever(manifest_url)
            host_url_retrieve = get_host_url(manifest_url)

            if not manifest_url.endswith(".m3u8"):
                print("Manifest URL provided not ended with .m3u8!!!! Please provide valid asset url with .m3u8 extension")
            else:
                print("Manifest URL ends with .m3u8 extension")
                status_code, response_data, error_msg = url_requester(http_request_method, manifest_url)

                if status_code == 200:
                    stream_inf_holder = []
                    stream_iframe_holder = []
                    playlist_uri_holder = []
                    manifest_metadata_holder = {}
                    if response_data is not None:
                        print(response_data)
                        for line in response_data.split('\n'):
                            if '#EXTM3U' in line:
                                manifest_metadata_holder['EXTM3U'] = 'available'

                            if '#EXT-X-VERSION' in line:
                                manifest_metadata_holder['EXT-X-VERSION'] = line.split(':')[1]

                            if '#EXT-X-FAXS-CM' in line:
                                if line.split(':')[1]!='' or line.split(':')[1] is not None:
                                    manifest_metadata_holder['EXT-X-FAXS-CM'] = "encrypted"

                            if '#EXT-X-XCAL-CONTENTMETADATA' in line:
                                if line.split(':')[1]!='' or line.split(':')[1] is not None:
                                    manifest_metadata_holder['EXT-X-XCAL-CONTENTMETADATA'] = "available"

                            if 'EXT-X-STREAM-INF' in line:
                                stream_metadata = line.split(':')[1]
                                for stream_inf_line in stream_metadata.split('\n'):
                                    attr = attribute_spliter(stream_inf_line)
                                    stream_dict = {k: v for k, v in (x.split('=') for x in attr)} #Parsing the stream_info informations like codecs,bandwith,resolution,etc...
                                    stream_inf_holder.append(stream_dict)

                                if stream_inf_holder!=[]:
                                    manifest_metadata_holder['stream_info'] = stream_inf_holder
                                else:
                                    manifest_metadata_holder['stream_info'] = []

                            if '#EXT-X-I-FRAME-STREAM-INF' in line:
                                stream_iframe_metadata = line.split(':')[1]
                                for stream_iframe_info_line in stream_iframe_metadata.split('\n'):
                                    attr = attribute_spliter(stream_iframe_info_line)
                                    stream_iframe_dict = {k: v for k, v in (x.split('=') for x in attr)}
                                    stream_iframe_holder.append(stream_iframe_dict)

                                if stream_iframe_holder != []:
                                    manifest_metadata_holder['iframe_info'] = stream_iframe_holder
                                else:
                                    manifest_metadata_holder['iframe_info'] = []

                            if line.endswith('.m3u8'):
                                playlist_uri_holder.append(str(host_url_retrieve)+ line)

                                if playlist_uri_holder != []:
                                    manifest_metadata_holder['playlist_uri'] = playlist_uri_holder
                                else:
                                    manifest_metadata_holder['playlist_uri'] = []

                    bulk_manifest_holder.append({asset_identifier:manifest_metadata_holder})

    else:
        print('Please provide the manifest_url_list and manifest_url_list is {}'.format(len(manifest_url_list)))

    return json.dumps(bulk_manifest_holder)

manifest_metadata_holder = parent_manifest_url_loader_response_retrieve('GET',url)
print manifest_metadata_holder