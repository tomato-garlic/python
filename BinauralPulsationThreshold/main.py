# -*- coding: utf-8 -*-
"""
main.py
=======
パルセーション閾値測定プログラム エントリーポイント

実行フロー:
  1. 初期ダイアログ: 被験者ID, ITDリスト入力
  2. Phase 1: 1kHz聴取閾値測定 → マスカーレベル算出
  3. Phase 2: 全ITD条件をインターリーブして提示 → 1-up 1-down 適応法
  4. CSV保存 → 終了
"""

import os
import sys

# Windows/Mac 両環境でコンソール出力の文字化けを防ぐ
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from psychopy import visual, core, gui, event, sound, prefs

import config
from phase1_threshold import run_phase1
from phase2_1up1down import run_1up1down_interleaved
from data_recorder import DataRecorder
import plot_results


# ────────────────────────────────────────────
# 初期ダイアログ
# ────────────────────────────────────────────

def show_dialog() -> tuple[str, list[int], float | None, str, float, float, str, int]:
    """
    被験者IDと測定するITDリスト、および既知のSL基準値を取得するダイアログ。
    """
    try:
        devices = sound.getDevices()
        if isinstance(devices, dict):
            device_names = list(devices.keys())
        else:
            device_names = [dev['deviceName'] for dev in devices]
    except Exception:
        device_names = ["default"]

    if not device_names:
        device_names = ["default"]

    dlg = gui.Dlg(title="Pulsation Threshold Measurement")
    dlg.addField("Subject ID:", "P01")
    dlg.addField("ITD list (us, comma-separated):", "-600, -400, -200, 0, 200, 400, 600")
    dlg.addField("SL reference (dB FS, blank = run Phase 1):", "")
    dlg.addField("Sound Device:", choices=["default"] + [d for d in device_names if d != "default"])
    dlg.addField("Test frequency (Hz):", config.TEST_FREQ)
    dlg.addField("Modulation frequency (Hz):", config.MOD_FREQ)
    dlg.addField("Modulation type:", choices=["None", "SAM", "Transposed"], initial="None")
    dlg.addField("Masker ITD (us):", config.MASKER_ITD_US)

    ok = dlg.show()
    if not ok:
        core.quit()

    subject_id   = str(dlg.data[0]).strip()
    raw_itds     = str(dlg.data[1]).strip()
    raw_sl       = str(dlg.data[2]).strip()
    device_name  = str(dlg.data[3])
    test_freq    = float(dlg.data[4])
    mod_freq     = float(dlg.data[5])
    mod_type     = str(dlg.data[6])
    masker_itd   = int(dlg.data[7])

    # ITDリストのパース
    itd_list_us = []
    for token in raw_itds.split(","):
        token = token.strip()
        if token.lstrip("-").isdigit():
            itd_list_us.append(int(token))

    if not itd_list_us:
        raise ValueError(f"Please enter a valid ITD list: '{raw_itds}'")

    # SL基準値のパース（空欄なら None）
    sl_reference_db: float | None = None
    if raw_sl != "":
        try:
            sl_reference_db = float(raw_sl)
        except ValueError:
            raise ValueError(f"SL reference must be a number: '{raw_sl}'")
            
    if device_name != "default":
        prefs.hardware['audioDevice'] = [device_name]

    return subject_id, itd_list_us, sl_reference_db, device_name, test_freq, mod_freq, mod_type, masker_itd


# ────────────────────────────────────────────
# メイン
# ────────────────────────────────────────────

def show_instructions(win: visual.Window) -> None:
    """
    実験の全体的な説明と教示を表示する。
    """
    msg = visual.TextStim(
        win,
        text=config.INSTRUCTION_TEXT,
        height=0.06, wrapWidth=1.8, color="white",
    )
    msg.draw()
    win.flip()
    event.waitKeys(keyList=["space"])


def main() -> None:
    # ── 初期ダイアログ ──
    subject_id, itd_list_us, sl_reference_db, device_name, test_freq, mod_freq, mod_type, masker_itd = show_dialog()

    # µs → 秒 変換
    itd_list_sec = [us * 1e-6 for us in itd_list_us]
    masker_itd_sec = masker_itd * 1e-6

    # ── ウィンドウ生成 ──
    win = visual.Window(
        size=(1600, 900),
        fullscr=False,
        color="black",
        units="norm",
        screen=0,
    )
    win.setMouseVisible(False)

    # ── 教示画面の表示 ──
    show_instructions(win)

    recorder = DataRecorder()

    # ── Phase 1: 1kHz聴取閾値測定（sl_reference_db が未入力の場合のみ）──
    if sl_reference_db is None:
        print("Running Phase 1: 1kHz threshold measurement...")
        sl_reference_db = run_phase1(win)
    else:
        print(f"Phase 1 skipped. Using SL reference = {sl_reference_db:.2f} dB FS")
    # ユーザー要望: Target_SL + Phase1閾値
    masker_spectrum_level_db = sl_reference_db + config.TARGET_SL

    # ── Phase 2: 全ITD条件をインターリーブして実施 ──
    results = run_1up1down_interleaved(
        win=win,
        masker_spectrum_level_db=masker_spectrum_level_db,
        itd_list_us=itd_list_us,
        itd_list_sec=itd_list_sec,
        subject_id=subject_id,
        recorder=recorder,
        sl_reference_db=sl_reference_db,
        test_freq=test_freq,
        mod_freq=mod_freq,
        mod_type=mod_type,
        masker_itd_sec=masker_itd_sec,
        masker_itd_us=masker_itd,
    )

    final_thresholds: list[dict] = []

    for itd_us, (final_thr, reversal_levels) in results.items():
        recorder.update_block_metadata(
            itd_us=itd_us,
            threshold_db=final_thr,
            reversal_levels=reversal_levels
        )

        final_thresholds.append({
            "itd_us": itd_us,
            "final_threshold_dBFS": final_thr,
        })

    # ── データ保存 ──
    csv_path = recorder.save(subject_id)

    print(f"\n=== Experiment finished: {subject_id} ===")
    print(f"Phase 1 SL ref: {sl_reference_db:.2f} dB FS")
    print(f"Masker spec level: {masker_spectrum_level_db:.2f} dB/Hz\n")
    print(f"{'ITD(us)':>10} {'Threshold(dB FS)':>18}")
    for row in sorted(final_thresholds, key=lambda r: r["itd_us"]):
        print(
            f"{row['itd_us']:>10} "
            f"{row['final_threshold_dBFS']:>18.2f}"
        )
    print(f"\nCSV saved: {csv_path}")

    # ── 終了画面 ──
    msg = visual.TextStim(
        win,
        text=(
            "Experiment finished\n\n"
            f"Results saved to {csv_path}\n\n"
            "[Space] to show graphs & exit"
        ),
        height=0.06, wrapWidth=1.8, color="white",
    )
    msg.draw()
    win.flip()
    event.waitKeys(keyList=["space"])

    win.close()  # PsychoPy ウィンドウを先に閉じる

    # ── 結果グラフを自動生成 ──
    print("Generating result plots...")
    df_result, _ = plot_results.load_csv(csv_path)
    stem = os.path.splitext(csv_path)[0]
    
    subtitle = f"Test: {test_freq}Hz, Mod: {mod_type} ({mod_freq}Hz), Masker ITD: {masker_itd}µs"
    
    # ITDごとにStaircaseをプロット
    for itd, grp in df_result.groupby("itd_us"):
        plot_results.plot_staircase(grp, itd, stem, subtitle)
        
    plot_results.plot_all(df_result, stem)

    core.quit()


if __name__ == "__main__":
    main()
