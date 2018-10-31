from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import urllib.request as ul
import xmltodict
import json
import time as t

# from django.shortcuts import render
# import sys
# import io
# sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
# sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')
# 깃허브 왜 안되냐

# BusStops, to School
schoolBusStop13 = ['벽산아파트', '약수맨션', '노량진역', '대방역2번출구앞']
schoolBusStop5513 = ['관악구청', '서울대입구', '봉천사거리, 봉천중앙시장', '봉현초등학교', '벽산블루밍벽산아파트303동앞']

# BusStops, to Home
homeBusStop13 = ['관악드림타운북문 방면 (동작13)', '벽산아파트 방면 (동작13)']
homeBusStop5513 = ['관악드림타운북문 방면 (5513)', '벽산아파트 방면 (5513)']

# Meal table, index(0-4) => Mon-Fri
lunchfoods = []
dinnerfoods = []


# n은 xml상에서 봤을 때 itemList 순서임, index이므로 0부터 시작.
def bus(n, busStn, busNo):
    url = 'http://ws.bus.go.kr/api/rest/stationinfo/getStationByUid?ServiceKey=fef2WSoMFkV557J%2BKKEe0LmP4Y1o8IsH6x4Lv4p0pArUHTs6sk6sHVGaNfkFZRM2sSUn5Uvw0JzETmEyk5VeoA%3D%3D&arsId=' + busStn

    request = ul.Request(url)
    response = ul.urlopen(request)
    rescode = response.getcode()

    if rescode == 200:
        responseData = response.read()
        rD = xmltodict.parse(responseData)
        rDJ = json.dumps(rD)
        rDD = json.loads(rDJ)

        if n == 0:
            bus01 = rDD["ServiceResult"]["msgBody"]["itemList"]["arrmsg1"]
            bus02 = rDD["ServiceResult"]["msgBody"]["itemList"]["arrmsg2"]
            id01 = rDD["ServiceResult"]["msgBody"]["itemList"]["vehId1"]
            id02 = rDD["ServiceResult"]["msgBody"]["itemList"]["vehId2"]

        else:
            bus01 = rDD["ServiceResult"]["msgBody"]["itemList"][n]["arrmsg1"]
            bus02 = rDD["ServiceResult"]["msgBody"]["itemList"][n]["arrmsg2"]
            id01 = rDD["ServiceResult"]["msgBody"]["itemList"][n]["vehId1"]
            id02 = rDD["ServiceResult"]["msgBody"]["itemList"][n]["vehId2"]

        bus01 = '곧' if bus01 == '곧 도착' else bus01
        bus01 = bus01.replace('분', '분 ').replace('초후', '초 후 ').replace('번째', ' 정류장')
        bus02 = bus02.replace('분', '분 ').replace('초후', '초 후 ').replace('번째', ' 정류장')

        # 동작13과 5513의 리턴값이 다르다, 타요버스가 없으니까 타요 제외.
        if busNo == 13:
            tayoList = ['57', '58', '92', '95']
            tayo1 = '이번 버스는 타요차량입니다.' if id01[-2:] in tayoList else '이번 버스는 일반차량입니다.'
            tayo2 = '다음 버스는 타요차량입니다.' if id02[-2:] in tayoList else '다음 버스는 일반차량입니다.'
            if bus01 in ['출발대기', '운행종료']:
                tayo1 = ''
            if bus02 in ['출발대기', '운행종료']:
                tayo2 = ''
            return [bus01, bus02, tayo1, tayo2]

        elif busNo == 5513:
            return [bus01, bus02]


isRefreshed = 0
updatedtime = 0


