# -*- coding: utf-8 -*-
import base64
from urllib.parse import quote, urlencode, urljoin
import requests
import json
import time


class QimaiEncryptor(object):

    def __init__(self, uri):
        self.uri = uri

    @staticmethod
    def encrypt_raw_str(raw_str):
        key = "00000008d78d46a"
        key_len = len(key)
        res = []
        for i in range(len(raw_str)):
            # 两个字符的ASCII码取异或再转为字节
            code1 = ord(raw_str[i])
            code2 = ord(key[(i + 10) % key_len])
            res.append(chr(code1 ^ code2))
        return "".join(res)

    def get_analysis(self, params, uri=None):
        if isinstance(params, str):
            part1 = params.encode()
        elif isinstance(params, bytes):
            part1 = params
        else:
            params = params.copy()
            for key, value in params.items():
                if isinstance(value, bytes):
                    value =  value.decode()
            part1 = "".join(sorted(params.values()))
            part1 = quote(part1).encode()
        part1 = base64.b64encode(part1).decode()

        part2 = uri if uri is not None else self.uri
        if part2 is None:
            part2 = ""

        part3 = str(int(time.time() * 1000) - 1515125653845)

        # 拼接后加密，再BASE64编码
        raw_str = "@#".join([part1, part2, part3, "1"])
        encrypted_str = self.encrypt_raw_str(raw_str).encode()
        encrypted_str = base64.b64encode(encrypted_str).decode()
        return encrypted_str

    def __call__(self, *args, **kwargs):
        return self.get_analysis(*args, **kwargs)
