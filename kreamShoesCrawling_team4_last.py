#!/usr/bin/env python
# coding: utf-8


###########################################################################################
# 빅데이터컴퓨팅 중간고사 팀프로젝트
# 팀원 : 노상후(A64030), 김지윤(), 이종기
# 작성일 : 2022.04.11 ~
# 
# <Crawling Method List>
# 각 Method로 수집한 데이터는 아이템명으로 연계할 수 있고, 아이템명에 '/'가 들어간 경우 모두 '_'로 교체
# basicInfoCrawling : 검색결과 페이지에서 신발에 대한 기본정보를 수집함(아이템명, 브랜드명, 거래량) 
# detailDataCrawling : 선택된 단일 상품 상품 상세 페이지에서 체걸거래 이력, 판매입찰 이력, 구매입찰 이력을 추출하는 Method
# imgUrlCrawling : 검색결과 페이지에서 신발의 이미지 파일을 수집함(저장경로 : /shoesimgs, 파일명 : 신발이름.png)
# kreamCrawling : 상기 3개(basicInfoCrawling, detailDataCrawling, imgUrlCrawling) Crawling Method를 
#                 활용하여 데이터를 수집하고, 저장하는 Method
# dataClensing : 크롤링된 데이터의 EU 사이즈 데이터 제거 및 괄호제거 클렌징을 수행하고, 사이즈 그룹(A,B,C) 추가
#
#
# <Chart and Crawling Method List>
# showShoesImages : 수집된 신발 이미지를 차트 리스트 형태로 보여주는 Method
# selShoes : 차트에서 보여줄 신발을 선택받는 Method
# selShoesTwo : 차트에서 보여줄 신발을 2종 선택받는 Method
# selOptions : 차트의 종류(혹은 Data업데이트)를 선택받는 Method
# dataClensing : 사이즈 data의 불필요한 문자를 제거하고, Size를 A/B/C 3개그룹으로 분할
# 
# chartMethod1 : 최근 3일 체결거래량(Y) 많은 신발 top5
# chartMethod2 : 최근 3일 가격 급등 신발 Top5
# chartMethod3 : 최근 3일 가격 급락 신발 Top5
# chartMethod4 : 선택된 신발 1개에 대해 상세한 분석결과(최대 1주일, 사이즈 그룹별, 최근 거래이력과 구매/판매입찰가 분포)를 보여주는 Method
# chartMethod5 : 선택신발 A와 B의 주요 데이터 차트비교
#
#
# < 프로그램 사용 제약 >
# 1. KREAM 회원가입 (https://kream.co.kr/login) : 현재 ID/PW (setario87@naver.com / pgwAD8&b)
# 2. Selenium 설치 (pip install selenium) : Webdriver 수동 설치하지 않기 위해 v4.0.0 이상 사용
# 3. webdriver-manager 설치(pip install webdriver-manager)
# 4. pandas 설치
# 5. numpy 설치
# 6. matplotlib 설치
###########################################################################################

#암시적 대기
#browser=webdriver.Chrome('chromedriver')
#browser.implicitly_wait(5)

import os
import pandas as pd # for data control
import numpy as np # for data control

import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service # For ChromeWebDriver
from selenium.webdriver.chrome.options import Options # For ChromeWebDriver
from webdriver_manager.chrome import ChromeDriverManager # webdriver-manager
from selenium.webdriver import ActionChains # for scroll down to element
from selenium.webdriver.support.ui import WebDriverWait # For 명시적 대기
from selenium.webdriver.support import expected_conditions as EC # For 명시적 대기 조건
from selenium.common.exceptions import NoSuchElementException # element가 없는경우 예외처리
from urllib.request import urlretrieve  # For 이미지 추출
from matplotlib import pyplot as plt # For chart 표현
import seaborn as sns # For chart 표현


import time # For 시간측정

######################################## Crawling Method List Start ########################################


