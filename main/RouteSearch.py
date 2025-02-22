import collections

import math
import hexgrid
import morton
from main.models import *
import time

from queue import PriorityQueue

Point = collections.namedtuple("Point", ["x", "y"])

Hmap = {}
TileValue_Map = {}


# 시간 측정 데코레이터 함수
def logging_time(original_fn):
    def wrapper_fn(*args, **kwargs):
        start_time = time.time()
        result = original_fn(*args, **kwargs)
        end_time = time.time()
        print("소요시간[{}]: {} sec".format(original_fn.__name__, end_time - start_time))
        return result

    return wrapper_fn


# H(x) : 현재 위치에서 목적지 까지의 거리 - manhaten distance
def Heuristic(a, b):
    # type : (Hex(q,r), Hex(q,r))
    dx = a.q - b.q
    dy = a.r - b.r

    if dx == dy:
        return abs(dx + dy)
    else:
        return max(abs(dx), abs(dy))


def HexHeuristic(a, b):  # Diagonal Distance
    return (abs(a.q - b.q) + abs(a.q + a.r - b.q - b.r) + abs(a.r - b.r)) / 1


# 현재 까지 이동한 거리
def G_cost():
    cost = 0
    return cost


# Time Complexity는 H에 따라 다르다.
# O(b^d), where d = depth, b = 각 노드의 하위 요소 수
# heapque를 이용하면 길을 출력할 때 reverse를 안해도 됨

class Node:
    def __init__(self, parent=None, position=None):
        self.parent = parent
        self.position = position

        self.g = 0  # 출잘지지점에서 현재노드까지의 cost합
        self.h = 0  # heuristic 현재노드에서 목적지까지의 추정 거리
        self.f = 0  # g+h

        self.cost = 0  # 이 타일의 cost

        self.TileValue = 0
        self.TileValue_sum = 0  # 여기 까지 오는데 먹는 Value

    def __eq__(self, other):
        return self.position == other.position


@logging_time
def giveCost(grid, startx, starty, endx, endy):
    # x : lon(128), y : lat(37)
    loadpoint = Loadpoint.objects.filter(lon__range=(endx, startx), lat__range=(endy, starty)).order_by('lat')
    cctv = Cctv.objects.filter(lon__range=(endx, startx), lat__range=(endy, starty)).order_by('lat')
    # securitycenter = Securitycenter.objects.filter(lon__range=(endx, startx), lat__range=(endy, starty)).order_by('lat')
    # lamp = Lamp.objects.filter(lon__range=(endx, startx), lat__range=(endy, starty)).order_by('lat')
    # alltimeshop = Alltimeshop.objects.filter(lon__range=(endx, startx), lat__range=(endy, starty)).order_by('lat')

    # 24시 가게
    # for coor in alltimeshop:
    #     Hex_Point = grid.hex_at(Point(float(coor.lon), float(coor.lat)))
    #
    #     if (Hex_Point in Hmap):
    #         Hmap[Hex_Point] = Hmap[Hex_Point] + 1

    #securitycenter
    # for coor in securitycenter:
    #     Hex_Point = grid.hex_at(Point(float(coor.lon), float(coor.lat)))
    #
    #     if (Hex_Point in Hmap):
    #         Hmap[Hex_Point] = Hmap[Hex_Point] + 1

    # cctv
    for coor in cctv:
        Hex_Point = grid.hex_at(Point(float(coor.lon), float(coor.lat)))

        if (Hex_Point in Hmap):
            Hmap[Hex_Point] = Hmap[Hex_Point] + 1

    # loadpoint
    for coor in loadpoint:
        Hex_Point = grid.hex_at(Point(float(coor.lon), float(coor.lat)))

        if (Hex_Point in Hmap):
            Hmap[Hex_Point] = Hmap[Hex_Point] + 2

    # lamp
    # for coor in lamp:
    #     Hex_Point = grid.hex_at(Point(float(coor.lon), float(coor.lat)))
    #
    #     if (Hex_Point in Hmap):
    #         Hmap[Hex_Point] = Hmap[Hex_Point] + 1


