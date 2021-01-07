 # -*- coding:utf-8 -*-

import requests
#model name: pycryptodome
from Crypto.Cipher import AES
import base64
from Crypto.Util.Padding import pad
from bs4 import BeautifulSoup
import argparse

#Settings aera

#登陆模式
auth_mode = "PASSWORD"  #1:PASSWORD 2:COOKIES

#统一身份认证账号密码，仅在“PASSWORD”认证模式下需要
stu_id = ""
stu_passwd = ""

#app.nwu.edu.cn认证Cookies，仅在“COOKIES”认证模式下需要
#可以通过浏览器直接获取
stu_varify_cookies = {
    "UUkey":"",
    "eai-sess":""
    }

#调试信息开关
debug_mode = False

#是否在账号密码登陆成功后输出app.nwu.edu.cn认证Cookies（即“COOKIES”认证模式下输入参数）
is_print_cookies = False

#重试最大次数
retry_max = 3



# costum padding for AES-128 (16 byte) (useless)
def add_to_16(text):
    if len(text.encode('utf-8')) % 16:
        add = 16 - (len(text.encode('utf-8')) % 16)
    else:
        add = 0
    text = text + ('\0' * add)
    return text.encode('utf-8')

# costum padding for AES (useless)
def add_to_n(text):
    n = 64
    if len(text.encode('utf-8')) % n:
        add = n - (len(text.encode('utf-8')) % n)
    else:
        add = 0
    text = text + ('\0' * add)
    return text.encode('utf-8')

# AES-CBC-128 encrypt
def encrypt(text,key,iv):
    mode = AES.MODE_CBC
    #text = add_to_16(text)
    #print(text)
    cryptos = AES.new(key, mode, iv)
    #cipher_text = cryptos.encrypt(text)
    cipher_text = cryptos.encrypt(pad(text.encode('utf-8'), AES.block_size))
    res = base64.encodebytes(cipher_text).decode()
    res = res.replace("\n","")
    return res



# Login functions
def get_cookies(username='2015000001',password='123456abc'):
    #cookies_res = {}

    ncov_report_url = "https://app.nwu.edu.cn/site/ncov/dailyup"
    auth_server_url = "http://authserver.nwu.edu.cn"
    action_url = "http://authserver.nwu.edu.cn/authserver/login"
    app_uc_login_url = "https://app.nwu.edu.cn/uc/wap/login"
    app_cas_login_url = "https://app.nwu.edu.cn/a_nwu/api/sso/cas"

    headers = {
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36 Edg/83.0.478.58"
    }

    action_1 = requests.get(auth_server_url,headers=headers)
    cookies_init = requests.utils.dict_from_cookiejar(action_1.cookies)
    if debug_mode:
        print(cookies_init)
    doc = BeautifulSoup(action_1.text, 'html.parser')
    if debug_mode:
        print(doc.title)
    lt = doc.find('input',attrs={"name": "lt"})['value']
    execution = doc.find('input',attrs={"name": "execution"})['value']
    aes_key = doc.find_all('script')[1].string.split('"')[3].encode('utf-8')
    #print(aes_key)

    #return
    
    # encrypt passwd ans create params
    #aes_key = "6cYJKrJBZAQzCtr9".encode('utf-8')
    aes_iv = b"6cYJKrJBZAQzCtr9"
    #aes_random_fill = "6cYJKrJBZAQzCtr96cYJKrJBZAQzCtr96cYJKrJBZAQzCtr96cYJKrJBZAQzCtr9"
    aes_random_fill = "abcdefghijklmnopabcdefghijklmnopabcdefghijklmnopabcdefghijklmnop"
    salted_pwd = encrypt(aes_random_fill+password,aes_key,aes_iv)
    if debug_mode:
        print("Salt: "+aes_key.decode())
        print("Salted password: "+salted_pwd)
    
    #return
    params = {
        "username":username,
        "password":salted_pwd,
        #"rememberMe":"0",
        "lt":lt,
        "dllt":"userNamePasswordLogin",
        "execution":execution,
        "_eventId":"submit",
        "rmShown":"1"
    }

    if debug_mode:
        print(params)

    #return
    action_2 = requests.post(action_url,params=params,cookies=cookies_init,headers=headers,allow_redirects=False)
    #print(action_2.text)
    doc = BeautifulSoup(action_2.text, 'html.parser')
    fails = doc.find_all(attrs={"class":"auth_error"})
    fail_flag = 0
    if len(fails)>0:
        for i in fails:
            #print(i)
            if i['style']=="display:none;":
                pass
            else:
                print("登陆失败：",end="  ")
                print(i.text)
                fail_flag = 1
    if fail_flag==0:
        #print(action_2.text)
        print("账户密码登陆成功")
    else:
        #print("Terminated...")
        return {}

    cookies_action_2 = requests.utils.dict_from_cookiejar(action_2.cookies)
    if debug_mode:
        print(cookies_action_2)

    #Get UUID and eai-sess
    #finally return this cookies
    params = {
        "redirect":"https://app.nwu.edu.cn/site/ncov/dailyup"
    }
    action_3 = requests.get(app_uc_login_url,params=params,cookies=cookies_action_2,headers=headers,allow_redirects=False)
    cookies_action_3 = requests.utils.dict_from_cookiejar(action_3.cookies)
    if debug_mode or is_print_cookies:
        print("Cookies for app:",end="  ")
        print(cookies_action_3)

    #Login to app (CAS)
    cookies_tmp = dict(cookies_action_2 , **cookies_action_3)
    params = {
        "redirect":"https://app.nwu.edu.cn/site/ncov/dailyup&from=wap"
    }
    action_4 = requests.get(app_cas_login_url,params=params,cookies=cookies_tmp,headers=headers,allow_redirects=True)
    #cookies_action_4 = requests.utils.dict_from_cookiejar(action_4.cookies)
    #print(cookies_action_4)
    #print(action_4.content)

    return cookies_action_3