def basicInfoCrawling(driver, shoesList): # 기본적으로 40개 신발에 대해 데이터 수집

    tradeScaleList = list()
    brandList = list()
    itemNameList = list()    
    
    for shoesOne in shoesList:
        tradeScale_item = shoesOne.find_element(By.CLASS_NAME,'status_value').get_attribute('innerText') # 신발 거래량 Text get
        tradeScale_item = tradeScale_item.replace(',','').replace('거래','').replace(' ','') # Text 정제

        if '만' in tradeScale_item:
            tradeScaleList.append(int(float(tradeScale_item.replace('만',''))*10000)) # '만'이 포함되어 있다면 10000을 곱해서 추가
        else:
            tradeScaleList.append(tradeScale_item) # '만'이 포함되어 있지 않다면, 그냥 추가

        brandList.append(shoesOne.find_element(By.CLASS_NAME,'brand').get_attribute('innerText')) # 브랜드명 추가
        itemNameList.append(shoesOne.find_element(By.CLASS_NAME,'name').get_attribute('innerText').replace('/','_')) # 아이템명 추가

    npCol1 = np.array(itemNameList)     # 아이템명
    npCol2 = np.array(brandList)        # 브랜드명
    npCol3 = np.array(tradeScaleList)   # 거래량
        
    dataset = np.vstack((npCol1,npCol2,npCol3)) # 데이터 열결합
    dataset = pd.DataFrame(dataset.T, columns = ['name', 'brand','tradeScale']) # Transpose 및 dataframe type으로 변환 
        
    return dataset
    
    
def detailDataCrawling(driver):
    
#     currentURL= 'https://kream.co.kr/products/56267'
#     driver.get(url=currentURL)
    
    detailtype = ['trade','sales','buy'] # 3개의 tab에 대한 구분 정보
    action = ActionChains(driver) # action chain 생성 (for scroll down to element)
        
    itemInfoEles = driver.find_element(By.CLASS_NAME, 'main_title_box') # 상세페이지의 상품 정보 Elements 가져오기

    brandName = itemInfoEles.find_element(By.CLASS_NAME, 'brand').get_attribute('innerText') # 브랜드명
    itemName = itemInfoEles.find_element(By.CLASS_NAME, 'title').get_attribute('innerText').replace('/','_') # 상품명
    itemSubName = itemInfoEles.find_element(By.CLASS_NAME, 'sub_title').get_attribute('innerText') # 서브상품명
    print(itemName)
    
    # 데이터 수집용 List 생성
    nameList = list()
    itemSubNameList = list()
    brandNameList = list()
    typeList = list()
    sizeList = list()
    priceList = list()
    dateQtyList = list()
    
    
    # panel1~3 반복문
    # panel1 : 체걸거래 이력
    # panel2 : 판매입찰 이력
    # panel3 : 구매입찰 이력
    for i in range(3):     
        try: # (거래/판매/구매)이력이 있는경우만 실행
            cPanel = 'panel'+str(i+1) # current panel
            
            panelEles = driver.find_element(By.CLASS_NAME,'wrap_bids').find_elements(By.TAG_NAME,'li')
            panelEles[i].click()
            
            print(cPanel," Crawling...")
            btn = driver.find_element(By.ID,cPanel).find_element(By.TAG_NAME,'a') # (거래/판매/구매)이력 더보기 클릭(시세 테이블 Open)
            btn.click() 
            
            # elements 로드 대기
            WebDriverWait(driver,timeout=20).until(lambda d: d.find_element(By.CLASS_NAME, "tab_info").find_element(By.ID,cPanel).find_elements(By.CLASS_NAME,'body_list'))

            # 최초 로드된 체결 (거래/판매/구매)이력 elements 가져오기(최초 최대 50개 로드)
            historyEles = driver.find_element(By.CLASS_NAME, "tab_info").find_element(By.ID,cPanel).find_elements(By.CLASS_NAME,'body_list')

            # 반복 Scroll하여 거래이력 확장
            # 스크롤 1회당 50개씩 노출, * 최대 5회 반복 : 300개 = 초기 50개+250개(50*5)
            bfrLen = 49
            for j in range(5):
                if len(historyEles) <= bfrLen : # 최초 로드된 거래이력이 50개 미만이거나, 스크롤링 이전값과 같으면 stop
                    break
                bfrLen = len(historyEles) # 현재 아이템 개수 저장
                
                # 마지막 (거래/판매/구매)이력으로 Scroll 이동
                action.move_to_element(historyEles[len(historyEles)-1]).perform() 

                # Scroll 이동 후 elements Udate 
                historyEles = driver.find_element(By.CLASS_NAME, "tab_info").find_element(By.ID,cPanel).find_elements(By.CLASS_NAME,'body_list')
            
            # 최종 (거래/판매/구매)이력 element 로드
            historyEles = driver.find_element(By.CLASS_NAME, "tab_info").find_element(By.ID,cPanel).find_elements(By.CLASS_NAME,'body_list')
            print('panel'+str(i+1), "collect : ", len(historyEles), " data")
            
            # 최종 (거래/판매/구매)이력 element 순환하며 데이터 수집
            # 거래가의 경우 전처리 필요(콤마제거, 원제거, 빠른배송Text 제거)
            for hisOne in historyEles:
                hisOne = hisOne.find_elements(By.TAG_NAME,'div') # 각 아이템 div3개 : 사이즈, 거래가, 거래일/수량
                nameList.append(itemName)
                itemSubNameList.append(itemSubName)
                brandNameList.append(brandName)
                typeList.append(detailtype[i])
                sizeList.append(hisOne[0].get_attribute('innerText')) # 사이즈
                priceList.append(hisOne[1].get_attribute('innerText').replace(',','').replace('원','').replace('빠른배송','').replace('\n','')) # 거래가
                dateQtyList.append(hisOne[2].get_attribute('innerText')) # 거래일 or 수량
            
            # 두번째 'X버튼'이 (거래/판매/구매)이력창 닫기에 대한 Element
            xBtn = driver.find_elements(By.CLASS_NAME, 'btn_layer_close')[1] 
            xBtn.click() # 창 닫기
        
        except NoSuchElementException: # 현재 탭에 내역이 없는경우
            print("This panel has no Item")
    # end panel for
    
    npCol1 = np.array(nameList)         # 현재 상세페이지의 아이템명
    npCol2 = np.array(itemSubNameList)  # 현재 상세페이지의 아이템서브명
    npCol3 = np.array(brandNameList)    # 현재 상세페이지의 브랜드명
    npCol4 = np.array(typeList)         # 거래/판매/구매
    npCol5 = np.array(sizeList)         # 사이즈
    npCol6 = np.array(dateQtyList)      # 날짜 혹은 수량
    npCol7 = np.array(priceList)        # 가격
    
    dataset = np.vstack((npCol1,npCol2,npCol3,npCol4,npCol5,npCol6,npCol7))# 데이터 열결합
    # Transpose 및 dataframe type으로 변환
    dataset = pd.DataFrame(dataset.T,columns = ['name', 'subName', 'brand','datatype','size','dateQty','price']) 
    
    return dataset