@logging_time
def astar(starthex, endhex, grid, mapsize):
    # startNode 와 endNode 초기화
    startNode = Node(None, starthex)
    endNode = Node(None, endhex)

    # openList, closeList 초기화
    openList = []  # 방문중이거나, 방문 할 곳
    closeList = []  # 더 나은 위치를 찾은 곳(이미 방문)

    # FirstCost_node = First_Cost_Search(startNode, grid)

    # openList에 시작 노드 추가
    openList.append(startNode)

    print('시작 :', startNode.position, '끝 : ', endNode.position)
    max_h = Heuristic(starthex, endhex)
    print('maxh : ', max_h)

    # endNode를 찾을 때까지 실행
    while openList:

        # 현재 노드 지정
        currentNode = openList[0]
        currentIdx = 0

        # print('현재 노드 : ',currentNode.position)
        # 이미 같은 노드가 openList에 있고, f값이 더 크면 -> Cost값
        # currentNode를 openList안에 있는 값으로 교체
        for index, item in enumerate(openList):
            if item.TileValue < currentNode.TileValue:
                currentNode = item
                currentIdx = index

        # openList에서 제거하고 closedList에 추가
        openList.pop(currentIdx)
        closeList.append(currentNode)

        # #현재 노드가 목적지면 current.position 추가하고
        # current 부모 노드로 이동
        if currentNode.position == endNode.position:
            print('찾았니?')
            path = []
            current = currentNode

            while current is not None:
                path.append(current.position)
                current = current.parent
            return path[::-1]  # reverse - 최단경로

        children = []

        # 인접한 좌표 체크
        # neighbor -> 범위, cost(갈 수 잇는 길인지) 체크

        neighbor = grid.hex_neighbors(currentNode.position, 1)

        for newPosition in neighbor:
            # 탐색할 새 노드 -> Hmap 안에 없으면 path(범위 안에 hexgrid만 탐색)
            if Hmap.get(newPosition) is not None:
                TileCost = Hmap[newPosition]
            else:
                continue

            new_node = Node(currentNode, newPosition)

            if new_node in closeList:
                continue

            new_node.cost = int(TileCost)

            new_node.g = int(currentNode.g) + 1  # 현재까지 오는 비용
            new_node.h = int(HexHeuristic(new_node.position, endhex))  # 목적지까지의 추정비용
            new_node.f = new_node.g + new_node.h

            # f range : 0 ~ [max_h + hexgrid length] -> 50:50
            new_node.TileValue = 1 / (1 + new_node.cost) + (new_node.f / max_h)
            new_node.TileValue_sum = currentNode.TileValue_sum + new_node.TileValue

            TileValue_Map[new_node.position] = new_node.TileValue

            if new_node in openList:
                idx = openList.index(new_node)
                if new_node.TileValue < openList[idx].TileValue:
                    openList.pop(idx)
                else:
                    continue

            children.append(new_node)

        children = sorted(children, key=lambda Node: Node.TileValue, reverse=True)

        openList = openList + children
        endpoint = currentNode

    path = []
    print('못찾음')
    for ch in closeList:
        path.append(ch.position)
    return path[::-1]  # reverse - 최단경로


# hex 좌표로
@logging_time
def startSetting(start_coordinate, end_coordinate):
    startX = start_coordinate[1]
    startY = start_coordinate[0]
    endX = end_coordinate[1]
    endY = end_coordinate[0]

    center = hexgrid.Point((float(startX) + float(endX)) / 2, (float(startY) + float(endY)) / 2)  # 중앙
    rate = 110.574 / (111.320 * math.cos(37.55582994870823 * math.pi / 180))  # 서울의 중앙을 잡고, 경도값에 대한 비율
    grid = hexgrid.Grid(hexgrid.OrientationFlat, center, Point(rate * 0.00005, 0.00006),
                        morton.Morton(2, 32))  # Point : hexgrid Size
    sPoint = grid.hex_at(Point(float(startX), float(startY)))  # hex_at : point to hex -> 출발지 Point -> hex좌표
    ePoint = grid.hex_at(Point(float(endX), float(endY)))  # 목적지
    map_size = max(abs(sPoint.q), abs(sPoint.r))  # 열col(q) 행row(r)

    # real_hexMap_size = map_size+10   #ex) 21 (q,r)이 가지는 최대 절대값
    real_hexMap_size = map_size + 15  # ex) 21 (q,r)이 가지는 최대 절대값

    LeftCorner = (
    grid.hex_center(hexgrid.Hex(-(real_hexMap_size), 0)).x, grid.hex_center(hexgrid.Hex(0, -(real_hexMap_size))).y)
    RightCorner = (
    grid.hex_center(hexgrid.Hex((real_hexMap_size), 0)).x, grid.hex_center(hexgrid.Hex(0, (real_hexMap_size))).y)

    endx = RightCorner[0]
    endy = RightCorner[1]

    startx = LeftCorner[0]
    starty = LeftCorner[1]

    # DB 데이터 불러오기
    # 범위의 양수 계산을 위해 변수 startx,endx / starty,endy 초기화
    if (endx > startx):
        temp = endx
        endx = startx
        startx = temp
    if (endy > starty):
        temp = endy
        endy = starty
        starty = temp

    neighbor = []

    neighbor = grid.hex_neighbors(grid.hex_at(center), real_hexMap_size)  # hex_neighbor : type(Hex, int) -> list
    neighbor.append(grid.hex_at(center))
    # print(neighbor)

    for hex in neighbor:
        Hmap[hex] = 0

    giveCost(grid, startx, starty, endx, endy)  # cost

    # result = astar(sPoint,ePoint,grid,map_size)
    path = astar(sPoint, ePoint, grid, map_size)
    return Hmap, grid, path, TileValue_Map