def foodie(n):
    global isRefreshed, updatedtime
    print(isRefreshed)

    s = list(str(t.localtime()).replace('time.struct_time(', '').replace(')', '').split(', '))
    # 2018.10.29 형식
    ymd = s[0].split('=')[1] + '.' + s[1].split('=')[1] + '.' + s[2].split('=')[1]
    currenttime = int(t.time())
    dayList = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    # 일요일, 새로고침되지 않았을 때 실행 (다른 방법 필요할듯, 업데이트 날짜 가져와서 7일 내이면 넘기고, 아니면 업데이트 하는 식으로)
    # food함수 내에는 고쳐질 게 많다. 토요일, 일요일에 리턴하는 0값을 처리해야 함.
    # 또, 방학이나 공휴일처럼 평일이지만 배식하지 않는 경우를 추가해줘야 함.
    if ((currenttime - updatedtime) > 500000 and isRefreshed == 0) or lunchfoods == []:
        # print함수는 서버 내의 consol log에 기록
        print('Empty Food task, Building up...')

        from bs4 import BeautifulSoup
        import requests

        # 중식 r1, 석식 r2
        r1 = requests.get(
            "https://stu.sen.go.kr/sts_sci_md01_001.do?"
            "schulCode=B100005528&schMmealScCode=2&schulCrseScCode=4&schYmd=" + ymd)
        r2 = requests.get(
            "https://stu.sen.go.kr/sts_sci_md01_001.do?"
            "schulCode=B100005528&schMmealScCode=3&schulCrseScCode=4&schYmd=" + ymd)
        c1 = r1.content
        c2 = r2.content
        html1 = BeautifulSoup(c1, "html.parser")
        html2 = BeautifulSoup(c2, "html.parser")
        tr1 = html1.find_all('tr')
        td1 = tr1[2].find_all('td')
        tr2 = html2.find_all('tr')
        td2 = tr2[2].find_all('td')

        for i in range(1, 6):
            td1[i] = str(td1[i])
            td2[i] = str(td2[i])
            tempdish1 = td1[i].replace('<td class="textC">', '').replace('<br/>', '\n', -1).replace('</td>', '')
            dish1 = ''
            for _ in tempdish1:
                if _ in '1234567890.':
                    continue
                else:
                    dish1 += _

            tempdish2 = td2[i].replace('<td class="textC">', '').replace('<br/>', '\n', -1).replace('</td>', '')
            dish2 = ''
            for _ in tempdish2:
                if _ in '1234567890.':
                    continue
                else:
                    dish2 += _

            lunchfoods.append(dish1)
            dinnerfoods.append(dish2)
        updatedtime = int(t.time())
        isRefreshed = 1

    # 토요일에 리프레시 0으로 맞춰주자
    if n == 'Sat' and isRefreshed == 1:
        isRefreshed = 0

    return dayList.index(n)


def keyboard(request):
    return JsonResponse(

        {
            'type': 'buttons',

            'buttons': ['오늘의 급식', '등하교 버스안내']

        }

    )