def imgUrlCrawling(shoesList):
    
    #폴더생성
    img_path = os.getcwd()+'\\shoesimgs'    # 이미지 수집 폴더
    if not os.path.isdir(img_path):      # 폴더가 없는 경우 새로 생성
        os.mkdir(img_path)

    for shoesOne in shoesList:
        # 신발 이미지 Source 추출
        imgSrcs = shoesOne.find_element(By.TAG_NAME, 'img').get_attribute('src')
        
        # 신발 아이템 이름 추출
        shoesName = shoesOne.find_element(By.CLASS_NAME,'name').get_attribute('innerText').replace('/','_')
        
        # 확장자명 추출
        start = imgSrcs.rfind('.')
        end = imgSrcs.rfind('?')
        filetype = imgSrcs[start:end]
        
        urlretrieve(imgSrcs, './shoesimgs/{}{}'.format(shoesName, filetype))


def kreamCrawling() :
    ################ 1. Chrome Web Driver 설정 ################

    start = time.time() # 수행시간 측정 시작

    chrome_options = webdriver.ChromeOptions() # Chrome관련 Option 설정필요시 추가
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)


    ################ 2. Kream 로그인 ###########################
    # id : setario87 
    # pw : pgwAD8&b

    currentURL = 'https://kream.co.kr/login' 
    driver.get(url=currentURL)

    loginEles = driver.find_elements(By.CLASS_NAME, 'input_txt') # 로그인 id/pw 입력 elements
    # element0 : id input tag
    # element1 : password input tag


    myId = 'setario87@naver.com'
    myPw = 'pgwAD8&b'
    loginEles[0].send_keys(myId) # input id
    loginEles[1].send_keys(myPw) # input password

    # login button click
    driver.find_element(By.CLASS_NAME, 'login_btn_box').find_element(By.TAG_NAME,'a').click()

    # 로그인 후 메인페이지 로딩 대기
    WebDriverWait(driver,timeout=30).until(EC.url_to_be('https://kream.co.kr/'))



    ################ 3. 각 신발에 대한 거래량 수집 ###########################
    # caegory_id : 34 → 신발 item으로 Filtering
    # sort = popular → 인기순 정렬
    # ※ page내 item 수는 per_page를 변경해도 40개로 고정되어 있으며, Scroll down시 40개씩 추가됨

    # 신발 리스트 페이지로 이동
    currentURL= 'https://kream.co.kr/search?category_id=34&sort=popular&per_page=40'
    driver.get(url=currentURL)

    # 신발 검색결과 로딩대기
    WebDriverWait(driver,timeout=30).until(EC.presence_of_element_located((By.CLASS_NAME, "search_result_item")))

    # 신발 리스트 가져오기
    shoesList = driver.find_elements(By.CLASS_NAME, 'search_result_item')

    # 기본정보(이름, 브랜드,거래량) 수집 Method 호출
    resultDF1 = basicInfoCrawling(driver, shoesList) 

    # 신발 이미지 파일 수집 Method 호출
    imgUrlCrawling(shoesList)


    ################ 4. 각 신발에 대한 체걸거래/판매입찰/구매입찰 이력 수집 ########################### 

    resultDF2 = pd.DataFrame(columns = ['name', 'subName', 'brand','datatype','size','dateQty','price'])

    # 신발갯수 만큼 반복
    # 상세페이지 후 Back하여 검색결과로 돌아오면 Doc을 다시 불러야해서 shoesList를 iterate할 수 없음
    for i in range(len(shoesList)):
        shoesList = driver.find_elements(By.CLASS_NAME, 'search_result_item')
        shoesList[i].find_element(By.CLASS_NAME, 'product').click() # 신발 상세페이지로 이동
        WebDriverWait(driver,timeout=30).until(EC.presence_of_element_located((By.CLASS_NAME, "main_title_box"))) # 상세페이지 로드 대기
        df = detailDataCrawling(driver) # 상세 페이지 데이터 수집 Method 호출
        driver.back() # 검색결과 페이지로 돌아오기
        WebDriverWait(driver,timeout=30).until(EC.presence_of_element_located((By.CLASS_NAME, "search_result_item"))) # 검색결과 페이지 로드 대기

        resultDF2 = pd.concat([resultDF2, df], ignore_index=True) # 결과 누적


    ################ 5. 결과 Merge 및 CSV 저장 ######################

    resultMerge = pd.merge(left = resultDF1[['name','tradeScale']] , right = resultDF2, how = "right", on = "name")

    resultMerge.to_csv('shoesData.csv',encoding='EUC-KR') # csv저장하기    

    print("time :", time.time() - start)    # 소요시간 측정

    
