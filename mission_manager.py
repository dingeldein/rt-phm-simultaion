from mission_execution import mission_execution
import numpy as np
import psycopg2
import time
import multiprocessing as mp
from uav import UAV


if __name__ == '__main__':
    #mp.freeze_support
    mission_types = ["Delivery Mission", "Reconnaissance Mission"]
    mission_queue = np.genfromtxt("mission_queue.csv", delimiter=",")
    pool = mp.Pool(10)

    con = psycopg2.connect(
        host="localhost",
        database="rt_phm_simulation",
        user="postgres",
        password="R!3senfelge"
    )

    mission_no = 1
    fleet_availability = np.zeros((10))
    while True:
        # check pending mission and get number of UAV needed
        uav_needed = len(mission_queue[mission_queue[:, 0] == mission_no])

        # check number of UAV available
        for i in range(10):
            cur = con.cursor()
            cur.execute('select mission_mode from uav{} order by index desc limit 1'.format(i + 1))
            uav_status = np.array(cur.fetchall())
            fleet_availability[i] = np.round(int(uav_status))
        # print("Before mission fleet availability: ", fleet_availability)
        uav_available = len(np.where(fleet_availability == 2)[0])
        print('Available UAV: ', uav_available, ' -  Needed UAV: ', uav_needed)
        print(fleet_availability)

        # assign mission
        if uav_needed <= uav_available:

            if mission_queue[mission_queue[:, 0] == mission_no][0, 1] == 0:
                # delivery mission
                print("Delivery mission in queue")
                # get available UAV [integration of health dependend selection HERE; instead of min]
                mission_len = mission_queue[mission_queue[:, 0] == mission_no][0, 3]
                available_uav_id = np.where(fleet_availability == 2)[0][0] + 1
                #chosen_uav = UAV(available_uav_id)
                #print(available_uav_id == chosen_uav.uav_id)
                #chosen_uav.mission_type = 0
                print("UAV to be sent on mission: ", available_uav_id)
                fleet_availability[available_uav_id - 1] = 0
                pool.apply_async(mission_execution, [available_uav_id, mission_len])
                # print('UAV ', available_uav_id, ' started on Delivery Mission #', mission_no)
                print(fleet_availability)

            if mission_queue[mission_queue[:, 0] == mission_no][0, 1] == 1:
                # reconnaissance mission
                print("SAR mission in queue")
                # get available UAV [integration of health dependend selection HERE]
                mission_len = mission_queue[mission_queue[:, 0] == mission_no][0, 3]
                for j in range(uav_needed):
                    available_uav_id = np.where(fleet_availability == 2)[0][0] + 1
                    #chosen_uav = UAV(available_uav_id)
                    #print(available_uav_id == chosen_uav.uav_id)
                    #chosen_uav.mission_type = 1
                    fleet_availability[available_uav_id - 1] = 1
                    # print(fleet_availability)
                    # print(available_uav_id)
                    pool.apply_async(mission_execution, [available_uav_id, mission_len])
                    # print('UAV ', available_uav_id, ' started on SAR Mission #', mission_no, 'including', uav_needed, 'UAV')
                    print(fleet_availability)

            mission_no += 1

        time.sleep(3)
