import os
import sys
import subprocess
import time

import requests
import pyautogui
from datetime import datetime
from google import genai
import json
from pathlib import Path

# --- 設定項目 ---
# デフォルト値
OBSIDIAN_VAULT_PATH = "G:/マイドライブ/ObsidianVault"
GEMINI_API_KEY = ""

# ホームディレクトリのグローバル設定ファイルから読み込み
CONFIG_PATH = Path.home() / ".devlop_logger_config.json"
if CONFIG_PATH.exists():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            OBSIDIAN_VAULT_PATH = config.get("OBSIDIAN_VAULT_PATH", OBSIDIAN_VAULT_PATH)
            GEMINI_API_KEY = config.get("GEMINI_API_KEY", GEMINI_API_KEY)
    except Exception as e:
        print(f"⚠️ 設定ファイルの読み込みに失敗しました: {e}", file=sys.stderr)

# 環境変数がある場合はそちらを優先
OBSIDIAN_VAULT_PATH = os.environ.get("OBSIDIAN_VAULT_PATH", OBSIDIAN_VAULT_PATH)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", GEMINI_API_KEY)

def get_git_diff():
    """現在のコミットとその前のコミットの差分(diff)を取得"""
    # Gitのフック環境変数がサブプロセスのGitコマンドに干渉するのを防ぐ
    clean_env = os.environ.copy()
    for key in ["GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE"]:
        clean_env.pop(key, None)

    try:
        # 親コミットが存在するか確認
        subprocess.check_call(
            ["git", "rev-parse", "HEAD~1"], 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL,
            env=clean_env
        )
        cmd = ["git", "diff", "HEAD~1", "HEAD"]
    except subprocess.CalledProcessError:
        # 親コミットがない場合（最初のコミットの場合）は --root オプションを使用して差分を取得
        cmd = ["git", "diff-tree", "-p", "--no-commit-id", "--root", "HEAD"]
    
    try:
        return subprocess.check_output(cmd, env=clean_env).decode("utf-8", errors="ignore")
    except Exception:
        return ""


def generate_summary(git_diff):
    """Gemini APIを使用してgit diffから変更要約を生成"""
    api_key = os.environ.get("GEMINI_API_KEY") or GEMINI_API_KEY
    if not api_key:
        return "⚠️ Gemini APIキーが設定されていないため、自動要約をスキップしました。\n\n```diff\n" + git_diff[:500] + "\n```"
        
    try:
        client = genai.Client(api_key=api_key)
        prompt = (
            "以下のGitの変更差分コード（diff）を詳細に分析し、どのような機能変更が行われ、"
            "その結果システムやユーザーにどのような具体的な変化（UI、機能、挙動など）が生じたかを、"
            "後でブログを書く際に役立つように、分かりやすい日本語の箇条書きで要約してください。\n\n"
            f"{git_diff}"
        )
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"⚠️ Gemini APIでの要約生成に失敗しました: {str(e)}\n\n```diff\n" + git_diff[:500] + "\n```"

def get_project_and_feature():
    """プロジェクト名と現在のGitブランチ（機能名）を自動取得"""
    # 実行時のカレントディレクトリ名をプロジェクト名にする
    project_name = os.path.basename(os.getcwd())
    
    clean_env = os.environ.copy()
    for key in ["GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE"]:
        clean_env.pop(key, None)
        
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], 
            stderr=subprocess.DEVNULL,
            env=clean_env
        ).decode("utf-8").strip()
        feature_name = branch.split("/")[-1]
    except Exception:
        feature_name = "general"
    return project_name, feature_name


def log_to_obsidian(text_content, take_screenshot=False):
    project, feature = get_project_and_feature()
    date_str = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    # Vault内の書き込み先ディレクトリ
    vault_base = Path(OBSIDIAN_VAULT_PATH) / "開発ログ" / project
    attachments_dir = vault_base / "attachments"
    
    # 1. スクショ処理（必要な場合）
    screenshot_md = ""
    if take_screenshot:
        ss_filename = f"ss_{datetime.now().strftime('%H%M%S')}.png"
        attachments_dir.mkdir(parents=True, exist_ok=True)
        ss_path = attachments_dir / ss_filename
        
        try:
            # スクショ撮影と保存
            screenshot = pyautogui.screenshot()
            screenshot.save(str(ss_path))
            screenshot_md = f"\n\n![[{ss_filename}]]"
        except Exception as e:
            print(f"⚠️ スクリーンショットの撮影・保存に失敗しました: {e}", file=sys.stderr)

    # 2. 本文の追記
    vault_base.mkdir(parents=True, exist_ok=True)
    note_path = vault_base / f"{date_str}_{feature}.md"
    
    # ドキュメントの警告通り、前後に改行(\n\n)を入れて既存テキストとの癒着を防ぐ
    formatted_payload = f"\n\n### [{timestamp}]\n{text_content}{screenshot_md}\n\n---"
    
    try:
        with open(note_path, "a", encoding="utf-8") as f:
            f.write(formatted_payload)
        return 200
    except Exception as e:
        print(f"⚠️ ログファイルの書き込みに失敗しました: {e}", file=sys.stderr)
        return 500

if __name__ == "__main__":
    # 呼び出し元のgitプロセスがロックを解放するのを少し待つ
    time.sleep(0.5)
    try:
        diff_content = get_git_diff()

        if not diff_content.strip():
            log_message = "- 変更差分はありませんでした。"
        else:
            summary_text = generate_summary(diff_content)
            log_message = f"#### 🛠️ 開発変更の要約\n{summary_text}"
            
        status = log_to_obsidian(log_message, take_screenshot=False)
        print(f"Log status: {status}")
    except Exception as e:
        print(f"⚠️ ロガー実行中にエラーが発生しました（コミット自体は成功しています）: {e}", file=sys.stderr)
        
    # 常に正常終了（0）を返すことで、git commitの本体動作に悪影響を及ぼさないようにガード
    sys.exit(0)