######################################## Crawling Method List END ########################################



######################################## Chart & Option Method List Start########################################

def showShoesImages(df_shoes):
    shoesNames = np.unique(df_shoes['name']) # 신발 이름명 
    shoesCnt = shoesNames.shape[0] # 수집된 신발 종류 갯수
    img_load_path = os.getcwd()+"\shoesimgs\\" # 신발 이미지 경로

    shoesImgDic = {}
    fig = plt.figure(figsize=(18, 40))

    k = 0
    for i, sName in enumerate(shoesNames):
        try: 
            shoesImg = plt.imread(img_load_path+sName+".png") # 이미지 불러오기
            shoesImgDic[i-k+1]=sName
            p = fig.add_subplot(15, 3, i-k+1)
            # 선택 번호와 신발이름 표시
            p.set_title("No "+str(i-k+1)+" : "+sName, color='red',fontsize=10)   
            p.imshow(shoesImg)
            p.axis('off') # 축표시제거  
        except OSError:
            #print('no file',i)
            k=k+1 # file이 없을 경우 index 조정을 위한 이미지 누락건수 k 증가
            pass
    plt.subplots_adjust(hspace=0.35) # 차트 간격조정
    plt.show()
    
    return shoesImgDic # 차트로 표시해던 신발리스트와 번호 리턴



def selOptions():
    optionDic = {0: "0. 데이터 업데이트하기(1~2시간 소요)",1: "1. 누적 거래량 상위 top10", 2: "2. (최근3일)상품가격 급등 top10", 3: "3. (최근3일)상품가격 급락 top10", 4: "4. 신발 1종 상세분석(사이즈/일자별 시세 및 체결거래량)", 5: "5. 신발 2종 비교분석(신발A VS 신발B)", 6:"6. 프로그램 종료"}

    for opt in list(optionDic.values()):
        print(opt,'\n')
    
    while True : # 정상입력이 아니라면 지속
        try:  # 정수형이고, 리스트 숫자범위 내에있으면 OK
            sel = int(input('확인하려는 차트종류(혹은 데이터 업데이트)를 입력해주세요 : ')) # 차트 종류(or Data업데이트) 번호 입력받기     
            if sel in range(len(optionDic)):
                break           
            else:
                raise ValueError('리스트의 번호를 숫자로 입력해주세요')           
        except ValueError as v:
            print(v)
            
    return sel


