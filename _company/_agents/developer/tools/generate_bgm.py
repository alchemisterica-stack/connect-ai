from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write
import torch
import os

def generate_bgm(prompt: str, duration: int = 8, output_dir: str = "generated_bgm", model_name: str = "large"):
    """
    MusicGen 모델을 사용하여 텍스트 프롬프트 기반으로 BGM을 생성합니다.

    Args:
        prompt (str): 음악 생성에 사용될 텍스트 프롬프트.
        duration (int): 생성될 음악의 길이 (초).
        output_dir (str): 생성된 음악 파일이 저장될 디렉토리.
        model_name (str): 사용할 MusicGen 모델의 크기 ("small", "medium", "large").
    """
    try:
        print(f"💻 코다리: MusicGen 모델 '{model_name}' 로드 중...")
        model = MusicGen.get_pretrained(model_name)
        model.set_generation_params(duration=duration)
        print("💻 코다리: 모델 로드 완료. BGM 생성 시작...")

        # 모델을 GPU로 이동 (가능하다면)
        if torch.cuda.is_available():
            model.to("cuda")
            print("💻 코다리: 모델이 GPU에서 실행됩니다.")
        else:
            print("💻 코다리: GPU를 사용할 수 없어 CPU에서 실행됩니다. 시간이 다소 소요될 수 있습니다.")

        wav = model.generate([prompt])

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        output_path = os.path.join(output_dir, f"bgm_{prompt.replace(' ', '_').replace('.', '')}")
        
        # 생성된 오디오 저장 (sampling_rate는 모델에서 가져옴)
        for idx, one_wav in enumerate(wav):
            audio_write(
                os.path.join(output_dir, f"{output_path}_{idx}"), 
                one_wav.cpu(), 
                model.sample_rate, 
                strategy="loudness",
                loudness_compressor=True
            )
        print(f"💻 코다리: BGM 생성이 완료되었습니다. '{output_dir}' 디렉토리를 확인하세요.")
        print(f"💻 코다리: 생성된 파일: {output_path}_0.wav (외)")

    except Exception as e:
        print(f"🐛 코다리: BGM 생성 중 오류 발생: {e}")

if __name__ == "__main__":
    # '자존감 높이는 긍정 한마디' 콘텐츠에 어울리는 프롬프트 예시
    default_prompt = "uplifting, calm, positive, motivational background music, for daily affirmations, gentle piano and strings"
    
    print("💻 코다리: BGM 생성 스크립트를 시작합니다.")
    print(f"💻 코다리: 기본 프롬프트: '{default_prompt}'")
    generate_bgm(default_prompt, duration=15) # 15초 길이의 BGM 생성