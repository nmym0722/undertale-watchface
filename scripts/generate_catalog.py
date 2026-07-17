import os
import shutil
import math
from PIL import Image, ImageDraw, ImageFont

# パスの定義
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_CHAR_DIR = os.path.join(BASE_DIR, "assets", "raw", "characters")
OUT_CATALOG_DIR = os.path.join(BASE_DIR, "assets", "raw", "catalogs")
ARTIFACT_DIR = r"C:\Users\daich\.gemini\antigravity-ide\brain\4b175843-f287-47a2-9760-1570df73453b"

# ディレクトリの作成
os.makedirs(OUT_CATALOG_DIR, exist_ok=True)

def make_background_transparent(img):
    """
    画像の左上隅 (0, 0) の色を背景透過色（クロマキー）として自動検出し、
    その色に極めて近いピクセルを完全透過 (A=0) に変換したRGBA画像を返します。
    """
    img = img.convert("RGBA")
    width, height = img.size
    pixels = img.load()
    
    bg_r, bg_g, bg_b, _ = pixels[0, 0]
    
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if abs(r - bg_r) < 15 and abs(g - bg_g) < 15 and abs(b - bg_b) < 15:
                pixels[x, y] = (0, 0, 0, 0)
            else:
                if a == 255:
                    pixels[x, y] = (r, g, b, 255)
    return img

def split_frame(img, box):
    """
    再帰的バウンディングボックス分割（内側境界スキャン版）。
    画像の端にある外側余白を無視し、画像の内側にある透明な隙間（境界）だけを検出して分割します。
    """
    cropped = img.crop(box)
    width, height = cropped.size
    
    pixels = list(cropped.getdata())
    
    row_opaque_count = [0] * height
    col_opaque_count = [0] * width
    for y in range(height):
        for x in range(width):
            alpha = pixels[y * width + x][3]
            if alpha > 15:
                row_opaque_count[y] += 1
                col_opaque_count[x] += 1
                
    row_transparent = [count <= 2 for count in row_opaque_count]
    col_transparent = [count <= 2 for count in col_opaque_count]
                
    # 1. 垂直方向に分割可能な透明列を検索（内側の 1 から width-2 まで）
    split_x = -1
    for x in range(1, width - 1):
        if col_transparent[x]:
            split_x = x
            break
            
    if split_x != -1:
        end_split_x = split_x
        while end_split_x < width - 1 and col_transparent[end_split_x]:
            end_split_x += 1
            
        box_left = (box[0], box[1], box[0] + split_x, box[3])
        box_right = (box[0] + end_split_x, box[1], box[2], box[3])
        
        l_img = img.crop(box_left)
        r_img = img.crop(box_right)
        l_bbox = l_img.getbbox()
        r_bbox = r_img.getbbox()
        
        res_left = split_frame(img, (box_left[0]+l_bbox[0], box_left[1]+l_bbox[1], box_left[0]+l_bbox[2], box_left[1]+l_bbox[3])) if l_bbox else []
        res_right = split_frame(img, (box_right[0]+r_bbox[0], box_right[1]+r_bbox[1], box_right[0]+r_bbox[2], box_right[1]+r_bbox[3])) if r_bbox else []
        return res_left + res_right

    # 2. 水平方向に分割可能な透明行を検索（内側の 1 から height-2 まで）
    split_y = -1
    for y in range(1, height - 1):
        if row_transparent[y]:
            split_y = y
            break
            
    if split_y != -1:
        end_split_y = split_y
        while end_split_y < height - 1 and row_transparent[end_split_y]:
            end_split_y += 1
            
        box_top = (box[0], box[1], box[2], box[1] + split_y)
        box_bottom = (box[0], box[1] + end_split_y, box[2], box[3])
        
        t_img = img.crop(box_top)
        b_img = img.crop(box_bottom)
        t_bbox = t_img.getbbox()
        b_bbox = b_img.getbbox()
        
        res_top = split_frame(img, (box_top[0]+t_bbox[0], box_top[1]+t_bbox[1], box_top[0]+t_bbox[2], box_top[1]+t_bbox[3])) if t_bbox else []
        res_bot = split_frame(img, (box_bottom[0]+b_bbox[0], box_bottom[1]+b_bbox[1], box_bottom[0]+b_bbox[2], box_bottom[1]+b_bbox[3])) if b_bbox else []
        return res_top + res_bot

    return [box]

