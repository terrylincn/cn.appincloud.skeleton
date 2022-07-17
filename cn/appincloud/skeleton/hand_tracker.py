import filecmp
import  cv2
import  mediapipe  as  mp
import sys

def  hand_process(cam_id=0):
    mp_drawing  =  mp.solutions.drawing_utils
    mp_drawing_styles  =  mp.solutions.drawing_styles
    mp_hands  =  mp.solutions.hands
    #  For  webcam  input:
    cap  =  cv2.VideoCapture(cam_id)

    with  mp_hands.Hands(
            model_complexity=0,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5)  as  hands:
        while  cap.isOpened():
            success,  image  =  cap.read()
            if  not  success:
                print("Ignoring  empty  camera  frame.")
                #  If  loading  a  video,  use  'break'  instead  of  'continue'.
                continue

            #  To  improve  performance,  optionally  mark  the  image  as  not  writeable  to
            #  pass  by  reference.
            image.flags.writeable  =  False
            image  =  cv2.cvtColor(image,  cv2.COLOR_BGR2RGB)
            results  =  hands.process(image)

            #  Draw  the  hand  annotations  on  the  image.
            image.flags.writeable  =  True
            image  =  cv2.cvtColor(image,  cv2.COLOR_RGB2BGR)
            if  results.multi_hand_landmarks:
                for  hand_landmarks  in  results.multi_hand_landmarks:
                    print(hand_landmarks)
                    mp_drawing.draw_landmarks(
                            image,
                            hand_landmarks,
                            mp_hands.HAND_CONNECTIONS,
                            mp_drawing_styles.get_default_hand_landmarks_style(),
                            mp_drawing_styles.get_default_hand_connections_style())
            #  Flip  the  image  horizontally  for  a  selfie-view  display.
            cv2.imshow('MediaPipe  Hands',  cv2.flip(image,  1))
            if  cv2.waitKey(5)  &  0xFF  ==  27:
                break
    cap.release()

def landmark2text(landmark):
    txt = ""
    for mark in landmark:
        one = "{} {} {}".format(mark.x,mark.y,mark.z)
        if txt != "":
            txt += " "
        txt += one
    return txt + "\n"

def handpose2kpts(videofile):
    txt = ""
    mp_drawing  =  mp.solutions.drawing_utils
    mp_drawing_styles  =  mp.solutions.drawing_styles
    mp_hands  =  mp.solutions.hands
    #  For  webcam  input:
    cap  =  cv2.VideoCapture(videofile)

    with  mp_hands.Hands(
            model_complexity=0,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5)  as  hands:
        while  cap.isOpened():
            success,  image  =  cap.read()
            if  not  success:
                print("Ignoring  empty  camera  frame.")
                #  If  loading  a  video,  use  'break'  instead  of  'continue'.
                break

            #  To  improve  performance,  optionally  mark  the  image  as  not  writeable  to
            #  pass  by  reference.
            image.flags.writeable  =  False
            image  =  cv2.cvtColor(image,  cv2.COLOR_BGR2RGB)
            results  =  hands.process(image)

            #  Draw  the  hand  annotations  on  the  image.
            image.flags.writeable  =  True
            image  =  cv2.cvtColor(image,  cv2.COLOR_RGB2BGR)
            if  results.multi_hand_landmarks:
                handedness = [
                    handedness.classification[0].label
                    for handedness in results.multi_handedness
                ]
                if "Left" not in handedness:
                    continue
                index = 0
                for  hand_landmarks  in  results.multi_hand_landmarks:
                    #only output right hand
                    if handedness.index("Left") == index:
                        txt += landmark2text(hand_landmarks.landmark)
                    index += 1

    cap.release()
    return txt



class HandTracker:
    def __init__(self):
        mp_hands  =  mp.solutions.hands
        self._hands = mp_hands.Hands(
            model_complexity=0,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5)
    
    def process(self, image):
        left_hand = None
        right_hand = None
        image.flags.writeable  =  False
        image  =  cv2.cvtColor(image,  cv2.COLOR_BGR2RGB)
        results  =  self._hands.process(image)
        if  results.multi_hand_landmarks:
            for  hand_landmarks  in  results.multi_hand_landmarks:
                print(hand_landmarks)
        return left_hand, right_hand

if __name__ == "__main__":
    #cam_id = int(sys.argv[1])
    #hand_process(cam_id)
    filepath = sys.argv[1]
    outfile = sys.argv[2]
    txt = handpose2kpts(filepath)
    with open(outfile, "w") as fp:
        fp.write(txt)