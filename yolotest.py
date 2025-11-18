import cv2
import torch
from ultralytics import YOLO
import numpy as np
import time

class CondaYOLODetector:
    def __init__(self, model_size='m'):
        print("🚀 初始化 YOLO 物体检测器...")
        print(f"✅ PyTorch 版本: {torch.__version__}")
        print(f"✅ CUDA 可用: {torch.cuda.is_available()}")
        
        # 加载 YOLO 模型
        self.model = YOLO(f'yolov8{model_size}.pt')
        
        # 物体到气味的映射
        self.scent_mapping = {
            'potted plant': ['植物清香', '绿叶气息'],
            'vase': ['花香', '植物芳香'],
            'apple': ['苹果香', '果香'],
            'orange': ['橙子香', '柑橘调'],
            'banana': ['香蕉味', '甜香'],
            'wine glass': ['葡萄酒香', '果酒气息'],
            'cup': ['饮品香气', '热饮香'],
            'bottle': ['瓶中物气味', '液体香气'],
        }
        
        print("✅ 检测器初始化完成")
    
    def detect_objects(self, frame, confidence=0.5):
        """检测物体并返回气味信息"""
        results = self.model(frame, verbose=False)
        
        detected_scents = []
        detection_info = []
        
        for result in results:
            for box in result.boxes:
                if float(box.conf) > confidence:
                    class_id = int(box.cls)
                    class_name = result.names[class_id]
                    
                    # 获取边界框坐标
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    # 获取气味信息
                    scents = self.scent_mapping.get(class_name, [])
                    detected_scents.extend(scents)
                    
                    detection_info.append({
                        'class': class_name,
                        'confidence': float(box.conf),
                        'bbox': (x1, y1, x2, y2),
                        'scents': scents
                    })
        
        return list(set(detected_scents)), detection_info
    
    def draw_detections(self, frame, detection_info):
        """在图像上绘制检测结果"""
        for info in detection_info:
            x1, y1, x2, y2 = info['bbox']
            
            # 绘制边界框
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # 绘制标签
            label = f"{info['class']} {info['confidence']:.2f}"
            cv2.putText(frame, label, (x1, y1 - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # 绘制气味信息
            if info['scents']:
                scent_text = f"Scent: {', '.join(info['scents'])}"
                cv2.putText(frame, scent_text, (x1, y1 - 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
        
        return frame
    def run_webcam_detection(self, camera_id=0):
        """运行摄像头实时检测"""
        print("📷 启动摄像头检测...")
        cap = cv2.VideoCapture(camera_id)
        #cap = cv2.VideoCapture("input.mp4")
        if not cap.isOpened():
            print("❌ 无法打开摄像头")
            return
        
        print("✅ 摄像头已打开")
        print("🎮 控制: 按 'q' 退出, 按 'p' 暂停")
        
        paused = False
        frame_count = 0
        start_time = time.time()
        
        while True:
            if not paused:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # 物体检测
                detection_start = time.time()
                scents, detection_info = self.detect_objects(frame)
                detection_time = time.time() - detection_start
                
                # 绘制检测结果
                frame = self.draw_detections(frame, detection_info)
                
                # 添加信息面板
                current_fps = frame_count / (time.time() - start_time)
                cv2.putText(frame, f"FPS: {current_fps:.1f}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f"Detected: {len(detection_info)}", (10, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                
                if scents:
                    scent_text = f"Scents: {', '.join(scents)}"
                    cv2.putText(frame, scent_text, (10, 90), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                
                # 显示结果
                cv2.imshow('YOLO物体检测 - 气味识别', frame)
            
            # 键盘控制
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('p'):
                paused = not paused
                print("⏸️ 暂停" if paused else "▶️ 继续")
        
        # 清理资源
        cap.release()
        cv2.destroyAllWindows()
        
        total_time = time.time() - start_time
        print(f"\n📊 统计信息:")
        print(f"总帧数: {frame_count}")
        print(f"总时间: {total_time:.2f}s")
        print(f"平均FPS: {frame_count/total_time:.2f}")

if __name__ == "__main__":
    # 创建检测器
    detector = CondaYOLODetector(model_size='m')
    
    # 运行摄像头检测
    detector.run_webcam_detection()