def selShoes(df_shoes):
    shoesDic = showShoesImages(df_shoes) # 신발 이미지 보여주기
    
    while True : # 정상입력이 아니라면 지속
        try:  # 정수형이고, 리스트 숫자범위 내에있으면 OK
            sel = int(input('차트에서 확인하려는 신발 번호를 입력해주세요 : ')) # 차트 종류(or Data업데이트) 번호 입력받기     
            if sel in list(shoesDic.keys()):
                break           
            else:
                raise ValueError('리스트에 있는 신발 번호를 숫자로 입력해주세요')           
        except ValueError as v:
            print(v)
    return shoesDic[sel] # 선택된 신발이름 리턴


def selShoesTwo(df_shoes):
    shoesDic = showShoesImages(df_shoes)  # 신발 이미지 보여주기

    while True:  # 정상입력이 아니라면 지속
        try:  # 정수형이고, 리스트 숫자범위 내에있으면 OK
            sel, sel1 = map(int, input('차트에서 확인하려는 신발 번호 두개를 입력해주세요 : ').split())  # 차트 종류(or Data업데이트) 번호 입력받기
            keys = list(shoesDic.keys())
            if sel in keys:
                break
            elif sel1 in keys:
                break
            else:
                raise ValueError('리스트에 있는 신발 번호를 숫자로 입력해주세요')
        except ValueError as v:
            print(v)
    return shoesDic[sel], shoesDic[sel1]  # 선택된 신발이름 리턴


def dataClensing(df_shoes):
    # 정규식을 통한 () 사이즈 제거
    df_shoes['size'] = df_shoes['size'].replace(r'\(.*\)|\s-\s.*', ' ', regex=True)
    
    # EU 사이즈 제거 로직
    removeEuSizeIdx = df_shoes.loc[(df_shoes['size'].str.contains('EU'))].index.tolist()
    df_shoes = df_shoes.drop(removeEuSizeIdx)
    df_shoes = df_shoes.reset_index(drop=True)   
    
    # SIZE 그룹 컬럼 추가
    df_shoes['size'] = pd.to_numeric(df_shoes['size'])

    # SIZE GROUP A : ~ 255
    # SIZE GROUP B : 260 ~ 270
    # SIZE GROUP C : 270 ~
    def groupFunc(x) :
        if x <= 255 :
            return 'A'
        elif x >= 260 and x <= 270:
            return 'B'
        else:
            return 'C'

    df_shoes["sizegroup"] = df_shoes["size"].apply(lambda x : groupFunc(x))
    
    return df_shoes


def chartMethod1(df_shoes):
    df_scale = df_shoes[['name','tradeScale']]
    df_scale_sorted = df_scale.sort_values(by='tradeScale', ascending=False).drop_duplicates()
    df_scale_sorted10 = df_scale_sorted[0:10]
    
    sns.set_theme(style="white", context="talk")
    sns.set(rc={'figure.figsize':(24,10)})
    sns.barplot(data=df_scale_sorted10, x= "tradeScale", y= "name", palette="rocket")

    plt.subplots_adjust(left=0.2)    
    plt.show()
    
def chartMethod2(df_shoes):
    trade_data = df_shoes.loc[(df_shoes["datatype"] =="trade")]
    dateNumpyList = np.unique(trade_data.dateQty) # 데이터의 날짜 리스트 중복제거

    dateList = np.flip(np.sort(dateNumpyList)) # 오름차순 정렬 후 선택
    lastDate = dateList[0] # 최근 날짜
    bf3Date = dateList[2] # 3일전 날짜

    df_3DayAgo = df_shoes.loc[(df_shoes['dateQty'] == bf3Date) & (df_shoes['datatype'] == 'trade')]
    df_today = df_shoes.loc[(df_shoes['dateQty'] == lastDate) & (df_shoes['datatype'] == 'trade')]

    df_3DayAgoMean = df_3DayAgo.groupby('name')['price'].agg(**{'mean_price_3day_ago':'mean'}).reset_index()
    df_3DayAgoMean.mean_price_3day_ago = df_3DayAgoMean.mean_price_3day_ago.round(-3)
    # df_3DayAgoMean.sort_values(by = 'mean_price_3day_ago', ascending = False).head()

    df_todayMean = df_today.groupby('name')['price'].agg(**{'mean_price_today':'mean'}).reset_index()
    df_todayMean.mean_price_today = df_todayMean.mean_price_today.round(-3)
    # df_todayMean.sort_values(by = 'mean_price_today', ascending = False).head()

    df_mean = pd.merge(df_3DayAgoMean,df_todayMean)
    df_mean['gap'] = df_mean.mean_price_today - df_mean.mean_price_3day_ago 

    df_meanDesc = df_mean.sort_values(by = 'gap', ascending = False).head(10)
    df_meanDesc

    sns.set_theme(style="white", context="talk")
    sns.set(rc={'figure.figsize':(24,10)})
    sns.barplot(data=df_meanDesc, x= "gap", y= "name", palette="deep")
    
    plt.subplots_adjust(left=0.2)    
    plt.show()   
    
