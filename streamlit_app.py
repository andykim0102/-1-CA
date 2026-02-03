import streamlit as st
import google.generativeai as genai
from pdf2image import convert_from_bytes
import io
from PIL import Image
import time

# 1. 페이지 설정
st.set_page_config(page_title="화학I 킬러 문항 판독기", layout="wide")

# 2. 사이드바: API 키 설정
with st.sidebar:
    st.header("설정")
    api_key = st.text_input("Google API Key를 입력하세요", type="password")
    if api_key:
        genai.configure(api_key=api_key)
    
    st.info("💡 PDF를 업로드하면 자동으로 고화질 분할되어 분석됩니다.")
    st.warning("⚠️ 정확도를 위해 'Pro' 모델을 사용하므로, 속도가 느립니다 (한 페이지당 약 2분).")

# 3. 프롬프트 설정
SYSTEM_PROMPT = """
**[역할]** 너는 수능 화학 I 만점 강사야. 
제공된 이미지 조각은 고난도 모의고사 문제의 일부야.
다음 4단계 프로세스를 엄격히 지켜서 풀어줘.

1. **[데이터 정밀 추출]**: 이미지에 보이는 표, 그래프, 분자 모형(점 개수 포함)을 텍스트로 묘사해. (잘린 문제라면 보이는 부분만 해석)
2. **[조건 분석]**: 미지수(X,Y,Z)가 실제 원소(C,N,O 등)인지 옥텟 규칙에 근거해 추론해.
3. **[논리적 풀이]**: ㄱ,ㄴ,ㄷ 보기를 하나씩 검증하고 식을 세워 계산해.
4. **[검증]**: 점 개수나 수치를 잘못 보지 않았는지 자문(Self-Correction) 후 정답 제시.

**주의:** 만약 이미지가 문제의 일부만 포함하고 있어서 풀 수 없다면 "문제의 나머지 부분이 필요합니다"라고만 답해.
"""

def get_gemini_response(image):
    # 표준 Pro 모델 이름으로 변경 (404 방지)
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    # 정확도를 위해 창의성 0 설정
    generation_config = genai.types.GenerationConfig(temperature=0.0)
    
    response = model.generate_content(
        [SYSTEM_PROMPT, image],
        generation_config=generation_config
    )
    return response.text

# 4. 메인 UI
st.title("🧪 화학 I 서바이벌 모의고사 자동 분석기")

uploaded_file = st.file_uploader("PDF 시험지를 업로드하세요", type=["pdf"])

if uploaded_file is not None and api_key:
    st.success("파일 업로드 완료! 분석을 시작합니다... (시간이 좀 걸립니다)")
    
    # 메모리 오류 방지를 위해 150 DPI 설정
    images = convert_from_bytes(uploaded_file.read(), dpi=150)
    
    for page_num, img in enumerate(images):
        st.markdown(f"## 📄 {page_num + 1} 페이지 분석")
        
        # [자동 분할 로직] 
        width, height = img.size
        crops = [
            (img.crop((0, 0, width//2, height//2)), "좌측 상단 (1/4)"),
            (img.crop((width//2, 0, width, height//2)), "우측 상단 (2/4)"),
            (img.crop((0, height//2, width//2, height)), "좌측 하단 (3/4)"),
            (img.crop((width//2, height//2, width, height)), "우측 하단 (4/4)")
        ]
        
        cols = st.columns(2) # 2열 레이아웃
        
        for i, (cropped_img, label) in enumerate(crops):
            with cols[i % 2]:
                st.image(cropped_img, caption=f"P{page_num+1} - {label}", use_column_width=True)
                
                with st.spinner(f"🔍 {label} 정밀 분석 중... (Pro 모델 쿨타임 준수 중)"):
                    try:
                        result = get_gemini_response(cropped_img)
                        st.markdown(f"**🤖 분석 결과:**\n\n{result}")
                        st.divider()
                        
                        # [핵심] 무료 계정 제한(RPM) 회피를 위한 30초 대기
                        time.sleep(30)
                        
                    except Exception as e:
                        st.error(f"에러 발생: {e}")

elif not api_key:
    st.warning("왼쪽 사이드바에 API Key를 먼저 입력해주세요.")
