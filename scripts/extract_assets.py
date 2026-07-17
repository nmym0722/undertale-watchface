import os
import shutil
import sys
from PIL import Image

# パスの定義
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_CHAR_DIR = os.path.join(BASE_DIR, "assets", "raw", "characters")
RAW_FONT_DIR = os.path.join(BASE_DIR, "assets", "raw", "fonts")
OUT_CHAR_DIR = os.path.join(BASE_DIR, "assets", "images", "characters")
OUT_FONT_DIR = os.path.join(BASE_DIR, "assets", "fonts")

# 必要なディレクトリの作成
for path in [RAW_CHAR_DIR, RAW_FONT_DIR, OUT_CHAR_DIR, OUT_FONT_DIR]:
    os.makedirs(path, exist_ok=True)

# ユーザー様がカタログから選択したコマの番号マッピング
SELECTED_INDICES = {
    "undyne": 7,       # 戦闘用構えポーズ (No.7)
    "sans": 0,         # 正面立ち姿 (No.0)
    "papyrus": 0,      # 正面立ち姿 (No.0)
    "flowey": 0,       # 通常笑顔 (No.0)
    "alphys": 0,       # 正面立ち姿 (No.0)
    "toriel": 0,       # 正面立ち姿 (No.0)
    "asgore": 0,       # 正面立ち姿 (No.0)
    "asriel": 8,       # 特定立ち姿 (No.8)
    "chara": 0,        # 通常立ち姿 (No.0)
    "monsterkid": 0,   # 正面立ち姿 (No.0)
    "muffet": 1,       # 通常立ち姿 (No.1)
    "napstablook": 5,  # 泣き止んだ正面 (No.5)
    "temmie": 0,       # 通常立ち姿 (No.0)
    "dog": 8           # 正面お座り/静止 (No.8)
}

def find_background_color(img):
    """
    画像全体のカラーヒストグラムを解析し、最も面積の広いRGBカラーを透過背景色として動的に自動検出します。
    """
    img = img.convert("RGBA")
    try:
        resample_filter = Image.Resampling.NEAREST
    except AttributeError:
        resample_filter = Image.NEAREST
        
    small_img = img.resize((100, 100), resample=resample_filter)
    pixels = list(small_img.getdata())
    
    color_counts = {}
    for r, g, b, a in pixels:
        if a < 50:
            continue
        color = (r, g, b)
        color_counts[color] = color_counts.get(color, 0) + 1
        
    if not color_counts:
        return (138, 90, 157)
        
    bg_color = max(color_counts, key=color_counts.get)
    return bg_color

def make_background_transparent(img):
    """
    スプライトシート内で混在する「濃い紫 (138, 90, 157)」と「明るい紫 (195, 134, 255)」の両方を
    透過キーとして動的に検出し、完全に背景を透過 (A=0) させます。
    """
    img = img.convert("RGBA")
    width, height = img.size
    pixels = img.load()
    
    # 透過ターゲット色の候補リスト（自動検出された色、およびUndertaleスプライト背景の既知の2大透過色）
    bg_color_detected = find_background_color(img)
    target_bg_colors = [
        bg_color_detected,
        (138, 90, 157),  # 濃い紫 (Hex: #8A5A9D)
        (195, 134, 255)   # 明るい紫 (Hex: #C386FF)
    ]
    
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            
            # target_bg_colors のいずれかとRGB差が小さいピクセルを透過 (許容誤差20)
            is_bg = False
            for target_r, target_g, target_b in target_bg_colors:
                if abs(r - target_r) < 20 and abs(g - target_g) < 20 and abs(b - target_b) < 20:
                    is_bg = True
                    break
                    
            if is_bg:
                pixels[x, y] = (0, 0, 0, 0)
            else:
                if a == 255:
                    pixels[x, y] = (r, g, b, 255)
    return img

