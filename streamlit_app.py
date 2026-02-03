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
    
    st.info("💡 PDF를 업로드하면 '좌/우' 2단으로 나누어 분석합니다. (문제 잘림 방지)")
    st.warning("⚠️ 정확도를 위해 'Pro' 모델을 사용하므로, 속도가 느립니다 (한 페이지당 약 2분).")

# 3. 프롬프트 설정 (여러 문제가 섞여 있을 때 대응)
SYSTEM_PROMPT = """
**[역할]** 너는 수능 화학 I 만점 강사야. 
제공된 이미지는 시험지의 '한 쪽 단(Column)'이야. 여기엔 보통 1~3개의 문제가 포함되어 있어.
이미지 **위에서부터 아래로** 문제를 순서대로 식별하고, 각 문제마다 다음 4단계를 반복해.

---
**[문제 풀이 포맷]**

**문제 [번호]** (번호가 안 보이면 '첫 번째 문제' 등으로 표기)

1. **[데이터 정밀 추출]**: 표, 그래프, 분자 모형(점 개수!)을 텍스트로 묘사.
2. **[조건 분석]**: 옥텟 규칙 등을 이용해 원소(X,Y,Z) 추론.
3. **[논리적 풀이]**: 보기(ㄱ,ㄴ,ㄷ) 검증 및 계산 식 작성.
4. **[정답]**: 최종 정답 제시.

---
**주의:** 문제가 중간에 잘려서 풀 수 없다면 "문제가 잘려 있습니다"라고 하고 넘어가.
"""

def get_gemini_response(image):
    # [수정] 404 에러 방지를 위한 정식 모델명 사용
    model = genai.GenerativeModel('gemini-1.5-flash')
    
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
    st.success("파일 업로드 완료! 2단 분할 분석을 시작합니다... (Pro 모델)")
    
    # 메모리 오류 방지를 위해 150 DPI 설정
    images = convert_from_bytes(uploaded_file.read(), dpi=150)
    
    for page_num, img in enumerate(images):
        st.markdown(f"## 📄 {page_num + 1} 페이지 분석")
        
        # [핵심 수정] 4등분이 아니라 '좌/우 2등분'으로 변경
        # 시험지는 세로 단 편집이므로, 이렇게 잘라야 문제가 안 잘립니다.
        width, height = img.size
        
        # crop(left, top, right, bottom)
        crops = [
            (img.crop((0, 0, width//2, height)), "좌측 단 (1/2)"),     # 왼쪽 절반 통째로
            (img.crop((width//2, 0, width, height)), "우측 단 (2/2)")  # 오른쪽 절반 통째로
        ]
        
        cols = st.columns(2) # 2열 레이아웃
        
        for i, (cropped_img, label) in enumerate(crops):
            with cols[i]:
                st.image(cropped_img, caption=f"P{page_num+1} - {label}", use_column_width=True)
                
                with st.spinner(f"🔍 {label} 분석 중... (Pro 모델)"):
                    try:
                        result = get_gemini_response(cropped_img)
                        st.markdown(f"**🤖 분석 결과:**\n\n{result}")
                        st.divider()
                        
                        # 무료 계정 제한(RPM) 회피를 위한 30초 대기
                        time.sleep(30)
                        
                    except Exception as e:
                        st.error(f"에러 발생: {e}")

elif not api_key:
    st.warning("왼쪽 사이드바에 API Key를 먼저 입력해주세요.")

