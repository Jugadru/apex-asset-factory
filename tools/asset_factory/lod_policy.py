"""Deterministic procedural LOD policy; preserve named components and pivots."""
from copy import deepcopy


def apply_policy(parts, level):
    if type(level) is not int or level not in (0,1,2):
        raise ValueError("invalid LOD level")
    result=deepcopy(parts)
    for part in result:
        if part["kind"]=="cylinder" and level:
            part["sides"]=min(part["sides"],24 if level==1 else 12)
        if part["kind"]=="box" and level==2:
            part["bevel"]=0
    return result


def bevel_segments(level):
    if type(level) is not int or level not in (0,1,2):
        raise ValueError("invalid LOD level")
    return 2 if level==0 else 1


def level_for_distance(distance,current):
    if type(current) is not int or current not in (0,1,2) or not 0<=distance<1e9:
        raise ValueError("invalid distance or level")
    while current<2 and distance>=(25,70)[current]+3:
        current+=1
    while current>0 and distance<=(25,70)[current-1]-3:
        current-=1
    return current
