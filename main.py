import cv2
import numpy as np

# import video

if __name__ == '__main__':
    def callback(*arg):
        print(arg)

cv2.namedWindow("result")

# cap = video.create_capture(0)
cap = cv2.VideoCapture(0)

# Зеленый цвет
# hsv_min = np.array((53, 55, 147), np.uint8)
# hsv_max = np.array((83, 160, 255), np.uint8)

# Желтый цвет настроить
y_hsv_min = np.array((19, 194, 104), np.uint8)
y_hsv_max = np.array((38, 255, 208), np.uint8)

# Красный цвет
r_hsv_min = np.array((0, 184, 118), np.uint8)
r_hsv_max = np.array((3, 255, 253), np.uint8)

color_yellow = (0, 255, 255)

while True:
    flag, img = cap.read()
    img = cv2.flip(img, 1)  # отражение кадра вдоль оси Y
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # Распознавание желтого куба
    y_thresh = cv2.inRange(hsv, y_hsv_min, y_hsv_max)

    y_moments = cv2.moments(y_thresh, 1)
    dM01 = y_moments['m01']
    dM10 = y_moments['m10']
    dArea = y_moments['m00']
    # Отрисовка желтого куба
    if dArea > 100:
        x = int(dM10 / dArea)
        y = int(dM01 / dArea)
        cv2.circle(img, (x, y), 5, color_yellow, 2)
        cv2.putText(img, "%d-%d" % (x, y), (x + 10, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, color_yellow, 2)

    # Распознование красного куба
    r_thresh = cv2.inRange(hsv, r_hsv_min, r_hsv_max)
    r_moments = cv2.moments(r_thresh, 1)

    dM01 = r_moments['m01']
    dM10 = r_moments['m10']
    dArea = r_moments['m00']
    # Отрисовка красного куба
    if dArea > 100:
        x = int(dM10 / dArea)
        y = int(dM01 / dArea)
        cv2.circle(img, (x, y), 5, color_yellow, 2)
        cv2.putText(img, "%d-%d" % (x, y), (x + 10, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, color_yellow, 2)
    cv2.imshow('result', img)

    ch = cv2.waitKey(5)
    if ch == 27:
        break

cap.release()
cv2.destroyAllWindows()