def chartMethod3(df_shoes):
    trade_data = df_shoes.loc[(df_shoes["datatype"] =="trade")]
    dateNumpyList = np.unique(trade_data.dateQty) # 데이터의 날짜 리스트 중복제거

    dateList = np.flip(np.sort(dateNumpyList)) # 오름차순 정렬 후 선택
    lastDate = dateList[0] # 최근 날짜
    bf3Date = dateList[2] # 3일전 날짜

    df_3DayAgo = df_shoes.loc[(df_shoes['dateQty'] == bf3Date) & (df_shoes['datatype'] == 'trade')]
    df_today = df_shoes.loc[(df_shoes['dateQty'] == lastDate) & (df_shoes['datatype'] == 'trade')]

    df_3DayAgoMean = df_3DayAgo.groupby('name')['price'].agg(**{'mean_price_3day_ago':'mean'}).reset_index()
    df_3DayAgoMean.mean_price_3day_ago = df_3DayAgoMean.mean_price_3day_ago.round(-3)
    # df_3DayAgoMean.sort_values(by = 'mean_price_3day_ago', ascending = False).head()

    df_todayMean = df_today.groupby('name')['price'].agg(**{'mean_price_today':'mean'}).reset_index()
    df_todayMean.mean_price_today = df_todayMean.mean_price_today.round(-3)
    # df_todayMean.sort_values(by = 'mean_price_today', ascending = False).head()

    df_mean = pd.merge(df_3DayAgoMean,df_todayMean)
    df_mean['gap'] = df_mean.mean_price_today - df_mean.mean_price_3day_ago 

    df_meanAsc = df_mean.sort_values(by = 'gap', ascending = True).head(10)
    df_meanAsc

    sns.set_theme(style="white", context="talk")
    rs = np.random.RandomState(8)

    sns.set_theme(style="white", context="talk")
    sns.set(rc={'figure.figsize':(24,10)})
    sns.barplot(data=df_meanAsc, x= "gap", y= "name", palette="deep")

    plt.subplots_adjust(left=0.2)       
    plt.show()    


