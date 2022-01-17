from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys
import qdarkstyle
import psycopg2
import pandas as pd

conn = psycopg2.connect("host='localhost' dbname='rt_phm_simulation' user='postgres' password='R!3senfelge'")


class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        # setting title
        self.setWindowTitle("Fleet Health Dashboard")

        # setting geometry
        self.setGeometry(200, 200, 840, 540)

        # make QTimer
        self.qTimer = QTimer()
        self.qTimer.setInterval(300)
        self.qTimer.timeout.connect(self.get_cur_status)
        self.qTimer.start()

        # calling method
        self.UiComponents()


        # Show window
        self.show()

    # method for widgets
    def UiComponents(self):

        self.tableWidget = QTableWidget(self)
        self.tableWidget.setGeometry(QRect(20, 20, 800, 490))
        self.tableWidget.setRowCount(10)
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setVerticalHeaderLabels(["UAV 1", "UAV 2", "UAV 3", "UAV 4", "UAV 5", "UAV 6", "UAV 7", "UAV 8", "UAV 9", "UAV 10"])
        self.tableWidget.setHorizontalHeaderLabels(["Overall Health", "Battery Charge", "Mission Progress", "UAV Status"])

        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch)


    def get_cur_status(self):
        mission_mode = ['Delivery Mission',
                        'SAR Mission',
                        'available',
                        'in mission preparation',
                        'R2H triggered',
                        'in maintenance']

# "insert into uav{} (uav_id, flight_mode, hb1, hb2, hb3, hb4, hb1_fac, hb2_fac, hb3_fac, hb4_fac, hc1, hc2, hc3, hc4, hc1_fac, hc2_fac, hc3_fac, hc4_fac, psb, psb_fac, psc, psc_fac, bat_h, " \
# "hb1_fa, hb2_fa, hb3_fa, hb4_fa, hc1_fa, hc2_fa, hc3_fa, hc4_fa, psb_fa, psc_fa, no_missions, " \
# "mission_mode, logs, mission_progress, health_index) "

        for i in range(10):
            tab_entries = pd.read_sql_query('select least(hb1, hb2, hb3, hb4, hc1, hc2, hc3, hc4, psb, psc), bat_h, mission_mode, mission_progress from uav{} order by index desc limit 1'.format(i+1), conn)
            self.tableWidget.setItem(i, 0, QTableWidgetItem(str(round(float(tab_entries.least[0]*100), 2))))
            self.tableWidget.setItem(i, 1, QTableWidgetItem(str(round(float(tab_entries.bat_h[0]*100), 2))))
            self.tableWidget.setItem(i, 2, QTableWidgetItem(str(round(float(tab_entries.mission_progress[0]), 2))))
            self.tableWidget.setItem(i, 3, QTableWidgetItem(mission_mode[int(tab_entries.mission_mode[0])]))


# create pyqt5 app
App = QApplication(sys.argv)

# create the instance of our Window
window = Window()
App.setStyleSheet(qdarkstyle.load_stylesheet())

# start the app
sys.exit(App.exec())
