import time
import numpy as np

from rustypot import Sts3215PyController

#Side
Side = 1 # 1=> Right Hand // 2=> Left Hand


#Speed
MaxSpeed = 10
CloseSpeed = 3

#Fingers middle poses
MiddlePos = [8, -9, -2, -4, -2, 1, 3, -8] # replace values by your offset calibration results

c = Sts3215PyController(
        serial_port="COM5",
        baudrate=1000000,
        timeout=0.5,
    )



def main():
    
    c.write_torque_enable(1, True)
    c.write_torque_enable(2, True)
    c.write_torque_enable(3, True)
    c.write_torque_enable(4, True)
    c.write_torque_enable(5, True)
    c.write_torque_enable(6, True)
    c.write_torque_enable(7, True)
    c.write_torque_enable(8, True)
    t0 = time.time()


    Middle()
    time.sleep(3)

    while True:
        t = time.time() - t0

        OpenHand()
        time.sleep(0.5)

        CloseHand()
        time.sleep(3)

        OpenHand_Progressive()
        time.sleep(0.5)

        SpreadHand()
        time.sleep(0.6)
        ClenchHand()
        time.sleep(0.6)

        OpenHand()
        time.sleep(0.2)

        Index_Pointing()
        time.sleep(0.4)
        Nonono()
        time.sleep(0.5)
        
        OpenHand()
        time.sleep(0.3)

        Perfect()
        time.sleep(0.8)

        OpenHand()
        time.sleep(0.4)

        Victory()
        time.sleep(0.5)
        Scissors()
        time.sleep(0.5)

        OpenHand()
        time.sleep(0.4)

        Pinched()
        time.sleep(1.4)

        Fuck()
        time.sleep(0.8)



def Middle():
    Move_Index (-0,0, MaxSpeed)
    Move_Middle (-0,0, MaxSpeed)
    Move_Ring (-0,0, MaxSpeed)
    Move_Thumb (-0,0, MaxSpeed)

def OpenHand():
    Move_Index (-30,30, MaxSpeed)
    Move_Middle (-30,30, MaxSpeed)
    Move_Ring (-30,30, MaxSpeed)
    Move_Thumb (-30,30, MaxSpeed)

def CloseHand():
    Move_Index (80,-80, CloseSpeed)
    Move_Middle (80,-80, CloseSpeed)
    Move_Ring (80,-80, CloseSpeed)
    Move_Thumb (70,-70, CloseSpeed+1)

def OpenHand_Progressive():
    Move_Index (-30,30, MaxSpeed-2)
    time.sleep(0.2)
    Move_Middle (-30,30, MaxSpeed-2)
    time.sleep(0.2)
    Move_Ring (-30,30, MaxSpeed-2)
    time.sleep(0.2)
    Move_Thumb (-30,30, MaxSpeed-2)

def SpreadHand():
    if (Side==1): # Right Hand
        Move_Index (0, 65, MaxSpeed)
        Move_Middle (-30, 30, MaxSpeed)
        Move_Ring (-65, -0, MaxSpeed)
        Move_Thumb (-65, -0, MaxSpeed)  
  
    if (Side==2): # Left Hand
        Move_Index (-65, 0, MaxSpeed)
        Move_Middle (-30, 30, MaxSpeed)
        Move_Ring (-0, 65, MaxSpeed)
        Move_Thumb (-0, 65, MaxSpeed)  
  
def ClenchHand():
    if (Side==1): # Right Hand
        Move_Index (-50, 5, MaxSpeed)
        Move_Middle (-30, 30, MaxSpeed)
        Move_Ring (0, 55, MaxSpeed)
        Move_Thumb (-0, 65, MaxSpeed)  
  
    if (Side==2): # Left Hand
        Move_Index (-5, 50, MaxSpeed)
        Move_Middle (-30, 30, MaxSpeed)
        Move_Ring (-55, 0, MaxSpeed)
        Move_Thumb (-65, -0, MaxSpeed)
  
def Index_Pointing():
    Move_Index (-30, 30, MaxSpeed)
    Move_Middle (80, -80, MaxSpeed)
    Move_Ring (80, -80, MaxSpeed)
    Move_Thumb (80, -80, MaxSpeed)
  
def Nonono():
  Index_Pointing()
  for i in range(3) :
        time.sleep(0.2)
        Move_Index (-10, 80, MaxSpeed)
        time.sleep(0.2)
        Move_Index (-80, 10, MaxSpeed)
  
  Move_Index (-35, 35, MaxSpeed)
  time.sleep(0.4)
  