@csrf_exempt
def message(request):
    json_str = (request.body).decode('utf-8')
    received_json = json.loads(json_str)
    clickedButton = received_json['content']

    if clickedButton == '초기화면':
        return JsonResponse(
            {
                'message': {
                    'text': '초기화면으로 돌아갑니다.'
                },
                'keyboard': {
                    'type': 'buttons',
                    'buttons': ['오늘의 급식', '등하교 버스안내']
                }
            }
        )

    elif clickedButton == '오늘의 급식':
        return JsonResponse(
            {
                'message': {
                    'text': '중 / 석식을 선택해 주세요.\n매일 오후 2시 이후에는 다음날 급식을 안내합니다.'
                },
                'keyboard': {
                    'type': 'buttons',
                    'buttons': ['중식', '석식', '초기화면']
                }
            }
        )

    elif clickedButton == '등하교 버스안내':
        return JsonResponse(
            {
                'message': {
                    'text': '노선 및 방향을 선택해 주세요'
                },
                'keyboard': {
                    'type': 'buttons',
                    'buttons': ['동작13 - 등교', '동작13 - 하교', '5513 - 등교', '5513 - 하교']
                }
            }
        )

    elif clickedButton == '중식':
        tmr = 0
        day = foodie(str(t.ctime())[:3])

        if int(str(t.ctime())[11:13]) > 14: # 2시가 지나면 내일 점심을 보여준다
            tmr = 1
            day += 1
        return JsonResponse(
            {
                'message': {
                    'text': '{}의 중식\n\n{}'.format('오늘' if tmr == 0 else '내일',
                                                  lunchfoods[day] if day < 5 else '메뉴가 없습니다.')
                },
                'keyboard': {
                    'type': 'buttons',
                    'buttons': ['오늘의 급식', '등하교 버스안내']
                }
            }
        )

    elif clickedButton == '석식':
        tmr = 0
        day = foodie(str(t.ctime())[:3])

        if int(str(t.ctime())[11:13]) > 14:  # 2시가 지나면 내일 점심을 보여준다
            tmr = 1
            day += 1
        return JsonResponse(
            {
                'message': {
                    'text': '{}의 석식\n\n{}'.format('오늘' if tmr == 0 else '내일',
                                                  lunchfoods[day] if day < 5 else '메뉴가 없습니다.')
                },
                'keyboard': {
                    'type': 'buttons',
                    'buttons': ['오늘의 급식', '등하교 버스안내']
                }
            }
        )

    elif clickedButton == '5513 - 등교':
        return JsonResponse(
            {
                'message': {
                    'text': '정류장을 선택해 주세요.'
                },
                'keyboard': {
                    'type': 'buttons',
                    'buttons': ['관악구청', '서울대입구', '봉천사거리, 봉천중앙시장', '봉현초등학교', '벽산블루밍벽산아파트303동앞']
                }
            }
        )

    elif clickedButton == '동작13 - 등교':
        return JsonResponse(
            {
                'message': {
                    'text': '정류장을 선택해 주세요.'
                },
                'keyboard': {
                    'type': 'buttons',
                    'buttons': ['벽산아파트', '약수맨션', '노량진역', '대방역2번출구앞', '초기화면']
                }
            }
        )

    if clickedButton in schoolBusStop13:
        busStop = ['21910', '20891', '20867', '20834'][schoolBusStop13.index(clickedButton)]
        n = [0, 1, 1, 2][schoolBusStop13.index(clickedButton)]
        busList = bus(n, busStop, 13)
        bus01, bus02, tayo1, tayo2 = map(str, busList)

        return JsonResponse(
            {
                'message': {
                    'text': '---{}({})---\n\n이번 버스 : {}{}\n{}\n\n다음 버스 : {}{}\n{}'.format(clickedButton, busStop, bus01,
                            '도착 예정' if bus01 not in ['출발대기', '운행종료'] else '', tayo1, bus02,
                            '도착 예정' if bus02 not in ['출발대기', '운행종료'] else '', tayo2)

                },
                'keyboard': {
                    'type': 'buttons',
                    'buttons': ['오늘의 급식', '등하교 버스안내']
                }
            }
        )

    if clickedButton in schoolBusStop5513:
        busStop = ['21130', '21252', '21131', '21236', '21247'][schoolBusStop5513.index(clickedButton)]
        n = [5, 1, 7, 2, 0][schoolBusStop5513.index(clickedButton)]
        busList = bus(n, busStop, 5513)
        bus01, bus02 = map(str, busList)

        return JsonResponse(
            {
                'message': {
                    'text': '---{}({})---\n\n이번 버스 : {}{}\n\n다음 버스 : {}{}\n'.format(clickedButton, busStop, bus01,
                            '도착 예정' if bus01 not in ['출발대기', '운행종료'] else '', bus02,
                            '도착 예정' if bus02 not in ['출발대기', '운행종료'] else '')
                },
                'keyboard': {
                    'type': 'buttons',
                    'buttons': ['오늘의 급식', '등하교 버스안내']
                }
            }
        )

    elif clickedButton == '동작13 - 하교':

        return JsonResponse(
            {
                'message': {
                    'text': '동작13 버스 방향을 선택해 주세요.'
                },
                'keyboard': {
                    'type': 'buttons',
                    'buttons': ['관악드림타운북문 방면 (동작13)', '벽산아파트 방면 (동작13)', '초기화면']
                }
            }
        )

    elif clickedButton == '5513 - 하교':

        return JsonResponse(
            {
                'message': {
                    'text': '5513 버스 방향을 선택해 주세요.'
                },
                'keyboard': {
                    'type': 'buttons',
                    'buttons': ['관악드림타운북문 방면 (5513)', '벽산아파트 방면 (5513)', '초기화면']
                }
            }
        )

    if clickedButton in homeBusStop13:
        busStop = ['21244', '21243'][homeBusStop13.index(clickedButton)]
        busList = bus(1, busStop, 13)
        bus01, bus02, tayo1, tayo2 = map(str, busList)
        return JsonResponse(
            {
                'message': {
                    'text': '---{}({})---\n\n이번 버스 : {}{}\n{}\n\n다음 버스 : {}{}\n{}'.format(clickedButton, busStop, bus01,
                            '도착 예정' if bus01 not in ['출발대기', '운행종료'] else '', tayo1, bus02,
                            '도착 예정' if bus02 not in ['출발대기', '운행종료'] else '', tayo2)
                },
                'keyboard': {
                    'type': 'buttons',
                    'buttons': ['오늘의 급식', '등하교 버스안내']
                }
            }
        )

    if clickedButton in homeBusStop5513:
        busStop = ['21244', '21243'][homeBusStop5513.index(clickedButton)]
        busList = bus(2, busStop, 5513)
        bus01, bus02 = map(str, busList)
        return JsonResponse(
            {
                'message': {
                    'text': '---{}({})---\n\n이번 버스 : {}{}\n\n다음 버스 : {}{}\n'.format(clickedButton, busStop, bus01,
                            '도착 예정' if bus01 not in ['출발대기', '운행종료'] else '', bus02,
                            '도착 예정' if bus02 not in ['출발대기', '운행종료'] else '')

                },
                'keyboard': {
                    'type': 'buttons',
                    'buttons': ['오늘의 급식', '등하교 버스안내']
                }
            }
        )