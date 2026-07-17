import * as hmUI from '@zos/ui'
import { Battery, HeartRate, Step, Weather } from '@zos/sensor'
import { createTimer, stopTimer } from '@zos/timer'

// 解像度: 390×450 (Amazfit Bip 6)


WatchFace({
  // 各種ウィジェットを保持する変数
  widgets: {},

  onInit() {
    console.log('Undertale Watchface: onInit')
    // 2.0クラス仕様でセンサーを初期化
    try {
      this.batterySensor = new Battery()
    } catch (e) {
      console.log('Error: create batterySensor failed', e)
    }
    try {
      this.heartSensor = new HeartRate()
    } catch (e) {
      console.log('Error: create heartSensor failed', e)
    }
    try {
      this.stepSensor = new Step()
    } catch (e) {
      console.log('Error: create stepSensor failed', e)
    }
    try {
      this.weatherSensor = new Weather()
    } catch (e) {
      console.log('Error: create weatherSensor failed', e)
    }
  },

  build() {
    console.log('Undertale Watchface: build')

    // 1. 真の黒背景 (#000000) — OLED省電力のため全面黒
    hmUI.createWidget(hmUI.widget.FILL_RECT, {
      x: 0,
      y: 0,
      w: 390,
      h: 450,
      color: 0x000000
    })

    // 2. 時刻表示（Monster Friendフォント - スクロールと角見切れ防止のためサイズ70に縮小、幅165に拡張、内寄せ）
    // 「時」の表示
    this.widgets.hourText = hmUI.createWidget(hmUI.widget.TEXT, {
      x: 15,
      y: 22,
      w: 165,
      h: 90,
      color: 0xffffff,
      text_size: 70,
      align_h: hmUI.align.RIGHT,
      align_v: hmUI.align.CENTER_V,
      font: 'fonts/MonsterFriendFore.ttf',
      text: '10'
    })

    // ハートのセパレーター (コロンの代わり)
    hmUI.createWidget(hmUI.widget.IMG, {
      x: 183,
      y: 55,
      w: 24,
      h: 24,
      src: 'images/red_soul_separator.png'
    })

    // 「分」の表示
    this.widgets.minuteText = hmUI.createWidget(hmUI.widget.TEXT, {
      x: 210,
      y: 22,
      w: 165,
      h: 90,
      color: 0xffffff,
      text_size: 70,
      align_h: hmUI.align.LEFT,
      align_v: hmUI.align.CENTER_V,
      font: 'fonts/MonsterFriendFore.ttf',
      text: '10'
    })

    // 3. 日付・曜日表示 (時刻の位置降下に合わせて y: 115 に下げ、h: 45 に変更)
    this.widgets.dateText = hmUI.createWidget(hmUI.widget.TEXT, {
      x: 30,
      y: 115,
      w: 330,
      h: 45,
      color: 0xffffff,
      text_size: 34,
      align_h: hmUI.align.CENTER_H,
      align_v: hmUI.align.CENTER_V,
      font: 'fonts/DeterminationMono.ttf',
      text: '* 07/13 MON'
    })

    // 4. キャラクター表示エリア (日付の位置降下に合わせて y: 170 に下げて重複を回避)
    this.widgets.charImg = hmUI.createWidget(hmUI.widget.IMG, {
      x: 115,
      y: 170,
      w: 160,
      h: 160,
      src: 'images/undyne_active.png'
    })

    // 5. ステータスコンポーネント (LV & HP)
    // LV表記
    this.widgets.tempLvText = hmUI.createWidget(hmUI.widget.TEXT, {
      x: 55,
      y: 335,
      w: 70,
      h: 29,
      color: 0xffffff,
      text_size: 22,
      align_h: hmUI.align.LEFT,
      align_v: hmUI.align.CENTER_V,
      font: 'fonts/DeterminationMono.ttf',
      text: 'LV 19'
    })

    // HPバッテリーゲージ背景 (ダメージ時/レッド) - HPラベル削除に伴い左側に拡張 (x: 130, w: 120)
    hmUI.createWidget(hmUI.widget.FILL_RECT, {
      x: 130,
      y: 341,
      w: 120,
      h: 17,
      color: 0xcc0000
    })

    // HPバッテリーゲージ前景 (現在量/イエロー) - HPラベル削除に伴い左側に拡張 (x: 130, w: 84)
    this.widgets.batteryGauge = hmUI.createWidget(hmUI.widget.FILL_RECT, {
      x: 130,
      y: 341,
      w: 84,  // 初期幅（70%想定: 120 * 0.7 = 84）
      h: 17,
      color: 0xffff00
    })

    // バッテリーパーセント数値 (見切れとスクロールを防ぐため、xを左に広げ、wを拡張、スペース除去)
    this.widgets.batteryText = hmUI.createWidget(hmUI.widget.TEXT, {
      x: 250,
      y: 335,
      w: 85,
      h: 29,
      color: 0xffffff,
      text_size: 20,
      align_h: hmUI.align.RIGHT,
      align_v: hmUI.align.CENTER_V,
      font: 'fonts/DeterminationMono.ttf',
      text: '70/100'
    })

    // 6. FIGHT枠 (心拍数)
    // イエロー枠線
    hmUI.createWidget(hmUI.widget.STROKE_RECT, {
      x: 35,
      y: 385,
      w: 150,
      h: 40,
      color: 0xffff00,
      line_width: 2
    })
    // ハートアイコン
    hmUI.createWidget(hmUI.widget.IMG, {
      x: 47,
      y: 397,
      w: 18,
      h: 17,
      src: 'images/red_soul_icon.png'
    })
    // 心拍数数値
    this.widgets.heartText = hmUI.createWidget(hmUI.widget.TEXT, {
      x: 65,
      y: 385,
      w: 110,
      h: 40,
      color: 0xffff00,
      text_size: 26,
      align_h: hmUI.align.CENTER_H,
      align_v: hmUI.align.CENTER_V,
      font: 'fonts/DeterminationMono.ttf',
      text: '75'
    })

    // 7. MERCY枠 (歩数)
    // オレンジ枠線
    hmUI.createWidget(hmUI.widget.STROKE_RECT, {
      x: 205,
      y: 385,
      w: 150,
      h: 40,
      color: 0xfca600,
      line_width: 2
    })
    // 足跡アイコン
    hmUI.createWidget(hmUI.widget.IMG, {
      x: 217,
      y: 398,
      w: 14,
      h: 14,
      src: 'images/orange_footprints_icon.png'
    })
    // 歩数数値
    this.widgets.stepText = hmUI.createWidget(hmUI.widget.TEXT, {
      x: 235,
      y: 385,
      w: 110,
      h: 40,
      color: 0xfca600,
      text_size: 22,
      align_h: hmUI.align.CENTER_H,
      align_v: hmUI.align.CENTER_V,
      font: 'fonts/DeterminationMono.ttf',
      text: '8000'
    })

    // データの監視・更新登録
    this.registerSensors()
  },

  // センサーリスナーの設定と描画更新
  registerSensors() {
    // ① 時間・日付の更新 (Date & timer)
    const updateTime = () => {
      const now = new Date()
      const hour = now.getHours().toString().padStart(2, '0')
      const minute = now.getMinutes().toString().padStart(2, '0')
      const month = (now.getMonth() + 1).toString().padStart(2, '0')
      const day = now.getDate().toString().padStart(2, '0')

      const days = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']
      const dayStr = days[now.getDay()] || ''

      this.widgets.hourText.setProperty(hmUI.prop.TEXT, hour)
      this.widgets.minuteText.setProperty(hmUI.prop.TEXT, minute)
      this.widgets.dateText.setProperty(hmUI.prop.TEXT, `* ${month}/${day} ${dayStr}`)
    }
    updateTime() // 初回実行
    // 1秒ごとに更新するタイマーを登録
    this.timeTimer = createTimer(1000, 1000, updateTime)

    // ② バッテリー（HPバー）の更新
    const updateBattery = () => {
      const batterySensor = this.batterySensor
      if (!batterySensor) return
      const level = batterySensor.getCurrent() !== undefined ? batterySensor.getCurrent() : 100
      // 最大幅 120px に対して割合計算 (HPラベル削除に伴い90pxから120pxへ拡張)
      const barWidth = Math.floor(120 * (level / 100))

      // 背景の赤と同化するのを防ぐため、バーの色は常にイエロー（0xffff00）に固定します
      const barColor = 0xffff00

      // 幅と色、および描画座標を同時に一括で適用し、設定値の上書き消失を防ぎます
      this.widgets.batteryGauge.setProperty(hmUI.prop.MORE, {
        x: 130,
        y: 341,
        w: barWidth,
        h: 17,
        color: barColor
      })
      this.widgets.batteryText.setProperty(hmUI.prop.TEXT, `${level}/100`)
    }
    if (this.batterySensor) {
      this.batterySensor.onChange(updateBattery)
      updateBattery()
    }

    // ③ 心拍数の更新
    const updateHeart = () => {
      const heartSensor = this.heartSensor
      if (!heartSensor) return
      const rate = heartSensor.getCurrent() !== undefined ? heartSensor.getCurrent() : 0
      this.widgets.heartText.setProperty(hmUI.prop.TEXT, rate.toString())
    }
    if (this.heartSensor) {
      this.heartSensor.onCurrentChange(updateHeart)
      updateHeart()
    }

    // ④ 歩数の更新
    const updateSteps = () => {
      const stepSensor = this.stepSensor
      if (!stepSensor) return
      const steps = stepSensor.getCurrent() !== undefined ? stepSensor.getCurrent() : 0
      this.widgets.stepText.setProperty(hmUI.prop.TEXT, steps.toString())
    }
    if (this.stepSensor) {
      this.stepSensor.onChange(updateSteps)
      updateSteps()
    }

    // ⑤ 気温 (LV) の更新
    const updateTemp = () => {
      const weatherSensor = this.weatherSensor
      if (!weatherSensor) return
      let temp = '--'
      try {
        if (typeof weatherSensor.getForecast === 'function') {
          const { forecastData } = weatherSensor.getForecast()
          if (forecastData && forecastData.count > 0 && forecastData.data && forecastData.data[0]) {
            const item = forecastData.data[0]
            if (item.temp !== undefined) {
              temp = item.temp
            } else if (item.high !== undefined) {
              temp = item.high
            }
          }
        } else if (weatherSensor.forecasts && weatherSensor.forecasts.length > 0 && weatherSensor.forecasts[0]) {
          temp = weatherSensor.forecasts[0].temp
        }
      } catch (e) {
        console.log('Error reading weather data', e)
      }
      this.widgets.tempLvText.setProperty(hmUI.prop.TEXT, `LV ${temp}`)
    }
    if (this.weatherSensor) {
      try {
        if (this.weatherSensor.onChange) {
          this.weatherSensor.onChange(updateTemp)
        }
      } catch (e) {
        console.log('weather onChange registration failed', e)
      }
      updateTemp()
    }
  },

  // ★ 手首フリックで画面がアクティブになったときにランダムキャラクターを決定
  onResume() {
    console.log('Undertale Watchface: onResume')

    const characters = [
      'alphys', 'dog', 'asgore', 'asriel', 'chara',
      'flowey', 'monsterkid', 'muffet', 'napstablook',
      'papyrus', 'sans', 'temmie', 'toriel', 'undyne'
    ]

    const randomIndex  = Math.floor(Math.random() * characters.length)
    const selectedChar = characters[randomIndex]

    console.log('Random character chosen: ' + selectedChar)

    this.widgets.charImg.setProperty(hmUI.prop.SRC, `images/${selectedChar}_active.png`)
  },

  // 常時表示(AOD)待機モード移行時：OLED省電力のためキャラクター画像を黒画像に切り替える
  onPause() {
    console.log('Undertale Watchface: onPause (AOD mode)')
    this.widgets.charImg.setProperty(hmUI.prop.SRC, 'images/black_pixel.png')
  },

  onDestroy() {
    console.log('Undertale Watchface: onDestroy')
    if (this.timeTimer) {
      stopTimer(this.timeTimer)
    }
  }
})