def generate_catalog_for_sheet(filename):
    """
    スプライトシートから全コマを切り出し、番号付きカタログ画像を生成します。
    """
    raw_path = os.path.join(RAW_CHAR_DIR, filename)
    char_name = os.path.splitext(filename)[0].lower()
    
    try:
        with Image.open(raw_path) as img:
            img = make_background_transparent(img)
            
            # 全体のトリミング
            init_bbox = img.getbbox()
            if not init_bbox:
                return False
                
            # 1. 全コマのバウンディングボックスを再帰抽出
            boxes = split_frame(img, init_bbox)
            
            # コマ画像のリストを作成
            frames = []
            for box in boxes:
                frame = img.crop(box)
                f_bbox = frame.getbbox()
                if f_bbox:
                    cropped = frame.crop(f_bbox)
                    # 極小ノイズ（15x15未満のゴミ）は除外
                    if cropped.width >= 15 and cropped.height >= 15:
                        frames.append(cropped)
            
            if not frames:
                print(f"  [警告] {filename} から有効なコマを検出できませんでした。")
                return False
                
            # 2. グリッドセルのサイズ算出
            max_w = max(f.width for f in frames)
            max_h = max(f.height for f in frames)
            
            cell_w = max_w + 20
            cell_h = max_h + 30
            
            # 1行に最大8コマ並べる
            cols = 8
            if len(frames) < cols:
                cols = len(frames)
            rows = math.ceil(len(frames) / cols)
            
            # カタログキャンバスの作成 (暗いグレー背景)
            cat_w = cell_w * cols
            cat_h = cell_h * rows
            catalog = Image.new("RGBA", (cat_w, cat_h), (40, 40, 45, 255))
            draw = ImageDraw.Draw(catalog)
            
            try:
                font = ImageFont.load_default()
            except:
                font = None

            # 各コマをカタログに配置して描画
            for idx, frame in enumerate(frames):
                row = idx // cols
                col = idx % cols
                
                x = col * cell_w
                y = row * cell_h
                
                # 各セルの外枠線を描画 (枠線色: 薄グレー)
                draw.rectangle([x, y, x + cell_w - 1, y + cell_h - 1], outline=(80, 80, 90, 255), width=1)
                
                # キャラクターをセルの中央上寄せで貼り付け
                paste_x = x + (cell_w - frame.width) // 2
                paste_y = y + 5
                catalog.paste(frame, (paste_x, paste_y), frame)
                
                # コマのインデックス番号を描画
                num_str = str(idx)
                draw.text((x + 6, y + cell_h - 22), f"No.{num_str}", fill=(255, 60, 60, 255), font=font)
                draw.text((x + 6, y + cell_h - 10), f"({frame.width}x{frame.height})", fill=(150, 150, 160, 255), font=font)

            # 保存先
            catalog_filename = f"{char_name}_catalog.png"
            local_save_path = os.path.join(OUT_CATALOG_DIR, catalog_filename)
            artifact_save_path = os.path.join(ARTIFACT_DIR, catalog_filename)
            
            # 保存
            catalog.save(local_save_path, "PNG")
            shutil.copy2(local_save_path, artifact_save_path)
            
            print(f"  [カタログ生成成功] {filename} (全 {len(frames)} コマ) -> {catalog_filename} として出力しました。")
            return True
            
    except Exception as e:
        print(f"  [エラー] {filename} のカタログ生成中に問題が発生しました: {e}")
        return False

def main():
    print("=========================================")
    print(" Undertale Watchface カタログ画像生成ツール")
    print("=========================================\n")
    
    if not os.path.exists(RAW_CHAR_DIR):
        print("[エラー] assets/raw/characters/ ディレクトリが見つかりません。")
        return
        
    files = os.listdir(RAW_CHAR_DIR)
    png_files = [f for f in files if f.lower().endswith('.png') and f.lower() != "black_pixel.png"]
    
    if not png_files:
        print("[警告] 対象となるスプライト画像 (.png) が raw フォルダに見つかりません。")
        return
        
    success_count = 0
    for filename in png_files:
        if generate_catalog_for_sheet(filename):
            success_count += 1
            
    print(f"\n-> 完了: {len(png_files)} 件中 {success_count} 件のキャラクターアセットでカタログ画像を生成しました。")

if __name__ == "__main__":
    main()
