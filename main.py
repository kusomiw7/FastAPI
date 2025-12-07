from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from io import BytesIO
import numpy as np

# 設置 FastAPI 應用
app = FastAPI(title="GIF Service")

# 允許 CORS (跨來源資源共享) 設置
# 這裡使用 "*" 允許所有來源，以確保您的前端網頁能夠連線成功。
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # 允許所有 HTTP 方法 (POST, GET, etc.)
    allow_headers=["*"],  # 允許所有請求頭
)

# 根路徑，用於健康檢查和喚醒服務
@app.get("/")
def read_root():
    return {"message": "Welcome to the Giftwno1 FastAPI GIF Service. Use POST /generate/ to create a GIF."}

# GIF 生成端點
@app.post("/generate/")
async def generate_gif(file: UploadFile = File(...)):
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image.")

    try:
        # 1. 讀取上傳的圖片
        image_data = await file.read()
        img = Image.open(BytesIO(image_data)).convert("RGB")

        # 2. 定義 GIF 參數 (這與前端代碼中的設定是固定的)
        target_size = (300, 300)
        num_frames = 10 
        delay_ms = 100 # 每幀延遲 100 毫秒

        # 3. 調整圖片大小以符合 Ken Burns 效果所需的裁剪
        zoom_factor = 1.3
        max_process_w = int(target_size[0] * zoom_factor)
        max_process_h = int(target_size[1] * zoom_factor)
        
        # 確保圖片能完全覆蓋最大裁剪尺寸
        scale_factor = max(max_process_w / img.width, max_process_h / img.height)
        scaled_img = img.resize((int(img.width * scale_factor), int(img.height * scale_factor)))
        
        img_w, img_h = scaled_img.size
        
        # 4. 生成 Ken Burns 動畫幀
        frames = []
        for i in range(num_frames):
            # 線性從 1.0 (近景) 縮放至 1.3 (遠景) - 反向 Zoom Out 效果
            current_zoom_ratio = 1.0 + (zoom_factor - 1.0) * (i / (num_frames - 1))
            
            # 計算裁剪尺寸 (保持在 target_size 比例)
            crop_w = target_size[0] * current_zoom_ratio
            crop_h = target_size[1] * current_zoom_ratio
            
            # 將裁剪框置中
            crop_x = (img_w - crop_w) / 2
            crop_y = (img_h - crop_h) / 2
            
            # 裁剪圖片
            cropped_img = scaled_img.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))
            
            # 調整裁剪後的圖片大小至最終輸出尺寸
            final_frame = cropped_img.resize(target_size, Image.LANCZOS)
            frames.append(final_frame)

        # 5. 將所有幀組合成 GIF
        gif_buffer = BytesIO()
        if frames:
            # 儲存為 GIF
            frames[0].save(
                gif_buffer, 
                format='GIF', 
                save_all=True, 
                append_images=frames[1:], 
                duration=delay_ms, 
                loop=0,  # 循環播放
                optimize=True
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to generate frames.")

        gif_data = gif_buffer.getvalue()

        # 6. 回傳 GIF 響應
        return Response(content=gif_data, media_type="image/gif")

    except Exception as e:
        print(f"Error during GIF generation: {e}")
        # 在伺服器端發生錯誤時，回傳詳細錯誤訊息
        raise HTTPException(status_code=500, detail=f"Server failed to process the image: {e}")

# 設置完成後，Render 會使用 uvicorn main:app --host 0.0.0.0 --port 10000 來啟動它
