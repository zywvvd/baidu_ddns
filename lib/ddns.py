import hmac
import time
import requests 
import urllib.parse
from mtutils import json_load
import socket
import json
import re


class DDNS:    
    IP_TYPE = ['ipv4', 'ipv6']
    def __init__(self, url, AK, SK):
        self.url=url
        self.AK=AK
        self.SK=SK

    @classmethod
    def from_cofig(cls, config_json_path):
        config_info = json_load(config_json_path)
        url = config_info['url']
        assert url != "", f"请在assets / config.json 中配置 url"
        AK = config_info['AK']
        assert AK != "", f"请在assets / config.json 中配置 AK"
        SK = config_info['SK']
        assert SK != "", f"请在assets / config.json 中配置 SK"
        return cls(url, AK, SK)

    def getTime(self):#获取网络时间戳，用于鉴权
        url="http://api.m.taobao.com/rest/api3.do?api=mtop.common.getTimestamp"
        res=requests.get(url,timeout=5).text
        res=json.loads(res)["data"]["t"]
        return int(res)/1000

    def getIP(self, ip_type):#获取本地公网IP
        assert ip_type in self.IP_TYPE
        if ip_type == 'ipv4':
        
            url="http://pv.sohu.com/cityjson?ie=utf-8"
            res=requests.get(url,timeout=5).text
            res=res.split("=")[1].split(";")[0] #转换javascript为json格式
            res=json.loads(res)
            res=res["cip"]

        elif ip_type == 'ipv6':
            url="https://ipv6.ipw.cn/"
            res=requests.get(url,timeout=5).text
        else:
            raise RuntimeError(f"unknown ip type {ip_type}")
        return res.upper()

    def enc(self,key,message):
        h=hmac.new(key,message,digestmod="SHA256")
        return h.hexdigest()

    def post(self,URI,_data):
        #填写参数
        #获取UTC时间
        utc = time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(self.getTime()))
        #POST字典1
        data=json.dumps(_data)
        #创建请求header字典
        _headers={
            "host":"bcd.baidubce.com",
            "x-bce-date":utc,
            "Content-Type":"application/json;charset=utf-8",
            "Content-Length":str(len(data))
        }
        #格式化字典为http头标准格式
        headers=""
        for a,b in _headers.items():
            headers+=a+":"+b+"\r\n"
            
        #生成CanonicalHeaders
        method = "POST"
        CanonicalQueryString=""
        CanonicalURI = urllib.parse.quote(URI)  
        result = []
        for key,value in _headers.items():
            tempStr = str(urllib.parse.quote(key.lower(),safe="")) + ":" + str(urllib.parse.quote(value,safe=""))
            result.append(tempStr)
        result.sort()
        CanonicalHeaders = "\n".join(result)
        #拼接得到CanonicalRequest
        CanonicalRequest = method + "\n" + CanonicalURI + "\n" + CanonicalQueryString +"\n" + CanonicalHeaders
        #计算signingKey
        signingKey=self.enc(self.SK.encode(),b"bce-auth-v1/%b/%b/1800"%(self.AK.encode(),utc.encode()))
        #计算signature
        signature=self.enc(signingKey.encode(),CanonicalRequest.encode())
        #生成认证Authorization
        Authorization="bce-auth-v1/%s/%s/1800/content-length;content-type;host;x-bce-date/%s"%(self.AK,utc,signature)
        
        #最后生成完整的http请求
        http="POST %s HTTP/1.1\r\n%sAuthorization:%s\r\n\r\n"%(URI,headers,Authorization)+data

        #建立socket链接,发送http数据
        s=socket.socket()
        s.connect(("bcd.baidubce.com",80))
        s.send(http.encode())
        res=b"" 
        while True:
            _res=s.recv(10240)
            res+=_res
            if b"chunked" not in res: #如果不是chunked，一次性读完退出
                break
            if _res[-5:]==b"0\r\n\r\n": #chunked标志，连续读取到标识符退出
                break
        s.close()
        return res
    
    def get_domain_info(self, domain):
        data={
            'domain':self.url,
            'pageNo':1,
            'pageSize':100
            }
        url="/v1/domain/resolve/list"
        res=self.post(url,data)
        decoded_res = res.decode()
        
        json_part = decoded_res[decoded_res.find('\r\n{') + 2: decoded_res.find('}\r\n') + 1]
        clean_json_part = json_part.replace('\r', '').replace('\n', '')

        pattern = r'{"recordId":[^"]+,"domain":"' + domain + r'","view":"[^"]+","rdtype":"[^"]+","ttl":[^"]+,"rdata":"[^"]+","zoneName":"[^"]+","status":"[^"]+"}'
        searchObj = re.search(pattern, clean_json_part, flags=0)
        assert searchObj is not None, f"get_domain_info failed"

        domain_str = clean_json_part[searchObj.span()[0]:searchObj.span()[1]]

        domain_info = json.loads(domain_str)
      
        return domain_info
    
    def SET(self, domain, ip_type, logger):
        assert ip_type in self.IP_TYPE
        logger("ddns ready to update data. ")

        # ip
        try:
            local_ip = self.getIP(ip_type)
            logger(f"get local IP: {local_ip}")
        except Exception as e:
            logger(f"get local IP failed, exception {e}")
            return False

        # rdtype
        if ip_type == 'ipv4':
            rd_type = 'A'
        elif ip_type == 'ipv6':
            rd_type = 'AAAA'
        else:
            raise RuntimeError(f"unknown ip_type {ip_type}")
        logger(f"ip type {rd_type}")

        # record
        try:
            domain_info=self.get_domain_info(domain)
            logger(f"get domain info: {domain_info}")
            dns_ip = domain_info['rdata'].upper()
            recordId = domain_info['recordId']
        except Exception as e:
            logger(f"get domain_info failed, exception {e}")
            return False

        if local_ip!=dns_ip:
            logger(f"local IP changed, a update will be launched.")
            url="/v1/domain/resolve/edit"
            data={
                    "domain" : domain,
                    "rdType" : rd_type,
                    "rdata" : local_ip,
                    "ttl" : 60,
                    "zoneName" : self.url,
                    "recordId" : recordId
                }
        
            res=self.post(url, data)
            res_str = res.decode()
            split_lit = res_str.split(' ')
            if int(split_lit[1]) != 200:
                logger(f"DDNS update failed, error code {split_lit[1]}")
                logger(f"http responce: {res_str}")
            else:
                logger("DDNS update successfully !!!")
        else:
            logger("local IP is same as reomte IP, skip updating.")
