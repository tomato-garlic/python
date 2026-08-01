# -*- coding: utf-8 -*-
"""
config.py
=========
パルセーション閾値測定プログラム 共通設定ファイル
全スクリプトから import して使用する。
"""

# ---- 音声基本設定 ----
SAMPLE_RATE: int = 44100        # サンプリングレート (Hz)
N_CHANNELS: int = 2             # ステレオ (左=0, 右=1)

# ---- 刺激音 共通 ----
RAMP_DURATION: float = 0.020    # コサインテーパー長さ (秒)

# ---- Phase 1: 1kHz閾値測定 ----
PHASE1_FREQ: float = 1000.0     # 純音周波数 (Hz)
PHASE1_DURATION: float = 0.500  # 1呈示あたりの長さ (秒)
PHASE1_START_LEVEL: float = -20.0   # 開始レベル (dB FS, フルスケール基準)
PHASE1_STEP_LARGE: float = 2.0      # 初期ステップ幅 (dB)
PHASE1_STEP_SMALL: float = 1.0      # 収束後ステップ幅 (dB)
PHASE1_STEP_CHANGE_REVERSALS: int = 1   # ステップ縮小に必要な反転回数
PHASE1_TOTAL_REVERSALS: int = 4     # Phase1終了に必要な反転回数
PHASE1_MIN_LEVEL: float = -100.0    # 提示レベル下限 (dB FS)
PHASE1_MAX_LEVEL: float = 0.0       # 提示レベル上限 (dB FS)

# ---- Phase 2: 刺激音 ----
MASKER_DURATION: float = 0.145  # マスカー1区間の長さ (秒)
TEST_DURATION: float = 0.145    # テスト信号1区間の長さ (秒)
CROSSFADE_DURATION: float = 0.020   # クロスフェード長さ (秒)
TEST_FREQ: float = 500.0        # テスト信号周波数 (Hz)
MOD_FREQ: float = 250.0         # 変調周波数 (Hz)
MOD_TYPE: str = "None"    # 変調タイプ ("None", "SAM", "Transposed")
MASKER_ITD_US: int = 0          # マスカーのITD (µs)
TARGET_SL: float = 40.0         # マスカーの目標SL (Sensation Level または Stimulus Level)
# 交番刺激パターン (T-M-T-M-...-S)
# N_TEST の回数に応じて全体のセグメント数が自動的に決定されます。
N_TEST: int = 3
N_MASKER: int = N_TEST - 1
N_SILENCE: int = 1

# ---- Phase 2: 1-up/1-down 適応法 (Experiment C 準拠) ----
ADAPTIVE_INITIAL_STEP_SIZE: float = 12.0
ADAPTIVE_SECOND_STEP_SIZE: float = 6.0
ADAPTIVE_FINAL_STEP_SIZE: float = 3.0
ADAPTIVE_REVERSAL_TRIGGER_1: int = 2
ADAPTIVE_REVERSAL_TRIGGER_2: int = 4
ADAPTIVE_MAX_REVERSALS: int = 10
ADAPTIVE_NUM_REVERSALS_FOR_MEAN: int = 6
ADAPTIVE_INITIAL_TARGET_OFFSET: float = 20.0  # マスカーレベルからの初期オフセット目安
ADAPTIVE_ROVING_RANGE: float = 3.0            # ±3dBのロービング（ジッター）幅

TEST_MIN_LEVEL: float = -80.0   # テスト信号レベル下限 (dB FS)
TEST_MAX_LEVEL: float = 0.0     # テスト信号レベル上限 (dB FS)

# ---- キー設定 ----
KEY_PHASE1_YES = "y"        # Phase1: 聞こえた
KEY_PHASE1_NO  = "n"        # Phase1: 聞こえなかった
KEY_CONTINUOUS = "c"        # Phase2: 連続して聞こえた
KEY_INTERRUPTED = "i"       # Phase2: 途切れて聞こえた

# ---- データ保存 ----
DATA_DIR: str = "data"

# ---- 教示文 ----
INSTRUCTION_TEXT = (
    "====== 全体説明 ======\n"
    "この実験ではパルセーション閾値の測定を行います。\n\n"
    "[ Phase 1 ]\n"
    "1000Hzの純音が聞こえる最小の音の大きさを測定します。\n"
    "音が聞こえたら '{KEY_YES}' キーを、\n"
    "聞こえなかったら '{KEY_NO}' キーを押してください。\n\n"
    "[ Phase 2 ]\n"
    "ノイズ（ジャージャー音）とテスト音が交互に鳴るパターンが1回再生されます。\n"
    "テスト音がノイズの間で途切れず「連続」して聞こえたら '{KEY_C}' キーを、\n"
    "途切れて聞こえたら '{KEY_I}' キーを押してください。\n\n"
    "準備ができたら [Space] キーを押して開始してください。"
).format(
    KEY_YES=KEY_PHASE1_YES.upper(),
    KEY_NO=KEY_PHASE1_NO.upper(),
    KEY_C=KEY_CONTINUOUS.upper(),
    KEY_I=KEY_INTERRUPTED.upper(),
)