def Perfect():
  if (Side==1): #Right Hand
        Move_Index (45, -45, MaxSpeed-3)
        Move_Middle (0, -0, MaxSpeed)
        Move_Ring (-20, 20, MaxSpeed)
        Move_Thumb (50, 5, MaxSpeed)

  if (Side==2): #Left Hand
        Move_Index (45, -45, MaxSpeed-3)
        Move_Middle (0, -0, MaxSpeed)
        Move_Ring (-20, 20, MaxSpeed)
        Move_Thumb (-5, -50, MaxSpeed)

def Victory():
  if (Side==1): #Right Hand 
        Move_Index (-15, 65, MaxSpeed)
        Move_Middle (-65, 15, MaxSpeed)
        Move_Ring (80, -80, MaxSpeed)
        Move_Thumb (80, -80, MaxSpeed)

  if (Side==2): #Left Hand
        Move_Index (-65, 15, MaxSpeed)
        Move_Middle (-15, 65, MaxSpeed)
        Move_Ring (80, -80, MaxSpeed)
        Move_Thumb (80, -80, MaxSpeed)


def Scissors():
  Victory()
  if (Side==1): #Right Hand
        for i in range(3):  
            time.sleep(0.2)
            Move_Index (-50, 20, MaxSpeed)
            Move_Middle (-20, 50, MaxSpeed)
            
            time.sleep(0.2)
            Move_Index (-15, 65, MaxSpeed)
            Move_Middle (-65, 15, MaxSpeed)
    

  if (Side==2): #Left Hand
        for i in range(3):
            time.sleep(0.2)
            Move_Index (-20, 50, MaxSpeed)
            Move_Middle (-50, 20, MaxSpeed)
            
            time.sleep(0.2)
            Move_Index (-65, 15, MaxSpeed)
            Move_Middle (-15, 65, MaxSpeed)

def Pinched():
  if (Side==1): #Right Hand
        Move_Index (80, -80, MaxSpeed)
        Move_Thumb (-10, -80, MaxSpeed)
        Move_Middle (80, -80, MaxSpeed)
        Move_Ring (80, -80, MaxSpeed)
        

  if (Side==2): #Left Hand
        Move_Index (80, -80, MaxSpeed)
        Move_Thumb (80, 10, MaxSpeed)
        Move_Middle (80, -80, MaxSpeed)
        Move_Ring (80, -80, MaxSpeed)
        

def Fuck():

  if (Side==1): #Right Hand
        Move_Index (80, -80, MaxSpeed)
        Move_Middle (-30, 30, MaxSpeed)
        Move_Ring (80, -80, MaxSpeed)
        Move_Thumb (-10, -80, MaxSpeed)

  if (Side==2): #Left Hand
        Move_Index (80, -80, MaxSpeed)
        Move_Middle (-30, 30, MaxSpeed)
        Move_Ring (80, -80, MaxSpeed)
        Move_Thumb (80, 10, MaxSpeed)
  
def Move_Index (Angle_1,Angle_2,Speed):
    
    c.sync_write_goal_speed([1,2], [Speed, Speed])
    time.sleep(0.0005) 
    Pos_1 = np.deg2rad(MiddlePos[0]+Angle_1)
    Pos_2 = np.deg2rad(MiddlePos[1]+Angle_2) 
    c.sync_write_goal_position([1,2], [Pos_1,Pos_2])
    time.sleep(0.0005)

def Move_Middle(Angle_1,Angle_2,Speed):    
    c.sync_write_goal_speed([3,4], [Speed, Speed])
    time.sleep(0.0005)
    Pos_1 = np.deg2rad(MiddlePos[2]+Angle_1)
    Pos_2 = np.deg2rad(MiddlePos[3]+Angle_2)
    c.sync_write_goal_position([3,4], [Pos_1,Pos_2])
    time.sleep(0.0005)

def Move_Ring(Angle_1,Angle_2,Speed):    
    c.sync_write_goal_speed([5,6], [Speed, Speed])
    time.sleep(0.0005)
    Pos_1 = np.deg2rad(MiddlePos[4]+Angle_1)
    Pos_2 = np.deg2rad(MiddlePos[5]+Angle_2)
    c.sync_write_goal_position([5,6], [Pos_1,Pos_2])
    time.sleep(0.0005)

def Move_Thumb(Angle_1,Angle_2,Speed):    
    c.sync_write_goal_speed([7,8], [Speed, Speed])
    time.sleep(0.0005)
    Pos_1 = np.deg2rad(MiddlePos[6]+Angle_1)
    Pos_2 = np.deg2rad(MiddlePos[7]+Angle_2)
    c.sync_write_goal_position([7,8], [Pos_1,Pos_2])
    time.sleep(0.0005)


if __name__ == '__main__':
    main()



