import time
import multiprocessing as mp
#from mission_execution1 import mission_execution
from uav import UAV
import random
from mission_type import MissionType, mission_duration
import psycopg2

distance = 10
hover_time = 2
r2h_mission = [0 for _ in range(distance)]
r2h_mission.extend([1 for _ in range(hover_time)])
print(r2h_mission)
exit()

if __name__ == '__main__':
    pool = mp.Pool(10)

    con = psycopg2.connect(
        host="localhost",
        database="rt_phm_simulation",
        user="postgres",
        password="R!3senfelge"
    )

    # while True:


    for i in range(3):
        uav = UAV(i + 1)
        mission_type = random.choice(list(MissionType))
        uav.mission_type = mission_type.value
        mission_length = random.randint(*mission_duration[mission_type])
        pool.apply_async(mission_execution, [uav, mission_length])
        time.sleep(3)

    time.sleep(10)

    for i in range(2):
        uav = UAV(i + 4)
        mission_type = random.choice(list(MissionType))
        uav.mission_type = mission_type.value
        mission_length = random.randint(*mission_duration[mission_type])
        pool.apply_async(mission_execution, [uav, mission_length])




