# -*- coding: utf-8 -*-
"""
phase2_1up1down.py
==================
Phase 2: Experiment C 準拠の 1-up/1-down 階段法 (Staircase method)
被験者が「50%の確率で連続していると知覚するターゲット音のレベル」を探索する。
"""

import random
import numpy as np
from psychopy import visual, sound, core, event

import config
from phase2_stimulus import build_alternating_stimulus


class AdaptiveTrack1Up1Down:
    """
    1-up/1-down 階段法アルゴリズム (Experiment C準拠) を管理するクラス。
    """
    def __init__(self, masker_spectrum_level_db: float):
        self.masker_spectrum_level = masker_spectrum_level_db
        
        # 初期ターゲットレベル：確実に途切れて聞こえる高いレベル
        # config.ADAPTIVE_INITIAL_TARGET_OFFSET を目安に、± Roving_Range のジッターを加える
        jitter = random.uniform(-config.ADAPTIVE_ROVING_RANGE, config.ADAPTIVE_ROVING_RANGE)
        initial_target_level = masker_spectrum_level_db + config.ADAPTIVE_INITIAL_TARGET_OFFSET + jitter
        
        # リミッター適用
        self.current_target_level = float(np.clip(
            initial_target_level, 
            config.TEST_MIN_LEVEL, 
            config.TEST_MAX_LEVEL
        ))
        
        self.current_step_size = config.ADAPTIVE_INITIAL_STEP_SIZE
        self.reversal_count = 0
        self.previous_direction = None  # 1 (UP) or -1 (DOWN)
        self.reversal_levels = []
        
        self.history = []
        self.trial_no = 0
        self._finished = False

    def is_finished(self) -> bool:
        return self._finished

    def get_current_level(self) -> float:
        return self.current_target_level

    def get_threshold(self) -> float:
        """
        最後の N 回の反転レベルの算術平均を閾値として算出する。

        インターリーブ実行では、他条件の終了を待つ間に反転が規定回数を超えて
        蓄積される。全条件が同時刻に終了するため「最後の N 回」を採ることで
        条件間の推定の時間窓が揃う。
        """
        if not self.reversal_levels:
            return self.current_target_level

        target_revs = self.reversal_levels[-config.ADAPTIVE_NUM_REVERSALS_FOR_MEAN:]
        return float(np.mean(target_revs))

    def record_response(self, is_continuous: bool, trial_global: int) -> None:
        """
        被験者の回答に応じてロジックを進行する
        """
        self.trial_no += 1
        is_reversal = False
        
        # Step 1: レベル変更方向の決定
        if is_continuous:
            # 錯覚が起きている -> ターゲットレベルが低すぎる -> UP (+1)
            current_direction = 1
        else:
            # 途切れて聞こえた -> ターゲットレベルが高すぎる -> DOWN (-1)
            current_direction = -1

        next_target_level = self.current_target_level + (current_direction * self.current_step_size)
        
        # Step 2: 反転判定
        if self.previous_direction is not None and current_direction != self.previous_direction:
            # 反転発生
            self.reversal_count += 1
            self.reversal_levels.append(self.current_target_level)
            is_reversal = True
            
            # Step 3: ステップ幅の更新
            if self.reversal_count == config.ADAPTIVE_REVERSAL_TRIGGER_1:
                self.current_step_size = config.ADAPTIVE_SECOND_STEP_SIZE
            elif self.reversal_count == config.ADAPTIVE_REVERSAL_TRIGGER_2:
                self.current_step_size = config.ADAPTIVE_FINAL_STEP_SIZE

        # 履歴記録
        self.history.append({
            "trial_global": trial_global,
            "level_db": self.current_target_level,
            "response": "continuous" if is_continuous else "interrupted",
            "is_reversal": is_reversal,
            "reversal_count": self.reversal_count,
            "step_size": self.current_step_size
        })

        # Step 4: 終了判定とステータス更新
        self.previous_direction = current_direction

        if self.reversal_count >= config.ADAPTIVE_MAX_REVERSALS:
            self._finished = True

        # 規定反転数に達した後も、他条件の終了まで提示が続く。
        # レベルを固定すると同一刺激の反復提示になるため、更新は常に行う。
        self.current_target_level = float(np.clip(
            next_target_level,
            config.TEST_MIN_LEVEL,
            config.TEST_MAX_LEVEL
        ))


