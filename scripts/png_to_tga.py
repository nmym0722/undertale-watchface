import os
from PIL import Image

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(BASE_DIR, "assets", "images")

def convert_png_to_tga(dir_path):
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file.lower().endswith(".png"):
                # icon.png は app.json からシステム側で直接参照されるため除外します
                if file.lower() == "icon.png" and root == IMAGES_DIR:
                    print("  [スキップ] icon.png はシステムの規定によりPNGのまま維持します。")
                    continue
                
                png_path = os.path.join(root, file)
                tga_name = os.path.splitext(file)[0] + ".tga"
                tga_path = os.path.join(root, tga_name)
                
                try:
                    with Image.open(png_path) as img:
                        # TGAは透過アルファチャンネル付きRGBA形式をサポートしています
                        img.save(tga_path, "TGA")
                    os.remove(png_path)
                    print(f"  [変換成功] {file} -> {tga_name} (PNGは削除しました)")
                except Exception as e:
                    print(f"  [変換失敗] {file} の変換中にエラーが発生しました: {e}")

def main():
    print("=========================================")
    print(" PNG から TGA フォーマットへの一括変換スクリプト")
    print("=========================================\n")
    print(f"対象ディレクトリ: {IMAGES_DIR}")
    
    if not os.path.exists(IMAGES_DIR):
        print("エラー: images ディレクトリが見つかりません。")
        return
        
    convert_png_to_tga(IMAGES_DIR)
    print("\nすべての画像変換処理が完了しました。")

if __name__ == "__main__":
    main()
