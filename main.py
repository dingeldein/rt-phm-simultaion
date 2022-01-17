from mission_type import MissionType, mission_duration
import matplotlib.pyplot as plt
from mission_execution import mission_execution
import random
import pandas as pd
from uav import UAV
from pathlib import Path
from db import init_database
import numpy as np
from mission_execution import mission_execution
import time
import multiprocessing as mp

len_uav_array = 27
NUMBER_OF_UAVS = 10
no_ex_missions = 200 # Anzahl Missionen pro Drohne


def main(show_graphs=True) -> None:
    """Die main-Funktion des Projekts:
    Zuerst wird eine Verbindung zur Datenbank hergestellt, dann wird in einer Schleife
    für jede Drone Missionen simuliert und anschließend ausgewählte Werte in Graphen dargestellt."""

    # erstellt data Ordner, falls nicht vorhanden
    Path("data").mkdir(parents=True, exist_ok=True)

    con = init_database(NUMBER_OF_UAVS)
    # cursor
    cur = con.cursor()

    Path("data").mkdir(parents=True, exist_ok=True)

    uavs = []
    for i in range(NUMBER_OF_UAVS):
        uav = UAV(i+1)
        uavs.append(uav)

        # insert initial health into database
        uav.store_to_database(con, cur)
        print("UAV {} initialized".format(i+1))

        # for j in range(no_ex_missions):
        #     mission_type = random.choice(list(MissionType))
        #     uav.mission_type = mission_type.value
        #     mission_length = random.randint(*mission_duration[mission_type])
        #     print('No. of Mission: ', j, '\t\tMission Type: ', mission_type.name, '\t\tLength: ', mission_length)
        #     mission_execution(uav, mission_length)
        #
        # cur.execute(f'select * from uav{uav.uav_id}')
        # uav_complete = pd.DataFrame(cur.fetchall())
        # uav_complete.to_csv(f'data/complete_health_uav{uav.uav_id}.csv', sep=",", header=False)
        #
        # if show_graphs:
        #     fig = plt.figure()
        #     fig.set_figwidth(15)
        #     ax = plt.subplot(111)
        #     bearing_col_list = ['C0', 'C1', 'C2', 'C3']
        #     for j in range(len(uav.hover_bearing_health)):
        #         ax.plot(uav_complete.iloc[:, 3 + j], color=bearing_col_list[j], alpha=0.3, label=f"Hover {j} bearing health")
        #
        #     coil_col_list = ['C4', 'C5', 'C6', 'C7']
        #     for j in range(len(uav.hover_coil_health)):
        #         ax.plot(uav_complete.iloc[:, 11 + j], color=coil_col_list[j], alpha=0.3, label=f"Hover {j} coil health")
        #
        #     ax.plot(uav_complete.iloc[:, 19], color='C8', alpha=0.3, label="Pusher bearing health")
        #     ax.plot(uav_complete.iloc[:, 21], color='C9', alpha=0.3, label="Pusher coil health")
        #     ax.plot(uav_complete.iloc[:, 23], alpha=0.2, label="Battery capacity")
        #     plt.plot(uav_complete.iloc[:, 38], 'k', label="Health Index")
        #     ax.legend(loc='center left', bbox_to_anchor=(1.04, 0.68))
        #     ax.set_xlabel("Time in min")
        #     ax.set_ylabel("Health grade")
        #     ax.grid(True)
        #     #ax.set_ylim(0, 1)
        #     ax.set_title("UAV {} Degradation".format(i+1))
        #     plt.subplots_adjust(right=0.8)
        #     plt.show()

    time.sleep(3)

    mission_queue = np.genfromtxt("mission_queue.csv", delimiter=",")
    pool = mp.Pool(NUMBER_OF_UAVS)

    mission_no = 1
    fleet_availability = np.zeros((NUMBER_OF_UAVS))
    while True:
        # check pending mission and get number of UAV needed
        uav_needed = len(mission_queue[mission_queue[:, 0] == mission_no])

        # check number of UAV available
        for i in range(10):
            cur.execute('select mission_mode from uav{} order by index desc limit 1'.format(i + 1))
            uav_status = np.array(cur.fetchall())
            fleet_availability[i] = np.round(int(uav_status))
        # print("Before mission fleet availability: ", fleet_availability)
        uav_available = len(np.where(fleet_availability == 2)[0])
        print(fleet_availability)
        print('Available UAV: ', uav_available, ' -  Needed UAV: ', uav_needed)

        # assign mission
        if uav_needed <= uav_available:

            if mission_queue[mission_queue[:, 0] == mission_no][0, 1] == 0:
                # delivery mission
                print("Delivery mission in queue")
                # get available UAV [integration of health dependend selection HERE; instead of min]
                available_uav_id = np.where(fleet_availability == 2)[0][0] + 1
                # get latest health values and update class
                cur.execute("select hb1, hb2, hb3, hb4, hb1_fac, hb2_fac, hb3_fac, hb4_fac, hc1, hc2, hc3, hc4, "
                            "hc1_fac, hc2_fac, hc3_fac, hc4_fac, psb, psb_fac, psc, psc_fac, bat_h, no_missions "
                            "from uav{} order by index desc limit 1".format(available_uav_id))
                latest_uav_values = np.array(cur.fetchall())[0]
                print(available_uav_id)
                uavs[available_uav_id-1].mission_mode = 3
                uavs[available_uav_id-1].hover_bearing_health = latest_uav_values[0:4]
                uavs[available_uav_id-1].hover_bearing_factors = latest_uav_values[4:8]
                uavs[available_uav_id-1].hover_coil_health = latest_uav_values[8:12]
                uavs[available_uav_id-1].hover_coil_factors = latest_uav_values[12:16]
                uavs[available_uav_id-1].pusher_bearing_health = latest_uav_values[16]
                uavs[available_uav_id-1].pusher_bearing_factor = latest_uav_values[17]
                uavs[available_uav_id-1].pusher_coil_health = latest_uav_values[18]
                uavs[available_uav_id-1].pusher_coil_factor = latest_uav_values[19]
                uavs[available_uav_id-1].battery_level = latest_uav_values[20]
                uavs[available_uav_id-1].number_of_missions = latest_uav_values[21]

                #define mission parameters
                mission_type = list(MissionType)[0]
                uavs[available_uav_id-1].mission_type = mission_type.value
                mission_len = mission_queue[mission_queue[:, 0] == mission_no][0, 3]
                print("UAV to be sent on delivery mission: ", available_uav_id)
                fleet_availability[available_uav_id - 1] = False
                pool.apply_async(mission_execution, [uavs[available_uav_id-1], mission_len])
                # print('UAV ', available_uav_id, ' started on Delivery Mission #', mission_no)

            if mission_queue[mission_queue[:, 0] == mission_no][0, 1] == 1:
                # reconnaissance mission
                print("SAR mission in queue")
                # get available UAV [integration of health dependend selection HERE]
                mission_len = mission_queue[mission_queue[:, 0] == mission_no][0, 3]
                for j in range(uav_needed):
                    available_uav_id = np.where(fleet_availability == 2)[0][0] + 1
                    # get latest health values and update class
                    cur.execute("select hb1, hb2, hb3, hb4, hb1_fac, hb2_fac, hb3_fac, hb4_fac, hc1, hc2, hc3, hc4, "
                                "hc1_fac, hc2_fac, hc3_fac, hc4_fac, psb, psb_fac, psc, psc_fac, bat_h, no_missions "
                                "from uav{} order by index desc limit 1".format(available_uav_id))
                    latest_uav_values = np.array(cur.fetchall())[0]
                    print(available_uav_id)
                    uavs[available_uav_id-1].mission_mode = 3
                    uavs[available_uav_id-1].hover_bearing_health = latest_uav_values[0:4]
                    uavs[available_uav_id-1].hover_bearing_factors = latest_uav_values[4:8]
                    uavs[available_uav_id-1].hover_coil_health = latest_uav_values[8:12]
                    uavs[available_uav_id-1].hover_coil_factors = latest_uav_values[12:16]
                    uavs[available_uav_id-1].pusher_bearing_health = latest_uav_values[16]
                    uavs[available_uav_id-1].pusher_bearing_factor = latest_uav_values[17]
                    uavs[available_uav_id-1].pusher_coil_health = latest_uav_values[18]
                    uavs[available_uav_id-1].pusher_coil_factor = latest_uav_values[19]
                    uavs[available_uav_id-1].battery_level = latest_uav_values[20]
                    uavs[available_uav_id-1].number_of_missions = latest_uav_values[21]

                    # define mission parameters
                    mission_type = list(MissionType)[1]
                    uavs[available_uav_id-1].mission_type = mission_type.value
                    print("UAV to be sent on SAR mission: ", available_uav_id)
                    fleet_availability[available_uav_id - 1] = False

                    pool.apply_async(mission_execution, [uavs[available_uav_id-1], mission_len])
                    # print('UAV ', available_uav_id, ' started on SAR Mission #', mission_no, 'including', uav_needed, 'UAV')

            mission_no += 1

        time.sleep(4)

    # close cursor
    cur.close()
    # close database
    con.close()



if __name__ == '__main__':
    main()