def run_1up1down_interleaved(
    win: visual.Window,
    masker_spectrum_level_db: float,
    itd_list_us: list[int],
    itd_list_sec: list[float],
    subject_id: str,
    recorder,
    sl_reference_db: float,
    test_freq: float,
    mod_freq: float,
    mod_type: str,
    masker_itd_sec: float,
    masker_itd_us: int,
) -> dict[int, tuple[float, list[float]]]:
    """
    全ITD条件のトラックをインターリーブして実行する。

    各トラックは独立に 1-up 1-down 規則で進むが、提示順は毎ラウンド
    シャッフルされ、全条件が規定反転数に達するまで全トラックを回し続ける。
    これにより tone ITD と時刻の交絡が解け、判断基準が実験中に変動しても
    全条件に共通に乗るため、条件間の差では相殺される。
    """
    tracks = {
        itd_us: AdaptiveTrack1Up1Down(masker_spectrum_level_db)
        for itd_us in itd_list_us
    }
    itd_sec_map = dict(zip(itd_list_us, itd_list_sec))

    # ── 教示画面 ──
    # 条件が被験者に分かると基準が条件依存になるため、ITD は表示しない。
    instr = visual.TextStim(
        win,
        text=(
            f"Continuous (連続) と聴こえたら   → [{config.KEY_CONTINUOUS.upper()}] キー\n"
            f"Interrupted (断続) と聴こえたら → [{config.KEY_INTERRUPTED.upper()}] キー\n\n"
            "[スペース] で開始"
        ),
        height=0.06, wrapWidth=1.5, color="white",
    )
    instr.draw()
    win.flip()
    event.waitKeys(keyList=["space"])

    prompt = visual.TextStim(win, text="", height=0.08, color="white")
    session_trial_no = 0

    while not all(t.is_finished() for t in tracks.values()):
        # 1ラウンド = 全ITDを1回ずつ、順序はシャッフル
        round_order = list(itd_list_us)
        random.shuffle(round_order)

        for itd_us in round_order:
            track = tracks[itd_us]
            session_trial_no += 1
            level = track.get_current_level()

            # ── 刺激生成・再生 ──
            stim_array = build_alternating_stimulus(
                masker_spectrum_level_db, level, itd_sec_map[itd_us],
                test_freq=test_freq, mod_freq=mod_freq, mod_type=mod_type, masker_itd_sec=masker_itd_sec
            )
            snd = sound.Sound(
                value=stim_array,
                sampleRate=config.SAMPLE_RATE,
                stereo=True,
            )

            prompt.text = "聴いてください..."
            prompt.draw()
            win.flip()

            event.clearEvents()
            snd.play()
            stim_duration = stim_array.shape[0] / config.SAMPLE_RATE
            core.wait(stim_duration)
            snd.stop()
            snd = None

            # ── 応答収集 ──
            prompt.text = f"Continuous (連続) → [{config.KEY_CONTINUOUS.upper()}]     Interrupted (断続) → [{config.KEY_INTERRUPTED.upper()}]"
            prompt.draw()
            win.flip()

            keys = event.waitKeys(
                keyList=[config.KEY_CONTINUOUS, config.KEY_INTERRUPTED, "escape"],
            )

            if keys[0] == "escape":
                win.close()
                core.quit()
            else:
                is_continuous = (keys[0] == config.KEY_CONTINUOUS)

            # ── トラック更新 ──
            track.record_response(is_continuous, track.trial_no + 1)

            # ── データ記録 ──
            last = track.history[-1]
            recorder.add_trial(
                subject_id=subject_id,
                sl_reference_db=sl_reference_db,
                test_freq=test_freq,
                mod_freq=mod_freq,
                mod_type=mod_type,
                masker_itd_us=masker_itd_us,
                itd_us=itd_us,
                track="1up1down",
                trial_no=last["trial_global"],
                session_trial_no=session_trial_no,
                level_db=last["level_db"],
                response=last["response"],
                is_reversal=last["is_reversal"],
            )

            # ── 短インターバル ──
            prompt.text = ""
            prompt.draw()
            win.flip()
            core.wait(0.3)

    return {
        itd_us: (track.get_threshold(), track.reversal_levels)
        for itd_us, track in tracks.items()
    }

if __name__ == "__main__":
    print("=== 1-up/1-down 単体シミュレーション ===")
    masker_spectrum_db = -50.0
    track = AdaptiveTrack1Up1Down(masker_spectrum_db)

    rng = random.Random(42)
    trial = 0
    while not track.is_finished():
        trial += 1
        
        # 適当なPsychometric function (例: -45 dB を閾値とする)
        # level が -45 より小さければ（テスト音が弱ければ）連続して聞こえやすい
        level = track.get_current_level()
        prob_continuous = 1.0 / (1.0 + np.exp(0.5 * (level - (-45.0))))

        is_continuous = rng.random() < prob_continuous
        track.record_response(is_continuous, trial)

        last = track.history[-1]
        marker = " <<< reversal" if last["is_reversal"] else ""
        print(
            f"Trial {trial:3d} | level={last['level_db']:7.2f} dB | step={last['step_size']:4.1f} "
            f"| resp={last['response']:11s} | rev_cnt={last['reversal_count']}{marker}"
        )

    print(f"\nシミュレーション完了")
    print(f"Reversal Levels: {[f'{v:.2f}' for v in track.reversal_levels]}")
    print(f"算出閾値: {track.get_threshold():.2f} dB FS")