def sent_report(cookies):
    headers = {"Accept":"application/json, text/plain, */*","Content-Type":"application/x-www-form-urlencoded","X-Requested-With":"XMLHttpRequest"}
    # cookies = {"UUkey":"","eai-sess":""}
    params = {
        "sfzx":"1", #是否正常
        "tw":"1",   #体温（list）
        "area":"陕西省 西安市 长安区",
        "city":"西安市",
        "province":"陕西省",
        "address":"陕西省西安市长安区郭杜街道西北大学(长安校区)家属院21栋",
        "geo_api_info":'{"type":"complete","info":"SUCCESS","status":1,"$Da":"jsonp_687452_","position":{"Q":34.14218,"R":108.87518999999998,"lng":108.87519,"lat":34.14218},"message":"Get ipLocation success.Get address success.","location_type":"ip","accuracy":null,"isConverted":true,"addressComponent":{"citycode":"029","adcode":"610116","businessAreas":[],"neighborhoodType":"","neighborhood":"","building":"","buildingType":"","street":"文苑南路","streetNumber":"11号","country":"中国","province":"陕西省","city":"西安市","district":"长安区","township":"郭杜街道"},"formattedAddress":"陕西省西安市长安区郭杜街道西北大学(长安校区)家属院21栋","roads":[],"crosses":[],"pois":[]}',
        "sfcyglq":"0",  #是否隔离期
        "sfyzz":"0",    #是否有症状
        "qtqk":"",  #其他情况
        "ymtys":""  #？？？
    }
    res = requests.get("https://app.nwu.edu.cn/ncov/wap/open-report/save",headers=headers,cookies=cookies,params=params)
    #print(res.content.decode())
    json_res = res.json()
    print("填报返回结果："+json_res['m'])

    return json_res['m']


def main(username='',password=''):

    cookies_res = {}
    global retry_max

    if auth_mode=="PASSWORD":
        print("USE PASSWORD MODE")
        cookies_res = get_cookies(username=stu_id,password=stu_passwd)
    elif auth_mode=="COOKIES":
        print("USE COOKIES MODE")
        cookies_res = stu_varify_cookies
    else:
        print("Unknow auth mode")
        return
    
    if len(cookies_res)<=0:
        print("Terminated...")
        return
    else:
        res = sent_report(cookies=cookies_res)
        if res=="操作成功":
            print("\n[FINAL] 自动填报成功")
            return
        elif res=="您已上报过" or res=="未到上报时间":
            print("\n[FINAL] 还不用填报哦~")
            return
        else:
            if retry_max>0:
                print("Retry "+str(retry_max)+":")
                retry_max = retry_max-1
                main()
            else:
                print("\n[FINAL] 超过最大重试次数，填报失败！")



if __name__ == "__main__":
    
    #CLI
    parser = argparse.ArgumentParser(description='Auto report CLI')
    parser.add_argument('--cli', type=bool, default=False,help="")   #Is call by cli. If false, use settings at the begining of this file.
    parser.add_argument('--auth_mode', type=str, default="PASSWORD",help="")
    parser.add_argument('--username', type=str, default=None,help="")
    parser.add_argument('--password', type=str, default=None,help="")
    parser.add_argument('--eai-sess', type=str, default=None,help="")
    parser.add_argument('--UUkey', type=str, default=None,help="")
    args = parser.parse_args()
    #print("Inpute：", args)

    if args.cli==True:
        print("Load settings from CLI args...")
        auth_mode = args.auth_mode
        stu_id = args.username
        stu_passwd = args.password
        stu_varify_cookies['UUkey'] = args.UUkey
        stu_varify_cookies['eai-sess'] = args.eai_sess
    elif args.cli==False:
        print("Load Setting in file...")

    main()
    #get_cookies(stu_id,stu_passwd)
    #get_cookies()
