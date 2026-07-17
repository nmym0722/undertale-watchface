# ⌚ Amazfit Bip 6用 Undertaleテーマ文字盤 実装ガイド

本ドキュメントは、Amazfit Bip 6（Zepp OSベース）に対応した『Undertale』テーマ文字盤の開発手順、リソースの取得先、および画面オン時にキャラクターをランダム表示するためのプログラミング実装方法を解説するガイドです。

---

## 📁 1. 推奨プロジェクト構成

文字盤のパッケージをビルドする前に、以下のアセットフォルダ構成をワークスペース内に用意してください。

```text
undertale-watchface/
├── assets/
│   ├── fonts/
│   │   ├── MonsterFriend.ttf          # 時間・日付用フォント
│   │   ├── TroubleBeneathDome.ttf     # HP（バッテリー）数値用フォント
│   │   └── DeterminationMono.ttf      # 各種ステータス用フォント
│   └── images/
│       ├── red_soul_separator.png     # 時刻セパレーター (コロン)
│       ├── red_soul_icon.png          # FIGHT枠内のハートアイコン
│       ├── orange_footprints_icon.png # MERCY枠内の足跡アイコン
│       ├── hp_label.png               # 「HP」文字のスプライト
│       └── characters/                # ランダム表示用の透過PNG (各160x160に切り出し)
│           ├── alphys_active.png
│           ├── dog_active.png
│           ├── asgore_active.png
│           └── (その他アセットガイド記載の14キャラクター分)
├── watchface_config.json              # 文字盤レイアウト・マッピング定義
└── watchface.js                       # 動的ロジック（Zepp OS用エントリーポイント）
```

---

## 🛠️ 2. アセットのダウンロード＆抽出仕様

`undertale-assets-guide-v2.md` に基づく各アセットの取得先と切り出し手順です。

### 🅰️ 適用フォント

