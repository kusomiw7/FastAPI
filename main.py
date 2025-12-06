from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import Response
from PIL import Image
import io

app = FastAPI(title="FastAPI GIF Generator")

@app.get("/")
async def root():
    """服務健康檢查與歡迎訊息"""
    return {"message": "Welcome to the Giftwno1 FastAPI GIF Service. Use POST /generate/ to create a GIF."}

@app.post("/generate/")
async def create_gif_from_image(
    file: UploadFile = File(...),
):
    """
    接收單張圖片 (JPG/PNG)，將其轉換為一個簡單的 GIF 檔案並回傳。
    
    此處僅為確保 Render 部署成功的簡化範例，
    您可以根據需求擴展此處來實現更複雜的 Ken Burns 效果。
    """
    # 1. 讀取上傳的圖片內容
    image_data = await file.read()
    
    try:
        # 2. 使用 Pillow 開啟圖片
        original_image = Image.open(io.BytesIO(image_data))
        
        # 3. 圖片處理：確保顏色模式兼容 GIF
        if original_image.mode != "RGB":
            original_image = original_image.convert("RGB")

        # 4. 設定最大尺寸 (確保服務不會因處理超大圖而崩潰)
        max_size = 300
        original_image.thumbnail((max_size, max_size))
        
        # 5. 儲存為 GIF 格式到記憶體
        output = io.BytesIO()
        
        # 創建一個單幀 GIF (循環播放)
        original_image.save(
            output, 
            format="GIF", 
            save_all=True, 
            append_images=[],
            duration=100, # 每一幀顯示 100 毫秒
            loop=0 # 永遠循環
        )
        
        output.seek(0)
        
        # 6. 回傳 GIF 檔案
        return Response(content=output.getvalue(), media_type="image/gif")

    except Exception as e:
        # 處理圖片錯誤
        return Response(content=f"Error processing image: {str(e)}", status_code=500, media_type="text/plain")
