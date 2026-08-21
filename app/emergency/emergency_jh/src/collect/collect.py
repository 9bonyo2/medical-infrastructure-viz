import os
import json
import requests
import pandas as pd
from emergency.emergency_jh.src.preprocess.preprocess import(
    to_csv_doctor,
    to_csv_emergency,
    to_csv_population,
    to_csv_time
)

# 2015 ~ 2024 응급의료기관 API 호출
def get_emergency(api_key, year):
    url = "https://kosis.kr/openapi/Param/statisticsParameterData.do"

    params = {
        "method": "getList",
        "apiKey": api_key,
        "itmId": "B411+",
        "objL1": "ALL",
        "objL2": "ALL",
        "objL3": "",
        "objL4": "",
        "objL5": "",
        "objL6": "",
        "objL7": "",
        "objL8": "",
        "format": "json",
        "jsonVD": "Y",
        "prdSe": "Y",
        "startPrdDe": year,
        "endPrdDe": year,
        "orgId": "411",
        "tblId": "DT_41104_411"
    }

    res = requests.get(url, params=params)

    if not res.ok:
        print(f'error: {res.status_code}')
        return

    data = res.json()
    df = pd.DataFrame(data)

    to_csv_emergency(df, year)

def get_population(api_key, year):
    url = "https://kosis.kr/openapi/Param/statisticsParameterData.do"

    params = {
        "method": "getList",
        "apiKey": api_key,
        "itmId": "T00+",
        "objL1": "00+11+21+22+23+24+25+26+29+31+32+33+34+35+36+37+38+39+",
        "objL2": "ALL",
        "objL3": "",
        "objL4": "",
        "objL5": "",
        "objL6": "",
        "objL7": "",
        "objL8": "",
        "format": "json",
        "jsonVD": "Y",
        "prdSe": "Y",
        "startPrdDe": year,
        "endPrdDe": year,
        "orgId": "101",
        "tblId": "INH_1IN1503_01"
    }

    res = requests.get(url, params=params)

    if not res.ok:
        print(f'error: {res.status_code}')
        return

    data = res.json()
    df = pd.DataFrame(data)

    to_csv_population(df, year)

def get_doctor(api_key, year):
    url = "https://kosis.kr/openapi/Param/statisticsParameterData.do"

    params = {
        "method": "getList",
        "apiKey": api_key,
        "itmId": "B431+",
        "objL1": "ALL",
        "objL2": "ALL",
        "objL3": "",
        "objL4": "",
        "objL5": "",
        "objL6": "",
        "objL7": "",
        "objL8": "",
        "format": "json",
        "jsonVD": "Y",
        "prdSe": "Y",
        "startPrdDe": year,
        "endPrdDe": year,
        "orgId": "411",
        "tblId": "DT_41104_431"
    }

    res = requests.get(url, params=params)

    if not res.ok:
        print(f'error: {res.status_code}')
        return

    data = res.json()
    df = pd.DataFrame(data)

    to_csv_doctor(df, year)

def get_time(api_key, year):
    url = "https://kosis.kr/openapi/Param/statisticsParameterData.do"

    params = {
        "method": "getList",
        "apiKey": api_key,
        "itmId": "B151+",
        "objL1": "ALL",
        "objL2": "ALL",
        "objL3": "",
        "objL4": "",
        "objL5": "",
        "objL6": "",
        "objL7": "",
        "objL8": "",
        "format": "json",
        "jsonVD": "Y",
        "prdSe": "Y",
        "startPrdDe": year,
        "endPrdDe": year,
        "orgId": "411",
        "tblId": "DT_41104_151"
    }

    res = requests.get(url, params=params)

    if not res.ok:
        print(f'error: {res.status_code}')
        return

    data = res.json()
    df = pd.DataFrame(data)

    to_csv_time(df, year)