1. **時刻・日付・曜日**
   * **フォント名**: `Monster Friend` (ロゴや主要見出しの極太フォント)
   * **取得先**: [Behance - Monster Friend](https://www.behance.net/gallery/31378523/Monster-Friend-Undertale-Logo-Font)
2. **バッテリー残量 (HP) 数値**
   * **フォント名**: `Trouble Beneath The Dome` (旧 Mars Needs Cunnilingus)
   * **取得先**: [itch.io - World of Fonts](https://w.itch.io/world-of-fonts?download)
3. **心拍数・歩数・気温 (LV) 数値**
   * **フォント名**: `Determination Mono` (基本テキストフォント)
   * **取得先**: [Behance - Determination](https://www.behance.net/gallery/31268855/Determination-Better-Undertale-Font) または [8-Bit Operator JVE](https://fontstruct.com/fontstructions/show/534034/8bitoperator)

### 🖼️ 画像アセット

#### ① キャラクター立ち絵 (Spriters Resource)
「The Spriters Resource」のPC版『Undertale』ページのアセットIDから、対象スプライト（透過PNG）をダウンロードし、`160x160` ピクセル（ニアレストネイバー法による等倍・比率維持拡大）で中央下寄せにして切り出します。

* **サンズ (Sans)**: `/pc_computer/undertale/asset/76011/` (静止・歩行)
* **パピルス (Papyrus)**: `/pc_computer/undertale/asset/76008/` (ポーズ違い・歩行)
* **アンダイン (Undyne)**: `/pc_computer/undertale/asset/77124/` (戦闘用)
* **フラウィ (Flowey)**: `/pc_computer/undertale/asset/76943/` (表情変化)
* **アズリエル (Asriel)**: `/pc_computer/undertale/asset/77909/` (戦闘用神スプライト)
* **マフェット (Muffet)**: `/pc_computer/undertale/asset/77091/` (戦闘用スプライト)
* *(その他、アセットガイド記載のキャラクターも同様にIDから抽出)*

#### ② UIアイコン
* **赤いSOUL (時間セパレーター・心拍枠内アイコン)**:
  * [The Human Souls](https://www.spriters-resource.com/pc_computer/undertale/asset/77110/) から赤いハートを抽出。
* **FIGHT / MERCY 枠・足跡 (心拍・歩数表示部)**:
  * [Battle Menu](https://www.spriters-resource.com/pc_computer/undertale/asset/76661/) から、FIGHT（イエロー枠）、MERCY（オレンジ枠）と、MERCYボタン内に描画されている「足跡」のドット絵を切り出します。

---

## 💻 3. Zepp OS JSにおけるランダムキャラクター表示の実装

手首を振って画面がアクティブ（オン）になるたびにキャラクターがランダムで切り替わる仕組みを、Zepp OSのJavaScript APIで実現します。

### `watchface.js` 実装コード例

```javascript
import { createWidget, widget } from '@zeppos/device-types'

WatchFace({
  // 文字盤初期化時のライフサイクル
  onInit() {
    console.log('Undertale Watchface Init')
  },

  // 画面の構築 (ウィジェットの初期登録)
  build() {
    // 1. 背景の描画 (黒 #000000)
    createWidget(widget.FILL_RECT, {
      x: 0,
      y: 0,
      w: 320,
      h: 380,
      color: 0x000000
    })

    // 2. 基本的な時刻・日付等のUIウィジェット登録 (watchface_config.json の座標準拠)
    // (中略 - Time, Date, Battery, HR, Steps などの基本的なシステムウィジェットの登録)

    // 3. ランダム表示用キャラクター画像のウィジェット定義
    this.charWidget = createWidget(widget.IMG, {
      x: 80,
      y: 140,
      w: 160,
      h: 160,
      // 初期値はアンダインに設定
      src: 'characters/undyne_active.png'
    })
  },

  // ★ 画面が点灯（手首を振る・ボタン押下）した時のライフサイクル
  onResume() {
    console.log('Screen Wake Up - Selecting random character')
    
    // アセットガイド記載の14キャラクターのリスト
    const characters = [
      'alphys', 'dog', 'asgore', 'asriel', 'chara', 
      'flowey', 'monsterkid', 'muffet', 'napstablook', 
      'papyrus', 'sans', 'temmie', 'toriel', 'undyne'
    ]

    // ランダムにインデックスを選択
    const randomIndex = Math.floor(Math.random() * characters.length)
    const selectedChar = characters[randomIndex]

    // 画像パスの動的更新 (例: 'characters/sans_active.png')
    this.charWidget.setProperty(prop.MORE, {
      src: `characters/${selectedChar}_active.png`
    })
  },

  // 画面が消灯（待機/常時表示AOD移行）した時
  onPause() {
    console.log('Screen Sleep - Saving battery')
    // 常時表示(AOD)時は、OLED画面の素子消灯によるバッテリー消費削減のため
    // キャラクター画像の表示を非表示、または完全に真っ黒な省電力用画像に切り替えます
    this.charWidget.setProperty(prop.MORE, {
      src: 'characters/black_pixel.png' 
    })
  },

  onDestroy() {
    console.log('Watchface Destroyed')
  }
})
```

---

## 🔋 4. OLEDおよびバッテリーの最適化ガイド

Amazfit Bip 6などのOLEDディスプレイでは、黒色（#000000）の表示部分は電流が流れず、電力を全く消費しません。

1. **AOD（常時表示）時のキャラクター非表示**:
   * 上記コードの `onPause()` メソッドで示すように、画面が待機状態に入ったらキャラクターのカラー表示を強制的に非表示（または黒塗り）にします。
2. **文字盤のコントラスト**:
   * 表示する時刻（Monster Friend）は純白（`#FFFFFF`）とし、背景（`#000000`）との明暗差を最大化します。これにより視認性を損なわずに全体の点灯素子面積を約 15% 以下に抑制可能です。
