import time
import numpy as np

from rustypot import Sts3215PyController


ID_1 = 1 #Change to servo ID you want to calibrate 
ID_2 = 2 #Change to servo ID you want to calibrate 
MiddlePos_1 = 0 #Middle position offset for servo ID_1 
MiddlePos_2 = 0 #Middle position offset for servo ID_2


c = Sts3215PyController(
        serial_port="COM5",
        baudrate=1000000,
        timeout=0.5,
    )

def main():
    

    #c.write_torque_enable([1, 2], [True, True]) 
    #1 = On / 2 = Off / 3 = Free

    c.write_torque_enable(ID_1, True)
    c.write_torque_enable(ID_2, True)
    
    while True:
        

        CloseFinger()
        time.sleep(3)
        print(np.rad2deg(c.read_present_position(ID_1)))
        print(np.rad2deg(c.read_present_position(ID_2)))


        OpenFinger()
        time.sleep(1)
        print(np.rad2deg(c.read_present_position(ID_1)))
        print(np.rad2deg(c.read_present_position(ID_2)))



        print("  /  ")

        
        c.write_torque_enable(ID_1, False)
        c.write_torque_enable(ID_2, False)
        time.sleep(3)



def CloseFinger ():
    
    
    Pos_1 = np.deg2rad(MiddlePos_1+80)
    Pos_2 = np.deg2rad(MiddlePos_2-80)
    c.write_goal_position(ID_1, Pos_1)
    c.write_goal_position(ID_2, Pos_2)
    time.sleep(0.01)


def OpenFinger():
    
    Pos_1 = np.deg2rad(MiddlePos_1-30)
    Pos_2 = np.deg2rad(MiddlePos_2+30)
    c.write_goal_position(ID_1, Pos_1)
    c.write_goal_position(ID_2, Pos_2)
    
    time.sleep(0.01)






if __name__ == '__main__':
    main()


