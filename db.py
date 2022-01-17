import psycopg2
import psycopg2.extensions


row_insert_query = "insert into uav{} (uav_id, flight_mode, hb1, hb2, hb3, hb4, hb1_fac, hb2_fac, hb3_fac, hb4_fac, hc1, hc2, hc3, hc4, hc1_fac, hc2_fac, hc3_fac, hc4_fac, psb, psb_fac, psc, psc_fac, bat_h, " \
                   "hb1_fa, hb2_fa, hb3_fa, hb4_fa, hc1_fa, hc2_fa, hc3_fa, hc4_fa, psb_fa, psc_fa, no_missions, " \
                   "mission_mode, logs, mission_progress, health_index) values (%s, %s, %s, %s, " \
                   "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"


def init_database(uav_count: int) -> psycopg2.extensions.connection:
    """Erstellt für jede Drohne eine Tabelle in der Datenbank

    Args:
        uav_count(int): Die Anzahl an Drohnen

    Returns:
        psycopg2.extensions.connection: Verbindung zur Datenbank

    """
    # connect to postgres
    con = psycopg2.connect(
        host="localhost",
        database="rt_phm_simulation",
        user="postgres",
        password="R!3senfelge"
    )
    # cursor
    cur = con.cursor()

    for u in range(uav_count):
        cur.execute(f"drop table if exists uav{u+1}")
        # create empty uav table
        cur.execute(
            f"create table if not exists uav{u+1} (index serial primary key, uav_id integer,"
            " flight_mode real, hb1 real, hb2 real, hb3 real, hb4 real, hb1_fac real, hb2_fac real, hb3_fac real, hb4_fac real, hc1 real, hc2 real, hc3 real, hc4 real, hc1_fac real, hc2_fac real, hc3_fac real, hc4_fac real, psb real, psb_fac real, psc real, psc_fac real, bat_h real, "
            "hb1_fa real, hb2_fa real, hb3_fa real, hb4_fa real, hc1_fa real, hc2_fa real, hc3_fa real, hc4_fa real, psb_fa real, psc_fa real, no_missions integer, "
            "mission_mode real, logs real, mission_progress real, health_index real);")

    con.commit()
    cur.close()

    return con
