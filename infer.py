import logging
from pathlib import Path

import numpy as np
import soundfile

from infer_tools import infer_tool
# from infer_tools import merge
from infer_tools.infer_tool import Svc


def run_clip(svc_model, key, acc, use_pe, use_crepe, thre, use_gt_mel, add_noise_step, project_name='', f_name=None,
             file_path=None, out_path=None):
    infer_tool.mkdir(["./raw", "./results"])
    input_wav_path = "./infer_tools/wav_temp/input"
    # out_wav_path = "./infer_tools/wav_temp/output"
    cut_time = 30
    infer_tool.mkdir(["./infer_tools/wav_temp", input_wav_path])
    infer_tool.del_temp_wav(input_wav_path)
    if file_path is None:
        raw_audio_path = f"./raw/{f_name}"
        clean_name = f_name[:-4]
    else:
        raw_audio_path = file_path
        clean_name = str(Path(file_path).name)[:-4]
    infer_tool.format_wav(raw_audio_path)
    infer_tool.del_temp_wav("./infer_tools/wav_temp")
    infer_tool.cut_wav(Path(raw_audio_path).with_suffix('.wav'), clean_name, input_wav_path, cut_time)

    count = 0
    file_list = infer_tool.get_end_file(input_wav_path, "wav")
    f0_tst = []
    f0_pred = []
    audio = []
    for file_name in file_list:
        file_name = file_name.split("/")[-1]
        raw_path = f"{input_wav_path}/{file_name}"
        # out_path = f"{out_wav_path}/{file_name}"

        _f0_tst, _f0_pred, _audio = svc_model.infer(raw_path, key=key, acc=acc, use_pe=use_pe, use_crepe=use_crepe,
                                                    thre=thre, use_gt_mel=use_gt_mel, add_noise_step=add_noise_step)
        f0_tst.extend(_f0_tst)
        f0_pred.extend(_f0_pred)
        audio.extend(list(_audio))
        count += 1
    if out_path is None:
        out_path = f'./results/{clean_name}_{key}key_{project_name}.wav'
    soundfile.write(out_path, audio, 24000, 'PCM_16')
    # 清除缓存文件
    infer_tool.del_temp_wav(input_wav_path)
    return np.array(f0_tst), np.array(f0_pred), audio


if __name__ == '__main__':
    logging.getLogger('numba').setLevel(logging.WARNING)

    # 工程文件夹名，训练时用的那个
    project_name = "yilanqiu"
    model_path = f'./checkpoints/{project_name}/model_ckpt_steps_72000.ckpt'
    config_path = f'./checkpoints/{project_name}/config.yaml'
    # 支持多个wav文件，放在raw文件夹下
    file_names = ["青花瓷.wav"]
    trans = [0]  # 音高调整，支持正负（半音）
    # 加速倍数
    accelerate = 20
    hubert_gpu = True
    infer_tool.fill_a_to_b(trans, file_names)
    # 下面不动
    model = Svc(project_name, config_path, hubert_gpu, model_path)
    for f_name, tran in zip(file_names, trans):
        run_clip(model, key=tran, acc=accelerate, use_crepe=True, thre=0.05, use_pe=True, use_gt_mel=False,
                 add_noise_step=500, f_name=f_name, project_name=project_name)