# 최대 1주일, 최근 거래이력과 구매/판매 입찰가 분포를 보여주는 Method
def chartMethod4(df_shoes, shoesName):   
    # 선택된 신발의 거래이력 데이터만 추출
    trade_data = df_shoes.loc[(df_shoes["name"] == shoesName) & (df_shoes["datatype"] =="trade")]
    dateNumpyList = np.unique(trade_data.dateQty) # 데이터의 날짜 리스트 중복제거

    # 선택된 신발이 7일전 거래이력이 없을 수 있으므로, 7과 날짜 개수 중 작은것을 기준으로 선택
    if dateNumpyList.shape[0] < 7 :
        shorterDate = dateNumpyList.shape[0]
    else :
        shorterDate = 7

    # 선택된 기준(7 or 날짜개수)의 실제 날짜 구하기
    shorterDate = np.flip(np.sort(dateNumpyList))[shorterDate-1] # 오름차순 정렬 후 선택
    
    # 선택기준일자 이후의 데이터만 필터링
    trade_data = trade_data.loc[(df_shoes["dateQty"] >= shorterDate)]

    # 거래된 날짜별 평균가
    meanPrice = trade_data[['name','price']].groupby([trade_data['dateQty'],trade_data['sizegroup']]).mean()
    meanPrice = meanPrice.reset_index() # 인덱스 초기화
    meanPriceA = meanPrice[meanPrice['sizegroup']=='A']
    meanPriceB = meanPrice[meanPrice['sizegroup']=='B']
    meanPriceC = meanPrice[meanPrice['sizegroup']=='C']
    
    # 거래된 날짜별 거래건수
    tradeCnt = trade_data[['name','price']].groupby([trade_data['dateQty'],trade_data['sizegroup']]).count()     
    tradeCnt = tradeCnt.reset_index() # 인덱스 초기화
    tradeCntA = tradeCnt[meanPrice['sizegroup']=='A']
    tradeCntB = tradeCnt[meanPrice['sizegroup']=='B']
    tradeCntC = tradeCnt[meanPrice['sizegroup']=='C']
      
    # 선택된 신발의 구매입찰가 데이터만 추출
    df_shoes["Size&BidType"] = df_shoes["datatype"] + "/" + df_shoes["sizegroup"]
    buy_dataA = df_shoes.loc[(df_shoes["name"] == shoesName) & (df_shoes["datatype"] =="buy") & (df_shoes["sizegroup"] =="A")].astype({'dateQty': 'int64'})
    buy_dataB = df_shoes.loc[(df_shoes["name"] == shoesName) & (df_shoes["datatype"] =="buy") & (df_shoes["sizegroup"] =="B")].astype({'dateQty': 'int64'})
    buy_dataC = df_shoes.loc[(df_shoes["name"] == shoesName) & (df_shoes["datatype"] =="buy") & (df_shoes["sizegroup"] =="C")].astype({'dateQty': 'int64'})
   
    # 선택된 신발의 판매입찰가 데이터만 추출
    sales_dataA = df_shoes.loc[(df_shoes["name"] == shoesName) & (df_shoes["datatype"] =="sales") & (df_shoes["sizegroup"] =="A")].astype({'dateQty': 'int64'})
    sales_dataB = df_shoes.loc[(df_shoes["name"] == shoesName) & (df_shoes["datatype"] =="sales") & (df_shoes["sizegroup"] =="B")].astype({'dateQty': 'int64'})
    sales_dataC = df_shoes.loc[(df_shoes["name"] == shoesName) & (df_shoes["datatype"] =="sales") & (df_shoes["sizegroup"] =="C")].astype({'dateQty': 'int64'})
    
    # 차트 그리기
    fig, ax = plt.subplots(1, 2, figsize=(20,5))
    
    # 일자별 가격 추이 라인 차트
    ax[0].plot(meanPriceA['dateQty'], meanPriceA['price'], color ='green',label='sizeA(~255)')  # SizeA(~255) 가격 추이 그래프 그리기
    ax[0].plot(meanPriceB['dateQty'], meanPriceB['price'], color ='blue',label='sizeB(~270))')  # SizeB(~270) 가격 추이 그래프 그리기
    ax[0].plot(meanPriceC['dateQty'], meanPriceC['price'], color ='red',label='sizeC(275~)')  # SizeC(275~) 가격 추이 그래프 그리기
     
    ax[0].set_title("<"+selName+"> Price by day")
    ax[0].set_xlabel('Date')
    ax[0].set_ylabel('Price(won)')
    ax[0].legend(loc='upper left',fontsize=10) # 좌측 상단에 범례 표시    
    ax[0].grid(True, axis='y', color='gray', alpha=0.5, linestyle='--')

    # 구매입찰, 판매입찰 분포 산점도
    ax[1].scatter(buy_dataA['Size&BidType'], buy_dataA['price'],marker="o", s = buy_dataA['dateQty']*10, c='green') # 구매 입찰가 그리기(SizeA)
    ax[1].scatter(sales_dataA['Size&BidType'], sales_dataA['price'],marker="v", s = sales_dataA['dateQty']*10, c='green') # 판매 입찰가 그리기(SizeA)
    
    ax[1].scatter(buy_dataB['Size&BidType'], buy_dataB['price'],marker="o", s = buy_dataB['dateQty']*10, c='blue') # 구매 입찰가 그리기(SizeB)
    ax[1].scatter(sales_dataB['Size&BidType'], sales_dataB['price'],marker="v", s = sales_dataB['dateQty']*10, c='blue') # 판매 입찰가 그리기(SizeB)
    
    ax[1].scatter(buy_dataC['Size&BidType'], buy_dataC['price'],marker="o", s = buy_dataC['dateQty']*10, c='red') # 구매 입찰가 그리기(SizeC)
    ax[1].scatter(sales_dataC['Size&BidType'], sales_dataC['price'],marker="v", s = sales_dataC['dateQty']*10, c='red') # 판매 입찰가 그리기(SizeC)
    
    ax[1].legend(["SizeA(~255) bid purchase","SizeA(~255) bid sales","SizeB(~270) bid purchase","SizeB(~270) bid sales","SizeC(275~) bid purchase","SizeC(275~) bid sales"],loc='upper center') # 범례 표시    
    ax[1].set_title("<"+selName+"> purchase and sales bidding Count")
    ax[1].set_ylabel('Bidding Price')
    ax[1].grid(True, axis='y', color='gray', alpha=0.5, linestyle='--')
    
    # 일자별 거래량
    fig2, ax2 = plt.subplots(1,1, figsize=(20,5))
    ax2.bar(tradeCntA['dateQty'], tradeCntA['name'], color ='green')
    ax2.bar(tradeCntB['dateQty'], tradeCntB['name'], color ='blue')
    ax2.bar(tradeCntC['dateQty'], tradeCntC['name'], color ='red')
    ax2.set_title("<"+selName+"> Trade items by day")
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Trade number of cases') 

    plt.show()
    
    
    