def split_frame(img, box):
    """
    再帰的バウンディングボックス分割。
    透明な隙間（1px以上）を自動で検知して、画像をコマ単位へ分解します（内側境界スキャン）。
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
                
    # 垂直方向に分割可能な透明列を検索（内側のみ）
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

    # 水平方向に分割可能な透明行を検索（内側のみ）
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

def process_character_image(filename):
    """
    スプライトシートから全コマを分割抽出し、ユーザー指定のコマを
    本家のキャラクターサイズ比率(等身比率)を維持して160x160透過PNGとして整形・保存します。
    """
    raw_path = os.path.join(RAW_CHAR_DIR, filename)
    char_name = os.path.splitext(filename)[0].lower()
    out_filename = f"{char_name}_active.png"
    out_path = os.path.join(OUT_CHAR_DIR, out_filename)

    try:
        with Image.open(raw_path) as img:
            # 1. クロマキー背景透過処理 (マルチ背景色対応)
            img = make_background_transparent(img)
            
            # 全体のトリミング
            init_bbox = img.getbbox()
            if not init_bbox:
                return False
                
            # 2. 全コマのバウンディングボックスを再帰抽出
            boxes = split_frame(img, init_bbox)
            
            # コマ画像のリストを作成 (極小ノイズは除去)
            frames = []
            for box in boxes:
                frame = img.crop(box)
                f_bbox = frame.getbbox()
                if f_bbox:
                    cropped = frame.crop(f_bbox)
                    if cropped.width >= 15 and cropped.height >= 15:
                        frames.append(cropped)
                        
            if not frames:
                print(f"  [エラー] {filename} から有効なコマを検出できませんでした。")
                return False
                
            # 3. 指定インデックスのコマを選択
            # アンダインの場合は、戦闘アニメーション用の連番フレーム（No.6, 7, 8）も切り出して保存
            if char_name == "undyne":
                undyne_frames = [6, 7, 8]
                for i, idx in enumerate(undyne_frames):
                    if idx >= 0 and idx < len(frames):
                        u_frame = frames[idx]
                        c_w, c_h = u_frame.size
                        scale = 150.0 / c_h
                        new_w = max(1, int(c_w * scale))
                        new_h = max(1, int(c_h * scale))
                        
                        try:
                            resample_filter = Image.Resampling.NEAREST
                        except AttributeError:
                            resample_filter = Image.NEAREST

                        resized = u_frame.resize((new_w, new_h), resample=resample_filter)
                        canvas = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
                        paste_x = (160 - new_w) // 2
                        paste_y = 160 - new_h
                        canvas.paste(resized, (paste_x, paste_y), resized)
                        
                        frame_out_path = os.path.join(OUT_CHAR_DIR, f"undyne_{i}.png")
                        canvas.save(frame_out_path, "PNG")
                        print(f"  [アニメーション] undyne (コマ No.{idx}) -> undyne_{i}.png に保存しました")

            target_idx = SELECTED_INDICES.get(char_name, 0)
            if target_idx < 0 or target_idx >= len(frames):
                print(f"  [警告] 指定されたコマ No.{target_idx} は範囲外です。No.0 にフォールバックします。")
                target_idx = 0
                
            best_frame = frames[target_idx]
            
            # 4. キャラクターサイズ比率(等身比率)を維持したスケーリングの適用
            c_width, c_height = best_frame.size
            
            if char_name == "undyne":
                scale = 150.0 / c_height
            else:
                scale = 2.8
                if c_height * scale > 160 or c_width * scale > 160:
                    scale = min(160 / c_height, 160 / c_width)
            
            new_w = max(1, int(c_width * scale))
            new_h = max(1, int(c_height * scale))
            
            try:
                resample_filter = Image.Resampling.NEAREST
            except AttributeError:
                resample_filter = Image.NEAREST

            resized = best_frame.resize((new_w, new_h), resample=resample_filter)

            # 透過キャンバスの作成
            canvas = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
            
            # 中央下寄せで貼り付け
            paste_x = (160 - new_w) // 2
            paste_y = 160 - new_h
            canvas.paste(resized, (paste_x, paste_y), resized)

            # 保存
            canvas.save(out_path, "PNG")
            print(f"  [成功] {filename} (コマ No.{target_idx}) -> {out_filename} に保存しました (切り出し元サイズ: {c_width}x{c_height} -> 保存サイズ: {new_w}x{new_h})")
            return True
            
    except Exception as e:
        print(f"  [失敗] {filename} の処理中にエラーが発生しました: {e}")
        return False

def copy_fonts():
    """
    raw/fonts/ のフォントファイルをビルド用フォルダへコピーします。
    """
    if not os.path.exists(RAW_FONT_DIR):
        return
    
    files = os.listdir(RAW_FONT_DIR)
    copied_count = 0
    for filename in files:
        if filename.lower().endswith(('.ttf', '.otf')):
            src = os.path.join(RAW_FONT_DIR, filename)
            dst = os.path.join(OUT_FONT_DIR, filename)
            shutil.copy2(src, dst)
            print(f"  [フォント] {filename} をコピーしました。")
            copied_count += 1
            
    if copied_count == 0:
        print("  [情報] raw/fonts/ 内にコピー対象のフォントファイル (.ttf / .otf) が見つかりません。")

def generate_utility_images():
    """
    AOD待機時に使用する1x1の完全透過ダミー画像を生成します。
    """
    dummy_path = os.path.join(OUT_CHAR_DIR, "black_pixel.png")
    canvas = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    canvas.save(dummy_path, "PNG")
    print(f"  [ユーティリティ] AOD用ダミー画像 (black_pixel.png) を生成しました。")

def main():
    print("=========================================")
    print(" Undertale Watchface アセット自動比率切り出しツール")
    print("=========================================\n")
    
    # 1. フォント処理
    print("[1] フォントファイルをコピー中...")
    copy_fonts()
    
    # 2. ユーティリティ画像の生成
    print("\n[2] ユーティリティ画像(AOD用ダミー等)を生成中...")
    generate_utility_images()
    
    # 3. キャラクター画像処理
    print("\n[3] raw/characters/ 内から指定コマを比率維持して透過抽出中...")
    if not os.path.exists(RAW_CHAR_DIR):
        print("  [情報] raw/characters/ ディレクトリが存在しません。")
        return
        
    files = os.listdir(RAW_CHAR_DIR)
    png_files = [f for f in files if f.lower().endswith('.png') and f.lower() != "black_pixel.png"]
    
    if not png_files:
        print("  [警告] raw/characters/ 内にPNG画像が見つかりません。")
    else:
        success_count = 0
        for filename in png_files:
            if process_character_image(filename):
                success_count += 1
        print(f"\n-> 完了: {len(png_files)} 件中 {success_count} 件のキャラクター画像を切り出して保存しました。")

    print("\nすべての処理が完了しました。")

if __name__ == "__main__":
    main()
