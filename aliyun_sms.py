import uuid
import datetime
import hmac
import base64
import requests
from urllib.parse import urlencode, quote

class AliyunSMS(object):
    def __init__(self, app):
        self.app = app
        self.format = app.config.get("ALIYUN_API_FORMAT") or "JSON"
        self.version = "2016-09-27"
        self.key = app.config["ALIYUN_API_KEY"]
        self.secret = app.config["ALIYUN_API_SECRET"]
        self.signature = ""
        self.signature_method = "HMAC-SHA1"
        self.signature_version = "1.0"
        self.signature_nonce = str(uuid.uuid4())
        self.timestamp = datetime.datetime.utcnow().isoformat("T")
        self.region_id = app.config["ALIYUN_API_REGION_ID"]

        self.gateway = app.config["ALISMS_GATEWAY"]
        self.action = ""
        self.sign = ""
        self.template = ""
        self.params = {}
        self.phones = []

    def send_single(self, phone, sign, template, params):
        self.action = "SingleSendSms"
        self.phones.append(phone)
        self.sign = sign
        self.params = params
        self.template = template

        query_string = self.build_query_string()
        resp = requests.get(self.gateway + "?" + query_string).json()
        model = resp.get("Model")
        if model is not None:
            return True

        self.app.logger.info("send sms to %s failed, reason: %s" % (self.phones[0], resp.get("Message")))
        return False

    def build_query_string(self):
        query = []
        query.append(("Format", self.format))
        query.append(("Version", self.version))
        query.append(("AccessKeyId", self.key))
        query.append(("SignatureMethod", self.signature_method))
        query.append(("SignatureVersion", self.signature_version))
        query.append(("SignatureNonce", self.signature_nonce))
        query.append(("Timestamp", self.timestamp))
        query.append(("RegionId", self.region_id))
        query.append(("Action", self.action))
        query.append(("SignName", self.sign))
        query.append(("TemplateCode", self.template))
        query.append(("RecNum", ",".join(self.phones)))
        params = "{"
        for param in self.params:
            params += "\"" + param + "\"" + ":" + "\"" + str(self.params[param]) + "\"" + ","
        params = params[:-1] + "}"
        query.append(("ParamString", params))
        query = sorted(query, key=lambda key: key[0])
        query_string = ""
        for item in query:
            query_string += quote(item[0], safe="~") + "=" + quote(item[1], safe="~") + "&"
        query_string = query_string[:-1]
        tosign = "GET&%2F&" + quote(query_string, safe="~")
        secret = self.secret + "&"
        hmb = hmac.new(secret.encode("utf-8"), tosign.encode("utf-8"), "sha1").digest()
        self.signature = quote(base64.standard_b64encode(hmb).decode("ascii"), safe="~")
        query_string += "&" + "Signature=" + self.signature
        return query_string