def chartMethod5(df_shoes, shoesName, shoesName1):
    # 신발 A VS 신발B (https://seaborn.pydata.org/examples/grouped_barplot.html)
    df_compare_shoes = df_shoes.loc[(df_shoes["name"] == shoesName) | (df_shoes["name"] == shoesName1)]
    sns.set_theme(style="whitegrid")
    # Draw a nested barplot by species and sex
    g = sns.catplot(
        data=df_compare_shoes, kind="bar",
        x="size", y="price", hue="name",
        ci="sd", palette="dark", alpha=.6, height=10
    )

    g.despine(left=True)
    g.set_axis_labels("", "price (won)")
    g.legend.set_title("")

    plt.show()
    
######################################## Chart & Option Method List END ########################################


#################################### Program MAIN START ####################################
isNotExit = True

try:
    df_shoes = pd.read_csv('shoesData.csv', index_col=0, encoding='euc-kr') # 크롤링 파일 로드
    df_shoes = dataClensing(df_shoes) # 사이즈 괄호제거, 사이즈 그룹(A,B,C) 컬럼 추가
except FileNotFoundError:
    print("Data가 업습니다. 메뉴선택 0번 크롤링을 수행해주세요\n")

while isNotExit:
    selOption = selOptions()
    if selOption == 6: 
        isNotExit = False # 6번 선택시 종료
    elif selOption==0: # 크롤링 재수행 (DataUpdate)
        kreamCrawling()
        df_shoes = pd.read_csv('shoesData.csv', index_col=0, encoding='euc-kr')
        df_shoes = dataClensing(df_shoes)
    elif selOption==1: # 1번 차트 선택
        chartMethod1(df_shoes)
    elif selOption==2: # 2번 차트 선택
        chartMethod2(df_shoes)
    elif selOption==3: # 3번 차트 선택
        chartMethod3(df_shoes)
    elif selOption==4: # 4번 차트 선택
        selName = selShoes(df_shoes)
        chartMethod4(df_shoes,selName)
    elif selOption == 5:  # 5번 차트 선택
        selName, selName1 = selShoesTwo(df_shoes)
        chartMethod5(df_shoes, selName, selName1)

#################################### Program MAIN END ####################################



#################################### Program MAIN ####################################
isNotExit = True

try:
    df_shoes = pd.read_csv('shoesData.csv', index_col=0, encoding='euc-kr') # shoesData.csv 및 전처리 메서드 자리
    df_shoes = dataClensing(df_shoes) # 사이즈 괄호제거, 사이즈 그룹(A,B,C) 컬럼 추가
except FileNotFoundError:
    print("Data가 업습니다. 메뉴선택 0번 크롤링을 수행해주세요\n")
    
while isNotExit:
    selOption = selOptions()
    if selOption == 6: 
        isNotExit = False # 6번 선택시 종료
    elif selOption==0: # 크롤링 재수행 (DataUpdate)
        kreamCrawling()
        df_shoes = pd.read_csv('shoesData.csv', index_col=0, encoding='euc-kr')
        df_shoes = dataClensing(df_shoes)
    elif selOption==1: # 1번 차트 선택
        chartMethod1(df_shoes)
    elif selOption==2: # 2번 차트 선택
        chartMethod2(df_shoes)
    elif selOption==3: # 3번 차트 선택
        chartMethod3(df_shoes)
    elif selOption==4: # 4번 차트 선택
        selName = selShoes(df_shoes)
        chartMethod4(df_shoes,selName)
    elif selOption==5: # 5번 차트 선택
        selName = selShoes(df_shoes)
        chartMethod5(df_shoes,selName)        





