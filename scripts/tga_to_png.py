import os
import shutil
from PIL import Image

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(BASE_DIR, "assets", "images")
BACKUP_DIR = os.path.join(BASE_DIR, "assets", "tga_backup")

def convert_tga_to_png_and_backup(dir_path, backup_path):
    os.makedirs(backup_path, exist_ok=True)
    
    for root, dirs, files in os.walk(dir_path):
        # バックアップ用ディレクトリ自体はスキップします
        if root.startswith(backup_path):
            continue
            
        for file in files:
            if file.lower().endswith(".tga"):
                tga_path = os.path.join(root, file)
                png_name = os.path.splitext(file)[0] + ".png"
                png_path = os.path.join(root, png_name)
                
                try:
                    # TGA画像をPNG画像として再保存
                    with Image.open(tga_path) as img:
                        img.save(png_path, "PNG")
                    print(f"  [復元成功] {file} -> {png_name}")
                    
                    # 変換が完了したTGAファイルを退避フォルダへ移動
                    # サブフォルダ構造がある場合はフラットに移動すると競合する可能性があるので、相対パスを保つか
                    # 今回は characters/ などのサブフォルダはなく assets/images/ 直下にあることを想定
                    rel_dir = os.path.relpath(root, dir_path)
                    dest_dir = os.path.join(backup_path, rel_dir) if rel_dir != "." else backup_path
                    os.makedirs(dest_dir, exist_ok=True)
                    
                    dest_path = os.path.join(dest_dir, file)
                    if os.path.exists(dest_path):
                        os.remove(dest_path) # 上書き
                    shutil.move(tga_path, dest_path)
                    print(f"  [退避完了] {file} を {dest_dir} へ退避しました。")
                except Exception as e:
                    print(f"  [復元失敗] {file} の処理中にエラーが発生しました: {e}")

def main():
    print("=========================================")
    print(" TGA から PNG への逆変換および退避スクリプト")
    print("=========================================\n")
    print(f"対象ディレクトリ: {IMAGES_DIR}")
    print(f"退避ディレクトリ: {BACKUP_DIR}")
    
    if not os.path.exists(IMAGES_DIR):
        print("エラー: images ディレクトリが見つかりません。")
        return
        
    convert_tga_to_png_and_backup(IMAGES_DIR, BACKUP_DIR)
    print("\nすべての画像復元および退避処理が完了しました。")

if __name__ == "__main__":
    main()
