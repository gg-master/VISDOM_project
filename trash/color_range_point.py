import cv2
import time

if __name__ == '__main__':
    cv2.namedWindow("result")

cap = cv2.VideoCapture(0)

color_yellow = (0, 255, 255)
color_green = (0, 255, 0)
start_time = time.time()
while True:

    if time.time() - start_time >= 20:
        break
    time_late = 20 - round(time.time() - start_time)
    flag, img = cap.read()

    img = cv2.flip(img, 1)
    height, width = img.shape[:2]
    try:
        x1, y1, x2, y2 = (width // 2 - 50, height // 2 - 50,
                          width // 2 + 50, height // 2 + 50)
        h, w = y2 - y1, x2 - x1
        # Словарь с точками, в которых будут анализироваться пиксели
        dots = {1: (x1 + (w // 2), y1 + (h // 2)),
                2: (x1 + (w // 2), y1 + (h // 4)),
                3: (x1 + (w // 4), y1 + (h // 2)),
                4: (x1 + (w // 2), y2 - (h // 4)),
                5: (x2 - (w // 4), y1 + (h // 2))}
        cv2.rectangle(img, (x1, y1), (x2, y2), color_green, 1)
        # Центр
        cv2.circle(img, dots[1], 2, color_green, -1)
        # Верх
        cv2.circle(img, dots[2], 2, color_green, -1)
        # Лево
        cv2.circle(img, dots[3], 2, color_green, -1)
        # Низ
        cv2.circle(img, dots[4], 2, color_green, -1)
        # Право
        cv2.circle(img, dots[5], 2, color_green, -1)
        cv2.putText(img, f'{time_late}', (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, color_yellow, 2)
        print(img[dots[1]])
        cv2.imshow('result', img)
    except:
        cap.release()
        raise

    ch = cv2.waitKey(5)
    if ch == 27:
        break

cap.release()
cv2.destroyAllWindows()
